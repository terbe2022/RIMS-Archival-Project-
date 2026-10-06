"""Synthetic regressions; no model endpoint or real accession is accessed."""
import concurrent.futures
import ast
from functools import partial
from http.server import ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Repairs(unittest.TestCase):
    def test_all_python_sources_parse(self):
        for folder in ("scripts", "src"):
            for file in (ROOT / folder).rglob("*.py"):
                ast.parse(file.read_text(encoding="utf-8-sig"), filename=str(file))

    def test_vision_prompt_contains_valid_json_example(self):
        module = load("run_vision")
        example = module.PROMPT.split("Return: ", 1)[1]
        parsed = json.loads(example)
        self.assertIn("offense_evidence", parsed)
        self.assertIs(parsed["offensive"], False)

    def test_sync_public_dry_run_validates_without_repo_writes(self):
        module = load("sync_to_repo")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "repo" / ".git").mkdir(parents=True)
            payload = root / "payload.json"
            payload.write_text('{"jobs": [], "records": []}', encoding="utf-8")
            args = [sys.executable, "-B", str(ROOT / "scripts/sync_to_repo.py"), "--repo", str(root / "repo"),
                    "--public", "--dry-run", "--payload", str(payload)]
            # Source script is referenced relative to the selected pipeline layout.
            (root / "scripts").mkdir()
            (root / "scripts/sanitise_payload.py").write_bytes((ROOT / "scripts/sanitise_payload.py").read_bytes())
            proc = subprocess.run(args, cwd=root, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("validated in temporary storage", proc.stdout)
            self.assertEqual(list((root / "repo").iterdir()), [root / "repo" / ".git"])

    def test_script_imports_from_other_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("run_cpu_pass", "run_describe", "run_vision", "export_prototype",
                         "run_ocr", "estimate_accession", "export_workbench"):
                proc = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / (name + ".py")), "--help"],
                                      cwd=tmp, capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_manifest_association_round_trip(self):
        import pandas as pd
        import pyarrow.parquet as pq
        from workbench.schema import manifest as M
        rows = [{"file_uid": "synthetic", "accession_uid": "synthetic", "record_series": "9999999",
                 "path_raw": "sample.txt", "path_norm": "sample.txt", "retained_by_association": True}]
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "manifest.parquet"
            pq.write_table(M.enforce(pd.DataFrame(rows)), file)
            self.assertIs(pq.read_table(file).to_pylist()[0]["retained_by_association"], True)

    def test_public_review_drops_unknown_text_and_source_ids(self):
        module = load("export_review")
        payload = module.build([{"file_uid": "SENSITIVE", "accession_uid": "SENSITIVE",
                                "s02_rationale": "SENSITIVE", "s02_rule_matched": "SENSITIVE",
                                "filename": "SENSITIVE", "extension": "SENSITIVE",
                                "retained_by_association": True, "s02_decision": "selected"}],
                               {"valuable": "SENSITIVE", "name": "SENSITIVE"}, True)
        self.assertNotIn("SENSITIVE", json.dumps(payload))
        self.assertEqual(module.audit(payload), [])
        payload["items"][0]["new_secret"] = "SENSITIVE"
        self.assertTrue(module.audit(payload))

    def test_prototype_sanitizer_closed_allowlist(self):
        module = load("sanitise_payload")
        source = {"secret": "SENSITIVE", "jobs": [{"id": "SENSITIVE", "name": "SENSITIVE", "intake": {"valuable": "SENSITIVE"}}],
                  "records": [{"jobId": "SENSITIVE", "why": {"new": "SENSITIVE"}, "flags": ["SENSITIVE"], "unknown": "SENSITIVE"}]}
        payload = module.build_public(source)
        self.assertNotIn("SENSITIVE", json.dumps(payload))
        self.assertEqual(payload["jobs"][0]["files"], 1)

    def test_text_requires_redacted_directory(self):
        module = load("run_describe")
        with patch.object(sys, "argv", ["run_describe", "--manifest", "unused", "--out", "unused"]), \
             patch.object(module.pq, "read_schema") as read:
            self.assertEqual(module.main(), 2)
            read.assert_not_called()

    def test_missing_redacted_file_never_calls_model(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        module = load("run_describe")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "redacted" / "reading_room").mkdir(parents=True)
            manifest = root / "manifest.parquet"
            pq.write_table(pa.Table.from_pylist([{"file_uid": "synthetic", "accession_uid": "synthetic",
                           "s03_lane": "document", "s03_text_len": 200, "s03_text_sample": "SENSITIVE" * 30, "layer": 2}]), manifest)
            args = ["run_describe", "--manifest", str(manifest), "--out", str(root / "out.jsonl"),
                    "--redacted", str(root / "redacted")]
            with patch.object(sys, "argv", args), patch.object(module, "call_ollama") as call:
                self.assertEqual(module.main(), 1)
                call.assert_not_called()

    def test_all_lanes_preflight_before_model(self):
        module = load("run_all_lanes")
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(sys, "argv", ["lanes", "--manifest", "unused", "--out", tmp]), \
             patch.object(module, "lane_counts", return_value={"synthetic": {"text": 1, "image": 1}}), \
             patch.object(module, "run") as run:
            self.assertEqual(module.main(), 2)
            run.assert_not_called()

    def test_sync_blocks_force_and_unselected_docs(self):
        module = load("sync_to_repo")
        self.assertNotIn(("docs/*.md", "docs"), module.INCLUDE)
        with patch.object(sys, "argv", ["sync", "--force"]):
            self.assertEqual(module.main(), 2)

    def test_corrupt_log_is_not_silently_discarded(self):
        module = load("decision_server")
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log"
            log.write_text("not json\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                module.read_log(log)

    def test_concurrent_decisions_and_static_log_protection(self):
        module = load("decision_server")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.Handler.log_path = root / "decisions.log.jsonl"
            server = ThreadingHTTPServer(("127.0.0.1", 0), partial(module.Handler, directory=str(root)))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            def post(n):
                body = json.dumps({"file_uid": "synthetic", "decision": "selected", "reviewer": f"reviewer-{n}"}).encode()
                with urllib.request.urlopen(urllib.request.Request(base + "/api/decision", data=body,
                                            headers={"Content-Type": "application/json"}), timeout=10) as response:
                    return json.load(response)
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    list(pool.map(post, range(12)))
                entries = module.read_log(module.Handler.log_path)
                self.assertEqual(len({e["event_id"] for e in entries}), 12)
                self.assertIsNone(entries[0]["supersedes"])
                for prior, current in zip(entries, entries[1:]):
                    self.assertEqual(current["supersedes"], prior["event_id"])
                for path in ("/decisions.log.jsonl", "/%64ecisions.log.jsonl", "/"):
                    with self.assertRaises(urllib.error.HTTPError) as exc:
                        urllib.request.urlopen(base + path, timeout=10)
                    self.assertEqual(exc.exception.code, 403)
                with urllib.request.urlopen(base + "/api/decisions", timeout=10) as response:
                    self.assertEqual(json.load(response)["current"]["synthetic"], entries[-1])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()
