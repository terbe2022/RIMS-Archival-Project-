"""Colab synthetic runner. Offline execution needs only the Python standard library."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LIMITATIONS = ('Synthetic contract/integration smoke only; stub results are not model results. '
               'No archival quality, appraisal accuracy, sensitivity recall or throughput established.')


def preflight():
    result = {'python': platform.python_version(), 'gpu_available': False, 'gpu': None}
    try:
        import torch
        result['torch'] = torch.__version__
        result['gpu_available'] = torch.cuda.is_available()
        if result['gpu_available']:
            result['gpu'] = torch.cuda.get_device_name(0)
    except Exception as exc:
        result['gpu_probe_error'] = type(exc).__name__ + ': ' + str(exc)
    return result


def execute(args, cwd=ROOT):
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    # Never record environment variables or authentication state.
    return {'returncode': completed.returncode, 'stdout': completed.stdout,
            'stderr': completed.stderr}


def prepare_models(directory, commands):
    """Create an isolated environment; leave all kernel packages untouched."""
    print('Preparing isolated model dependencies; first setup may take several minutes.', flush=True)
    venv.EnvBuilder(with_pip=True).create(directory)
    python = directory / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    install = execute([str(python), '-m', 'pip', '--isolated', 'install', '--index-url', 'https://pypi.org/simple', '--disable-pip-version-check',
                       '-r', str(ROOT / 'validation/colab-requirements.txt')])
    commands['model_install'] = install
    if install['returncode']:
        raise RuntimeError('Isolated dependency installation failed; see diagnostic report.')
    commands['pip_check'] = execute([str(python), '-m', 'pip', 'check'])
    if commands['pip_check']['returncode']:
        raise RuntimeError('Isolated dependency check failed; model execution skipped.')
    commands['model_versions'] = execute([str(python), '-m', 'pip', 'list', '--format=json'])
    return python


def run_session(out, runtime=None, text_models=None, vision_models=None, enable_models=True):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # Refresh the report set, but do not include artifacts from previous runs in the bundle.
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'runtime': runtime if runtime is not None else preflight(),
              'limitations': LIMITATIONS, 'stages': {}, 'commands': {}}
    report['code_commit'] = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report['tracked_code_modified'] = bool(subprocess.check_output(
        ['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True).strip())
    artifacts = []
    def stage(name, python, models, lane, backend):
        print('Running ' + name + ' (' + backend + ')', flush=True)
        path = out / (name + '.json')
        # Do not mistake a previous run's artifact for a successful new run.
        if path.exists():
            path.unlink()
        command = execute([str(python), str(ROOT / 'validation/pipeline_model_compare.py'),
                           '--models', *models, '--lane', lane, '--backend', backend,
                           '--out', str(path)])
        report['commands'][name] = command
        state = {'status': 'failed'}
        if path.exists():
            result = json.loads(path.read_text(encoding='utf-8'))
            artifacts.append(path)
            rows = result['rows']
            state.update(cases=len(rows), errors=sum('error' in row for row in rows),
                         schema_valid=sum(row['metrics']['schema_valid'] for row in rows))
            if command['returncode'] == 0 and rows and state['schema_valid'] == len(rows) and not state['errors']:
                state['status'] = 'passed'
        report['stages'][name] = state
    try:
        stage('contract-smoke', sys.executable, ['stub'], 'text', 'stub')
        if report['stages']['contract-smoke']['status'] != 'passed':
            report['stages']['models'] = {'status': 'skipped', 'reason': 'offline contract failed'}
        elif not enable_models or not report['runtime']['gpu_available']:
            reason = 'models disabled' if not enable_models else 'CUDA GPU unavailable; choose Runtime > Change runtime type > GPU'
            report['stages']['models'] = {'status': 'skipped', 'reason': reason}
        else:
            python = prepare_models(out / '.model-venv', report['commands'])
            stage('text-comparison', python, text_models or ['Qwen/Qwen2.5-0.5B-Instruct'], 'text', 'hf')
            if vision_models:
                stage('vision-comparison', python, vision_models, 'vision', 'hf')
            else:
                report['stages']['vision-comparison'] = {'status': 'skipped', 'reason': 'optional vision disabled'}
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        report['stages']['session'] = {'status': 'failed', 'reason': report['error']}
    finally:
        diagnostic = out / 'diagnostics.json'
        diagnostic.write_text(json.dumps(report, indent=2), encoding='utf-8')
        summary = out / 'SUMMARY.txt'
        summary.write_text('Code commit: ' + report['code_commit'] + '\n' + LIMITATIONS + '\n\n' +
                           json.dumps(report['stages'], indent=2) + '\n' + report.get('error', ''), encoding='utf-8')
        bundle = out / 'archival-colab-report.zip'
        with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in [diagnostic, summary, *artifacts]:
                archive.write(path, path.name)
    return report, bundle
