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
import os
import threading
from uuid import uuid4
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
            try:
                with _LOCK:
                    entries = read_log(self.log_path)
            except (OSError, ValueError):
                return self._json(500, {"error": "decision history unavailable; repair required"})
            return self._json(200, {"decisions": entries,
                                    "current": state_from_entries(entries)})
        return super().do_GET()

    def send_head(self):
        # Protect an explicitly configured legacy log inside the static root,
        # including URL-encoded names and directory-listing requests.
        requested = Path(self.translate_path(self.path)).resolve()
        log = self.log_path.resolve()
        if requested == log or (requested.is_dir() and log.is_relative_to(requested)):
            self.send_error(403, "decision log is available only through the API")
            return None
        return super().send_head()

    def do_POST(self):
        if self.path.rstrip("/") != "/api/decision":
            return self._json(404, {"error": "no such endpoint"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 < n <= 65536:
                return self._json(400, {"error": "body must be 1..65536 bytes"})
            d = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": f"unparseable body: {exc}"})

        if not isinstance(d, dict):
            return self._json(400, {"error": "body must be an object"})
        missing = [k for k in ("file_uid", "decision", "reviewer")
                   if not isinstance(d.get(k), str) or not d[k].strip()]
        if missing:
            # A decision with no reviewer is not a decision. Refusing here is
            # what keeps "who decided this" answerable later.
            return self._json(400, {"error": f"missing: {', '.join(missing)}"})
        if d["decision"] not in VALID:
            return self._json(400, {
                "error": f"{d['decision']!r} is not one of {sorted(VALID)}"})

        entry = {
            "event_id": str(uuid4()),
            "file_uid": d["file_uid"],
            "accession": d.get("accession"),
            "decision": d["decision"],
            "reviewer": d["reviewer"],
            "role": d.get("role", "accessioning"),
            "reason": d.get("reason"),
            "agreed_with_pipeline": d.get("agreed_with_pipeline"),
            "supersedes": None,
            "at": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        }
        with _LOCK:
            try:
                prior = current_state(self.log_path).get(d["file_uid"])
            except (OSError, ValueError):
                return self._json(500, {"error": "decision history unavailable; no decision written"})
            if prior:
                entry["supersedes"] = prior.get("event_id") or prior.get("at")
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        return self._json(200, {"recorded": entry,
                                "changed_a_previous_decision": bool(prior)})

    def log_message(self, fmt, *a):
        if "/api/" in str(a[0] if a else ""):
            super().log_message(fmt, *a)


def read_log(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError("decision log contains a malformed entry") from exc
            if not isinstance(out[-1], dict) or not isinstance(out[-1].get("file_uid"), str):
                raise ValueError("decision log contains an invalid entry")
    return out


def current_state(path: Path) -> dict:
    """Newest entry wins. The log stays append-only."""
    return state_from_entries(read_log(path))


def state_from_entries(entries: list) -> dict:
    state: dict = {}
    for e in entries:
        state[e["file_uid"]] = e
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", default="demo/aw",
                    help="directory holding accession-workbench.html")
    ap.add_argument("--log", default=None,
                    help="decision log (default: sibling <payload-name>-state directory)")
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--bind", default="127.0.0.1")
    args = ap.parse_args()

    root = Path(args.payload).resolve()
    if not (root / "accession-workbench.html").exists():
        print(f"no accession-workbench.html in {root}")
        return 2
    legacy = root / "decisions.log.jsonl"
    if not args.log and legacy.exists():
        print("existing decision log found; specify --log to preserve that history")
        return 2
    Handler.log_path = (Path(args.log).resolve() if args.log else
                        root.parent / (root.name + "-state") / "decisions.log.jsonl")

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
