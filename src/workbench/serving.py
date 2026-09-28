"""
serving.py — one interface over vLLM and Ollama.

vLLM is the default, and that is a decision made from your own measurement
rather than from a vendor benchmark. From docs/design/pipeline-design.md, on
this L4:

    Ollama  llava-llama3 Q4_0    6.6 s/image
    Ollama  llava:7b     Q4_0    3.9 s/image
    vLLM    llava-1.5-7b FP16    1.08 s/image      <- 3.6x, purely the stack

Ollama serialises requests and holds the card at 28-31% utilisation; vLLM's
continuous batching runs it at 96-97%. Both are supported here because Ollama is
the easier thing to stand up and there is currently no throughput pressure — the
whole backlog is ~150,000 files against a 3-6 month turnaround. But when both are
available, vLLM wins.

Three guards apply whichever backend is in use, all from the Sept 2026 model
study:

  MAX_PIXELS      A 6378x4718 scan is 30 MP and hits Qwen's 12.8M ceiling at
                  16,384 vision tokens. Capping to ~1M px gives 1,280 tokens,
                  and the large default measured 26% WORSE on grounding. The cap
                  is both cheaper and better.

  num_predict     A reasoning default can spend 22,000 tokens on a trivial
                  prompt. think:false is silently ignored by some chat
                  templates; the token ceiling is enforced by the runner
                  regardless, so both are always set.

  blank pre-filter
                  Models fabricate descriptions of blank inputs at rates near
                  80%. A blank page that never reaches the model cannot
                  manufacture a false retention signal. The check is
                  deterministic and stated in the record, so an archivist can
                  argue with the threshold.
"""
from __future__ import annotations

import base64
import io
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

TIMEOUT = 600
MAX_PIXELS = 1_003_520
NUM_PREDICT_DEFAULT = 700
BLANK_CONTRAST = 8.0
BLUR_EDGE_ENERGY = 25.0


class ServingError(RuntimeError):
    pass


def _post(url: str, payload: dict, headers: Optional[dict] = None,
          timeout: int = TIMEOUT, retries: int = 3) -> dict:
    body = json.dumps(payload).encode()
    last: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt + 1)
                last = e
                continue
            raise ServingError(f"{url} -> {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt + 1)
                last = e
                continue
            raise ServingError(f"cannot reach {url}: {e}") from e
    raise ServingError(f"request failed after {retries} attempts: {last}")


# ---------------------------------------------------------------- images ----
@dataclass
class ImagePrep:
    usable: bool
    reason: str = ""
    b64: str = ""
    width: int = 0
    height: int = 0
    original_pixels: int = 0
    sent_pixels: int = 0
    contrast: float = 0.0
    edge_energy: float = 0.0

    def to_dict(self) -> dict:
        return {"usable": self.usable, "reason": self.reason,
                "sent_dimensions": f"{self.width} x {self.height}" if self.width else "",
                "original_pixels": self.original_pixels, "sent_pixels": self.sent_pixels,
                "contrast": round(self.contrast, 2),
                "edge_energy": round(self.edge_energy, 2)}


def prepare_image(path: str | Path, max_pixels: int = MAX_PIXELS) -> ImagePrep:
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return ImagePrep(usable=True, reason="Pillow/numpy absent, pre-filter skipped")
    try:
        with Image.open(path) as im:
            original_pixels = im.width * im.height
            im = im.convert("RGB")
            # measure before resizing: a downscale smooths away the noise that
            # distinguishes a blank page from a merely faint one
            a = np.asarray(im.convert("L").resize((256, 256))).astype("float32")
            contrast = float(a.std())
            lap = (a[1:-1, 2:] + a[1:-1, :-2] + a[2:, 1:-1] + a[:-2, 1:-1]
                   - 4 * a[1:-1, 1:-1])
            edge = float(lap.var())
            if contrast < BLANK_CONTRAST:
                return ImagePrep(False, f"blank or near-blank: pixel variance {contrast:.1f} "
                                        f"below threshold {BLANK_CONTRAST}",
                                 original_pixels=original_pixels,
                                 contrast=contrast, edge_energy=edge)
            if edge < BLUR_EDGE_ENERGY:
                return ImagePrep(False, f"no recoverable detail: edge energy {edge:.1f} "
                                        f"below threshold {BLUR_EDGE_ENERGY}",
                                 original_pixels=original_pixels,
                                 contrast=contrast, edge_energy=edge)
            if original_pixels > max_pixels:
                s = (max_pixels / original_pixels) ** 0.5
                im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))),
                               Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=88)
            return ImagePrep(True, b64=base64.b64encode(buf.getvalue()).decode(),
                             width=im.width, height=im.height,
                             original_pixels=original_pixels,
                             sent_pixels=im.width * im.height,
                             contrast=contrast, edge_energy=edge)
    except Exception as e:                                        # noqa: BLE001
        return ImagePrep(False, f"could not be opened as an image: {e}")


# ------------------------------------------------------------ json recovery --
def extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    try:
        import json_repair
        return json_repair.loads(text)
    except Exception:                                             # noqa: BLE001
        pass
    fixed = re.sub(r",\s*([}\]])", r"\1", text)
    fixed += "}" * max(0, fixed.count("{") - fixed.count("}"))
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        return None


# Flat on purpose. Ollama compiles a JSON schema to a GBNF grammar and its
# converter does not handle $ref, $defs, oneOf or anyOf — a nested schema fails
# at grammar compilation, which is an opaque failure rather than a loud one.
DESCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "subjects": {"type": "array", "items": {"type": "string"}},
        "genre": {"type": "string"},
        "sensitive_category": {"type": "string"},
        "sensitive_rationale": {"type": "string"},
        "appraisal_note": {"type": "string"},
        "confidence": {"type": "number"},
        "uncertain": {"type": "boolean"},
    },
    "required": ["title", "description", "confidence"],
}


# ---------------------------------------------------------------- backends --
@dataclass
class Tier:
    model: str
    label: str = "tier1"
    num_ctx: int = 16384
    num_predict: int = NUM_PREDICT_DEFAULT
    temperature: float = 0.2
    keep_alive: str = "30m"


class Backend:
    kind = "none"
    available = False

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.stats = {"calls": 0, "failures": 0, "repairs": 0, "prefiltered": 0,
                      "tier1": 0, "tier2": 0, "seconds": 0.0}
        self.max_pixels = int(cfg.get("max_pixels", MAX_PIXELS))
        self.dead_letters: list[dict] = []

    def health(self) -> dict:
        return {"ok": False, "error": "no backend"}

    def _raw(self, tier: Tier, system: str, user: str,
             image_b64: Optional[str], schema: Optional[dict]) -> str:
        raise NotImplementedError

    # -- shared call path ---------------------------------------------------
    def describe(self, system: str, user: str, *,
                 image_path: Optional[str | Path] = None,
                 tier: str = "tier1", schema: Optional[dict] = None,
                 retries: int = 3) -> tuple[Optional[dict], dict]:
        t = self.tier(tier)
        tel: dict[str, Any] = {"backend": self.kind, "tier": t.label, "model": t.model,
                               "attempts": 0, "repaired": False, "prefilter": None,
                               "seconds": 0.0}
        image_b64 = None
        if image_path is not None:
            prep = prepare_image(image_path, self.max_pixels)
            tel["prefilter"] = prep.to_dict()
            if not prep.usable:
                self.stats["prefiltered"] += 1
                return None, tel
            image_b64 = prep.b64

        started = time.time()
        for attempt in range(1, retries + 1):
            tel["attempts"] = attempt
            try:
                self.stats["calls"] += 1
                self.stats[t.label] = self.stats.get(t.label, 0) + 1
                if image_b64:
                    # Two calls by design: a grammar applied to a vision model
                    # degrades description quality, so describe freely first and
                    # convert to schema in a second, text-only, constrained call.
                    prose = self._raw(t, system, user, image_b64, None)
                    if not prose.strip():
                        continue
                    raw = self._raw(
                        t, "You convert a description into JSON. Use only what the "
                           "description states. Invent nothing. If the description says "
                           "it cannot tell, set uncertain to true.",
                        f"{user}\n\n--- description to convert ---\n{prose}",
                        None, schema or DESCRIPTION_SCHEMA)
                else:
                    raw = self._raw(t, system, user, None, schema or DESCRIPTION_SCHEMA)

                parsed = None
                if raw.strip().startswith("{"):
                    try:
                        parsed = json.loads(raw)
                    except json.JSONDecodeError:
                        parsed = None
                if parsed is None:
                    parsed = extract_json(raw)
                    if parsed is not None:
                        self.stats["repairs"] += 1
                        tel["repaired"] = True
                if parsed and str(parsed.get("title", "")).strip():
                    tel["seconds"] = round(time.time() - started, 2)
                    self.stats["seconds"] += tel["seconds"]
                    return parsed, tel
            except ServingError as e:
                tel["error"] = str(e)[:300]
                if attempt == retries:
                    break
                time.sleep(1.5 * attempt)
            except Exception as e:                                # noqa: BLE001
                tel["error"] = str(e)[:300]

        tel["seconds"] = round(time.time() - started, 2)
        self.stats["failures"] += 1
        self.dead_letters.append({"user": user[:400], "telemetry": tel})
        return None, tel

    def tier(self, which: str) -> Tier:
        raise NotImplementedError

    def report(self) -> dict:
        s = dict(self.stats)
        s["backend"] = self.kind
        n = max(1, s["calls"])
        s["repair_rate"] = round(s["repairs"] / n, 4)
        s["failure_rate"] = round(s["failures"] / n, 4)
        s["mean_seconds"] = round(s["seconds"] / n, 2)
        return s


class VLLMBackend(Backend):
    """OpenAI-compatible endpoint. The default, on measured evidence."""
    kind = "vllm"

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.base = (cfg.get("base_url") or "http://127.0.0.1:8100/v1").rstrip("/")
        self.key = cfg.get("api_key", "not-needed")
        t1 = cfg.get("tier1") or {}
        t2 = cfg.get("tier2") or {}
        self._t1 = Tier(t1.get("model", ""), "tier1",
                        num_predict=int(t1.get("num_predict", NUM_PREDICT_DEFAULT)))
        self._t2 = Tier(t2.get("model", ""), "tier2",
                        num_predict=int(t2.get("num_predict", 900)))
        self.available = bool(self._t1.model)

    def tier(self, which: str) -> Tier:
        return self._t2 if (which == "tier2" and self._t2.model) else self._t1

    def health(self) -> dict:
        try:
            with urllib.request.urlopen(f"{self.base}/models", timeout=15) as r:
                data = json.load(r)
            return {"ok": True, "models": [m["id"] for m in data.get("data", [])]}
        except Exception as e:                                    # noqa: BLE001
            return {"ok": False, "error": str(e)}

    def _raw(self, tier: Tier, system: str, user: str,
             image_b64: Optional[str], schema: Optional[dict]) -> str:
        content: Any = user
        if image_b64:
            content = [{"type": "text", "text": user},
                       {"type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]
        payload: dict[str, Any] = {
            "model": tier.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": content}],
            "temperature": tier.temperature,
            "max_tokens": tier.num_predict,
        }
        if schema:
            # vLLM's guided decoding is stricter and better than Ollama's
            payload["guided_json"] = schema
            payload["response_format"] = {"type": "json_object"}
        res = _post(f"{self.base}/chat/completions", payload,
                    headers={"Authorization": f"Bearer {self.key}"})
        return res["choices"][0]["message"]["content"] or ""


class OllamaBackend(Backend):
    """Fallback. Easier to stand up, roughly 3.6x slower on this hardware."""
    kind = "ollama"

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.base = (cfg.get("base_url") or "http://127.0.0.1:11435").rstrip("/")
        t1 = cfg.get("tier1") or {}
        t2 = cfg.get("tier2") or {}
        self._t1 = Tier(t1.get("model", ""), "tier1",
                        num_ctx=int(t1.get("num_ctx", 16384)),
                        num_predict=int(t1.get("num_predict", NUM_PREDICT_DEFAULT)),
                        keep_alive=t1.get("keep_alive", "30m"))
        self._t2 = Tier(t2.get("model", ""), "tier2",
                        num_ctx=int(t2.get("num_ctx", 16384)),
                        num_predict=int(t2.get("num_predict", 900)),
                        # unloaded after each escalation window; 24 GB will not
                        # hold a 9B and a 27B at once
                        keep_alive=t2.get("keep_alive", "0"))
        self.available = bool(self._t1.model)

    def tier(self, which: str) -> Tier:
        return self._t2 if (which == "tier2" and self._t2.model) else self._t1

    def health(self) -> dict:
        try:
            with urllib.request.urlopen(f"{self.base}/api/tags", timeout=15) as r:
                data = json.load(r)
            return {"ok": True, "models": [m["name"] for m in data.get("models", [])]}
        except Exception as e:                                    # noqa: BLE001
            return {"ok": False, "error": str(e)}

    def _raw(self, tier: Tier, system: str, user: str,
             image_b64: Optional[str], schema: Optional[dict]) -> str:
        payload: dict[str, Any] = {
            "model": tier.model, "prompt": user, "system": system, "stream": False,
            "keep_alive": tier.keep_alive,
            "think": False,
            "options": {"temperature": tier.temperature,
                        # never leave num_ctx automatic: Ollama picks from a VRAM
                        # tier and an L4 reports just under the 23 GiB threshold,
                        # which silently yields 4096 — too small for one image
                        "num_ctx": tier.num_ctx,
                        "num_predict": tier.num_predict},
        }
        if image_b64:
            payload["images"] = [image_b64]
        if schema:
            payload["format"] = schema
        return _post(f"{self.base}/api/generate", payload).get("response", "")

    def vision_canary(self, image_path: str | Path, expect: str) -> dict:
        """
        `ollama create` succeeding proves nothing about vision: a projector can
        be attached and ignored, attached and crash the runner, or misdetected
        entirely, and all three import cleanly. Show the model a string it
        cannot guess and see whether it comes back.
        """
        prep = prepare_image(image_path, self.max_pixels)
        if not prep.usable:
            return {"ok": False, "error": f"canary rejected by pre-filter: {prep.reason}"}
        try:
            out = self._raw(self._t1, "You read text in images. Reply with only that text.",
                            "What text appears in this image?", prep.b64, None)
        except ServingError as e:
            return {"ok": False, "error": str(e)}
        ok = expect.lower() in (out or "").lower()
        return {"ok": ok, "expected": expect, "got": (out or "")[:200],
                "verdict": "vision works" if ok else
                           "MODEL CANNOT SEE THE IMAGE — projector missing or ignored"}


class NoBackend(Backend):
    kind = "none"
    available = False

    def tier(self, which: str) -> Tier:
        return Tier("none", which)

    def describe(self, *a, **k):
        return None, {"backend": "none", "tier": "none", "attempts": 0, "seconds": 0.0}


def build_backend(cfg: dict) -> Backend:
    """
    Prefer vLLM, fall back to Ollama, fall back to deterministic. Each step
    reports why, because a silent downgrade to the no-model path would look like
    a working run that described nothing.
    """
    mcfg = dict(cfg.get("model", {}))
    order = mcfg.get("prefer", ["vllm", "ollama"])
    for kind in order:
        sub = dict(mcfg.get(kind) or {})
        if not sub:
            continue
        sub.setdefault("max_pixels", mcfg.get("max_pixels", MAX_PIXELS))
        backend = VLLMBackend(sub) if kind == "vllm" else OllamaBackend(sub)
        if not backend.available:
            print(f"  · {kind}: no tier1 model configured, skipping")
            continue
        h = backend.health()
        if not h["ok"]:
            print(f"  · {kind}: unreachable at {backend.base} ({h['error']}), skipping")
            continue
        missing = [t.model for t in (backend.tier("tier1"), backend.tier("tier2"))
                   if t.model and t.model not in h["models"]]
        if backend.tier("tier1").model in missing:
            print(f"  · {kind}: tier1 model '{backend.tier('tier1').model}' not loaded. "
                  f"Available: {', '.join(h['models']) or '(none)'}")
            continue
        print(f"  ✓ {kind} at {backend.base}, tier1={backend.tier('tier1').model}"
              + (f", tier2={backend.tier('tier2').model}" if backend.tier('tier2').model
                 and backend.tier('tier2').model not in missing else ", no tier2"))
        return backend
    print("  ! no serving backend available — running deterministic only. "
          "Descriptions will come from metadata and extracted text, not from a model.")
    return NoBackend(mcfg)
