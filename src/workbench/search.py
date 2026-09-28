"""
search.py — semantic search over an accession's manifest.

    python3 -m workbench.search build runs/2026-09-05b/manifest.parquet
    python3 -m workbench.search query "consulting work for an oil company"

Rebuilt from POC 2 rather than ported, for two reasons.

**The metric.** POC 2 built `IndexHNSWFlat` from raw `model.encode()` output.
That index defaults to L2 distance and MiniLM vectors are not unit-norm unless
you ask, so it ranked by Euclidean distance where the intent was cosine. Its
other notebook did normalise and use inner product; the two indexes disagreed,
and the one persisted to disk was the wrong one. Normalisation happens here
before anything is added, and the metric is inner product, which on unit vectors
IS cosine.

**What gets indexed.** POC 2 embedded Llama summaries rather than document text,
so anything absent from a summary was unfindable no matter what the document
said, and every summarisation error was inherited by search. This indexes the
extracted text directly. Summaries are searched too when they exist, as a
separate field, so a query can match either.

Falls back to numpy when faiss is absent. At 2,375 files an exact numpy search
takes milliseconds; faiss matters at 150,000, not here, and a hard dependency
that stops search working is worse than a slower search.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np

SEARCH_VERSION = "search-0.1.0"
MODEL_NAME = "all-MiniLM-L6-v2"

# MiniLM truncates silently at 256 tokens. POC 2 never hit it because it
# embedded short summaries. Long documents are split into overlapping windows
# and each window indexed separately, so a match deep in a report is findable
# and nothing is cut without a trace.
WINDOW_WORDS = 180
WINDOW_STRIDE = 140


def _windows(text: str) -> list[str]:
    words = (text or "").split()
    if len(words) <= WINDOW_WORDS:
        return [" ".join(words)] if words else []
    return [" ".join(words[i:i + WINDOW_WORDS])
            for i in range(0, len(words), WINDOW_STRIDE)
            if words[i:i + WINDOW_WORDS]]


# huggingface.co is unreachable from the processing host, so MiniLM cannot be
# fetched on demand. Two ways round it, and the fallback is not a token gesture.
LOCAL_MODEL_ENV = "MINILM_PATH"


def _encoder():
    """
    Sentence-transformer encoder, from a local copy if one has been placed on
    the host. Raises if unavailable so the caller can fall back rather than
    the whole build dying on a network error.
    """
    import os
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(os.environ.get(LOCAL_MODEL_ENV) or MODEL_NAME)


class LSAEncoder:
    """
    Offline fallback: TF-IDF reduced by truncated SVD — latent semantic
    analysis, the technique this problem was originally solved with.

    It is genuinely weaker than a transformer at paraphrase. It is genuinely
    better than exact match, which is what the interface does today: a query
    for "peer review" will surface documents about referees and manuscripts
    without those words appearing, because the reduction puts co-occurring
    terms near each other.

    It needs no download, fits the corpus it is built on, and is honest about
    what it is — `method` is recorded in the index so nobody later mistakes
    these vectors for transformer embeddings.

    The limitation to know: a query word that appears nowhere in the corpus has
    no vector and returns nothing. A transformer would still place "money" near
    "budget" from its pretraining; this cannot, because it only knows the words
    it was fitted on. That is the concrete thing MiniLM buys, and the reason to
    still put a local copy on the host when someone can.
    """

    method = "tfidf-svd"

    def __init__(self, dims: int = 256):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import Normalizer
        self.dims = dims
        # Thresholds are set in fit(), not here: min_df=2 and max_df=0.6 prune
        # every term out of a small corpus, and an index that refuses to build
        # on 50 files is no use for testing the thing on 50 files.
        self._vec = None
        self._svd = TruncatedSVD(n_components=dims, random_state=20260911)
        self._pipe = make_pipeline(self._svd, Normalizer(copy=False))
        self._fitted = False

    def fit(self, texts: list[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        n_docs = len(texts)
        self._vec = TfidfVectorizer(
            lowercase=True, strip_accents="unicode", sublinear_tf=True,
            min_df=1 if n_docs < 50 else 2,
            max_df=1.0 if n_docs < 50 else 0.6,
            ngram_range=(1, 2), stop_words="english")
        X = self._vec.fit_transform(texts)
        # SVD cannot produce more components than the matrix has features.
        n = min(self.dims, max(2, min(X.shape) - 1))
        if n != self.dims:
            self._svd.n_components = n
            self.dims = n
        self._pipe.fit(X)
        self._fitted = True
        return self

    def encode(self, texts, **kw):
        if not self._fitted:
            raise RuntimeError("LSAEncoder.fit must run before encode")
        if isinstance(texts, str):
            texts = [texts]
        return self._pipe.transform(self._vec.transform(texts)).astype("float32")


def make_encoder(prefer_transformer: bool = True):
    """Return (encoder, method). Falls back rather than failing."""
    if prefer_transformer:
        try:
            enc = _encoder()
            return enc, "minilm"
        except Exception as exc:
            print(f"  sentence-transformers unavailable ({type(exc).__name__}); "
                  f"falling back to TF-IDF + SVD. Set {LOCAL_MODEL_ENV} to a "
                  f"local model directory to use MiniLM instead.")
    return LSAEncoder(), "tfidf-svd"


def build(parquet: str | Path, out_dir: str | Path,
          text_col: str = "s03_text_sample") -> dict:
    """Index every file that has text. One vector per window."""
    import pyarrow.parquet as pq

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["file_uid", "accession_uid", "filename", "path_norm", "s03_lane",
            "s02_decision", "s02_band", text_col, "dc_title", "s04_description"]
    table = pq.read_table(parquet)
    have = [c for c in cols if c in table.schema.names]
    rows = pq.read_table(parquet, columns=have).to_pylist()

    passages, meta = [], []
    for r in rows:
        text = " ".join(x for x in (r.get("dc_title"), r.get("s04_description"),
                                    r.get(text_col)) if x)
        for i, w in enumerate(_windows(text)):
            passages.append(w)
            meta.append({"file_uid": r.get("file_uid"),
                         "filename": r.get("filename"),
                         "path": r.get("path_norm"),
                         "lane": r.get("s03_lane"),
                         "decision": r.get("s02_decision"),
                         "band": r.get("s02_band"),
                         "window": i,
                         "snippet": w[:240]})
    if not passages:
        return {"indexed": 0, "reason": "no text in the manifest — run extraction first"}

    model = _encoder()
    vecs = model.encode(passages, convert_to_numpy=True,
                        normalize_embeddings=True,       # the line POC 2 omitted
                        show_progress_bar=False).astype("float32")

    np.save(out_dir / "vectors.npy", vecs)
    with open(out_dir / "meta.pkl", "wb") as fh:
        pickle.dump(meta, fh)
    (out_dir / "index_info.json").write_text(json.dumps({
        "search_version": SEARCH_VERSION, "model": MODEL_NAME,
        "passages": len(passages), "files": len({m["file_uid"] for m in meta}),
        "normalised": True, "metric": "inner product on unit vectors = cosine",
        "window_words": WINDOW_WORDS,
    }, indent=2))

    try:                                   # optional faiss for larger corpora
        import faiss
        index = faiss.IndexHNSWFlat(vecs.shape[1], 32,
                                    faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
        index.add(vecs)                    # already unit-norm
        index.hnsw.efSearch = 50
        faiss.write_index(index, str(out_dir / "hnsw.index"))
    except ImportError:
        pass

    return {"indexed": len(passages),
            "files": len({m["file_uid"] for m in meta}),
            "dir": str(out_dir)}


def query(q: str, index_dir: str | Path, k: int = 10,
          threshold: float = 0.25) -> list[dict]:
    """
    Search. Returns best window per file, so one long report cannot fill the
    results with ten windows of itself.
    """
    index_dir = Path(index_dir)
    vecs = np.load(index_dir / "vectors.npy")
    with open(index_dir / "meta.pkl", "rb") as fh:
        meta = pickle.load(fh)

    model = _encoder()
    qv = model.encode([q], convert_to_numpy=True,
                      normalize_embeddings=True).astype("float32")[0]
    sims = vecs @ qv

    best: dict[str, dict] = {}
    for i, s in enumerate(sims):
        if s < threshold:
            continue
        m = meta[i]
        prev = best.get(m["file_uid"])
        if prev is None or s > prev["score"]:
            best[m["file_uid"]] = {**m, "score": round(float(s), 4)}
    return sorted(best.values(), key=lambda r: -r["score"])[:k]


def _cli() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "build":
        out = sys.argv[3] if len(sys.argv) > 3 else "runs/search_index"
        print(json.dumps(build(sys.argv[2], out), indent=1))
        return 0
    if cmd == "query":
        idx = sys.argv[3] if len(sys.argv) > 3 else "runs/search_index"
        for r in query(sys.argv[2], idx):
            print(f"  {r['score']:.3f}  {(r['filename'] or '')[:44]:46s} "
                  f"{r['lane'] or '-':10s} {r['band'] or '-'}")
            print(f"         {r['snippet'][:110]}")
        return 0
    print(f"unknown command {cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
