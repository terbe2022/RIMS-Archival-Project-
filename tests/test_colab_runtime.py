import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validation import colab_runtime as runtime


class ColabRuntimeTests(unittest.TestCase):
    def test_cpu_session_installs_nothing_and_bundles_contract(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runtime, 'prepare_models') as install:
            report, bundle = runtime.run_session(tmp, runtime={'gpu_available': False})
            install.assert_not_called()
            self.assertEqual(report['stages']['contract-smoke']['status'], 'passed')
            self.assertEqual(report['stages']['models']['status'], 'skipped')
            with zipfile.ZipFile(bundle) as archive:
                self.assertEqual(set(archive.namelist()), {'diagnostics.json', 'SUMMARY.txt', 'contract-smoke.json'})
                self.assertEqual(len(json.loads(archive.read('contract-smoke.json'))['rows']), 3)

    def test_setup_failure_preserves_report_and_offline_results(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runtime, 'prepare_models', side_effect=RuntimeError('simulated install failure')):
            report, bundle = runtime.run_session(tmp, runtime={'gpu_available': True})
            self.assertIn('simulated install failure', report['error'])
            self.assertTrue(bundle.exists())
            self.assertEqual(report['stages']['contract-smoke']['status'], 'passed')

    def test_failed_model_cannot_reuse_stale_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            stale = Path(tmp) / 'text-comparison.json'
            stale.write_text('{"rows": []}')
            real_execute = runtime.execute
            def fake_execute(args, **kwargs):
                if 'hf' in args:
                    return {'returncode': 1, 'stdout': '', 'stderr': 'simulated model load failure'}
                return real_execute(args, **kwargs)
            with patch.object(runtime, 'prepare_models', return_value=Path(sys.executable)), patch.object(runtime, 'execute', side_effect=fake_execute):
                report, bundle = runtime.run_session(tmp, runtime={'gpu_available': True})
            self.assertEqual(report['stages']['text-comparison']['status'], 'failed')
            with zipfile.ZipFile(bundle) as archive:
                self.assertNotIn('text-comparison.json', archive.namelist())

    def test_schema_failure_is_not_success_even_with_zero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake_execute(args, **kwargs):
                path = Path(args[args.index('--out') + 1])
                path.write_text(json.dumps({'rows': [{'metrics': {'schema_valid': False}}]}))
                return {'returncode': 0, 'stdout': '', 'stderr': ''}
            with patch.object(runtime, 'execute', side_effect=fake_execute), patch.object(runtime, 'prepare_models') as install:
                report, bundle = runtime.run_session(tmp, runtime={'gpu_available': True})
            install.assert_not_called()
            self.assertEqual(report['stages']['contract-smoke']['status'], 'failed')
            self.assertEqual(report['stages']['models']['status'], 'skipped')

    def test_models_disabled_skips_install_even_on_gpu(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runtime, 'prepare_models') as install:
            report, _ = runtime.run_session(tmp, runtime={'gpu_available': True}, enable_models=False)
            install.assert_not_called()
            self.assertEqual(report['stages']['models']['reason'], 'models disabled')

    def test_stub_runs_without_any_site_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, '-S', str(ROOT / 'validation/pipeline_model_compare.py'),
                                     '--models', 'stub', '--backend', 'stub', '--out', str(Path(tmp) / 'smoke.json')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_notebook_python_compiles_and_has_no_saved_outputs(self):
        notebook = json.loads((ROOT / 'notebooks/shared-pipeline-colab.ipynb').read_text(encoding='utf-8'))
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                compile(''.join(cell['source']), '<notebook>', 'exec')
                self.assertEqual(cell['outputs'], [])
                self.assertIsNone(cell['execution_count'])


if __name__ == '__main__':
    unittest.main()
