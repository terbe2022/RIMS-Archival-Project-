#!/usr/bin/env python3
"""Code-only deployment. Default is a dry run; no data sync or model startup."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    return [Path(p) for p in tracked if p and
        ((p.startswith(('src/', 'scripts/', 'tests/')) and p.endswith('.py'))
         or p in ['requirements.txt', 'web/accession-workbench.html', 'validation/pipeline_model_compare.py'])]


def safe_target(live, rel):
    path = live / rel
    if path.is_symlink() or not path.resolve().is_relative_to(live):
        raise ValueError('Symlink or out-of-directory deployment target: ' + str(rel))
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--rollback', type=Path, help='journal.json from a previous deployment backup')
    args = parser.parse_args()
    live = args.live.resolve()
    if not live.is_dir() or live == ROOT or (live / '.git').exists():
        parser.error('Use the existing non-Git live directory, separate from this fresh clone.')
    if args.rollback:
        journal = args.rollback.resolve()
        if not journal.is_relative_to(live / '_code_backups'):
            parser.error('Rollback journal must belong to this live directory.')
        data = json.loads(journal.read_text())
        for row in data['changed']:
            target = safe_target(live, Path(row['path']))
            if not target.is_file() or sha(target) != row['new_sha256']:
                parser.error('Code changed after deployment; refusing rollback: ' + row['path'])
        for row in data['changed']:
            target = safe_target(live, Path(row['path']))
            if row['old_exists']:
                shutil.copy2(journal.parent / 'original' / row['path'], target)
            else:
                target.unlink()
        receipt = live / 'state/deployed-code.json'
        previous = journal.parent / 'previous-receipt.json'
        if previous.exists():
            shutil.copy2(previous, receipt)
        elif receipt.exists():
            receipt.unlink()
        print('Rolled back code using', journal)
        return 0
    dirty = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT).strip()
    if dirty and args.apply:
        parser.error('Commit/review tracked changes before deployment.')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = sources()
    changes = []
    for rel in files:
        source, target = ROOT / rel, safe_target(live, rel)
        if rel.suffix == '.py':
            ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(rel))
        if not target.is_file() or sha(source) != sha(target):
            changes.append({'path': rel.as_posix(), 'old_exists': target.is_file(),
                            'new_sha256': sha(source)})
    print(json.dumps({'commit': commit, 'files': len(files), 'changes': len(changes)}, indent=2))
    for row in changes:
        print('UPDATE' if row['old_exists'] else 'ADD', row['path'])
    if args.verify:
        return 1 if changes else 0
    if not args.apply:
        print('Dry run only. Data, forms, decisions, models, old workbench/ and exports are untouched.')
        return 0
    backup = live / '_code_backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + commit[:10])
    backup.mkdir(parents=True)
    receipt = live / 'state/deployed-code.json'
    if receipt.exists():
        shutil.copy2(receipt, backup / 'previous-receipt.json')
    for row in changes:
        if row['old_exists']:
            dest = backup / 'original' / row['path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_target(live, Path(row['path'])), dest)
    (backup / 'journal.json').write_text(json.dumps({'commit': commit, 'changed': changes}, indent=2))
    applied = []
    try:
        for row in changes:
            target = safe_target(live, Path(row['path']))
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as tmp:
                temp = Path(tmp.name)
            try:
                shutil.copy2(ROOT / row['path'], temp)
                temp.replace(target)
            finally:
                temp.unlink(missing_ok=True)
            applied.append(row)
        assert all(sha(ROOT / rel) == sha(live / rel) for rel in files)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({'commit': commit, 'backup': str(backup),
            'files': {p.as_posix(): sha(ROOT / p) for p in files}}, indent=2))
    except Exception:
        for row in reversed(applied):
            target = safe_target(live, Path(row['path']))
            if row['old_exists']:
                shutil.copy2(backup / 'original' / row['path'], target)
            else:
                target.unlink(missing_ok=True)
        raise
    print('Verified deployed code. Rollback journal:', backup / 'journal.json')
    print('Scripts now prioritize src/workbench; the old workbench/ is preserved as legacy code.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
