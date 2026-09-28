#!/usr/bin/env python3
"""
decision_server.py — make decisions survive the tab closing.

    python3 scripts/decision_server.py --payload demo/aw --port 8899

Serves the workbench exactly as `python -m http.server` does, and adds two
endpoints so the interface can write decisions somewhere that persists:

    POST /api/decision    one decision, appended to the log
    GET  /api/decisions   every decision recorded so far

Why a log and not a database
----------------------------
Decisions are appended, never updated in place. A reviewer who changes their
mind produces a second entry, and both are kept: "selected at 14:02, changed to
restricted_review at 14:19" is the record an archives needs, and overwriting the
first would destroy exactly the thing the decision log exists to hold.

The current state of a file is the newest entry for it. That is computed on
read, so the log stays append-only and no recovery step is needed after a crash.

Why this is not the production answer
-------------------------------------
Single process, single file, no authentication, no concurrent-write locking
beyond a mutex within one process. It is the smallest thing that makes the
prototype usable by a person over more than one sitting. Production needs a real
store and an identity — but the shape of what is written should not change, and
that shape is the point of writing this now rather than later.
"""
from __future__ import annotations

import argparse
import json
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VALID = {"selected", "not_selected", "restricted_review", "discard_candidate"}
_LOCK = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    log_path: Path = Path("decisions.log.jsonl")

    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") == "/api/decisions":
            return self._json(200, {"decisions": read_log(self.log_path),
                                    "current": current_state(self.log_path)})
        return super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") != "/api/decision":
            return self._json(404, {"error": "no such endpoint"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": f"unparseable body: {exc}"})

        missing = [k for k in ("file_uid", "decision", "reviewer") if not d.get(k)]
        if missing:
            # A decision with no reviewer is not a decision. Refusing here is
            # what keeps "who decided this" answerable later.
            return self._json(400, {"error": f"missing: {', '.join(missing)}"})
        if d["decision"] not in VALID:
            return self._json(400, {
                "error": f"{d['decision']!r} is not one of {sorted(VALID)}"})

        entry = {
            "file_uid": d["file_uid"],
            "accession": d.get("accession"),
            "decision": d["decision"],
            "reviewer": d["reviewer"],
            "role": d.get("role", "accessioning"),
            "reason": d.get("reason"),
            "agreed_with_pipeline": d.get("agreed_with_pipeline"),
            "supersedes": None,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        prior = current_state(self.log_path).get(d["file_uid"])
        if prior:
            entry["supersedes"] = prior.get("at")

        with _LOCK:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        return self._json(200, {"recorded": entry,
                                "changed_a_previous_decision": bool(prior)})

    def log_message(self, fmt, *a):
        if "/api/" in (a[0] if a else ""):
            super().log_message(fmt, *a)


def read_log(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def current_state(path: Path) -> dict:
    """Newest entry wins. The log stays append-only."""
    state: dict = {}
    for e in read_log(path):
        state[e["file_uid"]] = e
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", default="demo/aw",
                    help="directory holding accession-workbench.html")
    ap.add_argument("--log", default=None,
                    help="decision log (default: <payload>/decisions.log.jsonl)")
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--bind", default="127.0.0.1")
    args = ap.parse_args()

    root = Path(args.payload).resolve()
    if not (root / "accession-workbench.html").exists():
        print(f"no accession-workbench.html in {root}")
        return 2
    Handler.log_path = Path(args.log) if args.log else root / "decisions.log.jsonl"

    existing = current_state(Handler.log_path)
    print(f"serving {root} on http://{args.bind}:{args.port}")
    print(f"  decision log: {Handler.log_path}")
    print(f"  {len(read_log(Handler.log_path))} entries, "
          f"{len(existing)} files with a current decision")
    print(f"  open http://{args.bind}:{args.port}/accession-workbench.html")

    srv = ThreadingHTTPServer(
        (args.bind, args.port), partial(Handler, directory=str(root)))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped. Decisions are in " + str(Handler.log_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
