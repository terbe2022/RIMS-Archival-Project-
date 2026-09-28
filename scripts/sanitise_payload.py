#!/usr/bin/env python3
"""
sanitise_payload.py — make a prototype payload safe to publish.

    python3 scripts/sanitise_payload.py demo/aw/prototype-data.json \\
        --out public/prototype-data.json

The demonstration payload carries real filenames, real folder paths and real
extracted text from unreviewed archival material — referee reports naming living
people, private correspondence, a credential file, a possible social security
number. None of that can go on a public web host.

This keeps the shape and every number — counts, bands, decisions, rules matched,
folder shares, run times — and removes the content. What a visitor sees is a
working interface over a real run, with nothing in it that identifies anybody.

It refuses to write if anything identifying survives, rather than trusting that
the column list was complete.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Anything that could name a person, a place, or the content of a file.
DROP = ("filename", "boxPath", "folder", "body", "snippet", "versions",
        "description", "title", "keywords", "reviewReason", "reviewCriterion",
        "thumb", "view", "proximity", "format", "date", "boxFileId")

# Kept, because they are the demonstration: what the pipeline decided and why.
KEEP_RATIONALE = True

LEAK = re.compile(
    r"\b[A-Z][a-z]+,[A-Z][a-z]+"          # Surname,Forename in filenames
    r"|@[\w.-]+\.\w+"                      # email addresses
    r"|\b\d{3}[- ]\d{2}[- ]\d{4}\b"        # SSN shape
    r"|\b\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b"  # phone
    r"|hanratty|hart@|pglaf|conoco", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("payload")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = json.loads(Path(args.payload).read_text())

    for n, r in enumerate(d.get("records", []), 1):
        kind = r.get("kind") or "file"
        ext = {"image": "jpg", "email": "eml", "document": "pdf",
               "tabular": "xlsx"}.get(kind, "dat")
        for k in DROP:
            r.pop(k, None)
        r["filename"] = f"item-{n:05d}.{ext}"
        r["title"] = f"{kind.title()} record {n:05d}"
        r["folder"] = f"folder-{(n % 40) + 1:02d}"
        r["description"] = (
            "Content withheld in the public build. The decision, the rule "
            "matched and the ranking are real; the text is not shown.")
        # The rationale quotes the archivist's own appraisal criteria, which
        # are professional judgements about a collection, not personal data —
        # and they are the whole point of the demonstration.
        if r.get("rationale"):
            rat = r["rationale"]
            for name in ("Hanratty", "Conoco", "Hart", "Gutenberg", "pglaf",
                         "Eudora", "Illinois Workshop", "Ethiopian", "Begemdir",
                         "Tegray", "Wallo", "AIChE"):
                rat = re.sub(re.escape(name), "[REDACTED]", rat, flags=re.I)
            r["rationale"] = rat
        r["flags"] = [str(f) for f in (r.get("flags") or [])]

    for j in d.get("jobs", []):
        form = j.get("intake") or {}
        # Appraisal criteria stay; provenance naming living people does not.
        # The criteria are professional judgements, but they name the creator
        # and the client — "the Conoco folder", "Hanratty's own work". Keeping
        # the sentence and removing the name keeps what the demonstration needs
        # and drops what it must not publish.
        def _scrub(t: str) -> str:
            for name in ("Hanratty", "Conoco", "Hart", "Gutenberg", "Michael S. Hart",
                         "pglaf", "Eudora", "Illinois Workshop", "Ethiopian",
                         "Begemdir", "Tegray", "Wallo", "AIChE"):
                t = re.sub(re.escape(name), "[REDACTED]", t, flags=re.I)
            return t

        j["intake"] = {k: _scrub(form.get(k)) for k in
                       ("valuable", "exclude", "access") if form.get(k)}
        j["intake"]["source"] = ("Withheld in the public build. The appraisal "
                                 "criteria above are the real ones and are what "
                                 "every ranking was scored against.")
        for f in j.get("folders") or []:
            f["folder"] = "folder-" + str(abs(hash(f.get("folder", ""))) % 97)
        j["name"] = {"ACC-2026-020": "Scanning programme output (sample)",
                     "ACC-2026-021": "Faculty office computer (sample)",
                     "ACC-2026-022": "Mixed correspondence folder (sample)",
                     "ACC-2026-023": "Departmental transfer (queued)"
                     }.get(j.get("id"), j.get("name"))

    d["public"] = True
    d["notice"] = ("Public demonstration build. Every count, decision, rule "
                   "and ranking comes from a real run over 2,375 files. All "
                   "filenames, paths and content have been removed.")

    text = json.dumps(d, default=str)
    hits = LEAK.findall(text)
    if hits:
        print(f"REFUSING TO WRITE — {len(hits)} identifying string(s) survived, "
              f"e.g. {sorted(set(hits))[:5]}", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"wrote {out}  {out.stat().st_size/1024:.0f} KB")
    print(f"  {len(d.get('records', []))} records, content removed, "
          f"decisions and rankings intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
