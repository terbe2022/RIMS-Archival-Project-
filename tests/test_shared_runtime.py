import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from validation.pipeline_model_compare import assess, run

spec = importlib.util.spec_from_file_location('deploy', ROOT / 'scripts/deploy_code.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class SharedRuntime(unittest.TestCase):
    def test_stub_is_explicit_and_contract_valid(self):
        report = run(['stub'], backend='stub')
        self.assertEqual(len(report['rows']), 3)
        self.assertTrue(all(r['metrics']['schema_valid'] for r in report['rows']))
        self.assertEqual({r['backend'] for r in report['rows']}, {'stub'})

    def test_vision_stub_uses_generated_images(self):
        report = run(['stub'], lane='vision', backend='stub')
        self.assertEqual(len(report['rows']), 2)
        self.assertTrue(all(r['metrics']['schema_valid'] for r in report['rows']))

    def test_malformed_output_not_counted_as_success(self):
        self.assertFalse(assess('not JSON', 'text', {})['schema_valid'])
        self.assertFalse(assess('{"readable":"false"}', 'text', {})['schema_valid'])

    def test_server_backend_requires_explicit_endpoint(self):
        with self.assertRaises(ValueError):
            run(['model'], backend='ollama')

    def test_deploy_preserves_data_and_rollback_restores_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, live = Path(tmp) / 'repo', Path(tmp) / 'live'
            (repo / 'scripts').mkdir(parents=True)
            (live / 'scripts').mkdir(parents=True)
            (live / 'data').mkdir()
            (repo / 'scripts/a.py').write_text('value = 2\n')
            (repo / 'scripts/new.py').write_text('value = 3\n')
            (live / 'scripts/a.py').write_text('value = 1\n')
            (live / 'data/original.txt').write_text('retain this original')
            def git_output(args, **kwargs):
                if 'ls-files' in args:
                    return b'scripts/a.py\0scripts/new.py\0'
                if 'status' in args:
                    return b''
                return 'a' * 40 + '\n'
            with patch.object(deploy, 'ROOT', repo), patch.object(deploy.subprocess, 'check_output', side_effect=git_output):
                with patch.object(sys, 'argv', ['deploy', '--live', str(live)]):
                    self.assertEqual(deploy.main(), 0)
                self.assertEqual((live / 'scripts/a.py').read_text(), 'value = 1\n')
                self.assertFalse((live / '_code_backups').exists())
                with patch.object(sys, 'argv', ['deploy', '--live', str(live), '--apply']):
                    self.assertEqual(deploy.main(), 0)
                self.assertEqual((live / 'scripts/a.py').read_text(), 'value = 2\n')
                receipt = json.loads((live / 'state/deployed-code.json').read_text())
                journal = Path(receipt['backup']) / 'journal.json'
                with patch.object(sys, 'argv', ['deploy', '--live', str(live), '--verify']):
                    self.assertEqual(deploy.main(), 0)
                with patch.object(sys, 'argv', ['deploy', '--live', str(live), '--rollback', str(journal)]):
                    self.assertEqual(deploy.main(), 0)
                self.assertEqual((live / 'scripts/a.py').read_text(), 'value = 1\n')
                self.assertFalse((live / 'scripts/new.py').exists())
                self.assertEqual((live / 'data/original.txt').read_text(), 'retain this original')


if __name__ == '__main__':
    unittest.main()
