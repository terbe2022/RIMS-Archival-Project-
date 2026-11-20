"""Verify the imported synthetic fixtures without executing or unpacking them."""
import hashlib
import json
import os
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    if os.name == 'nt':
        root = Path('\\\\?\\' + str(root))
    manifest = json.loads((root / 'PROVENANCE.json').read_text(encoding='utf-8'))
    failures = []
    for entry in manifest['files']:
        path = root.joinpath(*entry['path'].split('/'))
        try:
            data = path.read_bytes()
        except OSError as exc:
            failures.append(f"{entry['path']}: {exc}")
            continue
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if (len(data) != entry['bytes'] or blob != entry['git_blob_sha']
                or hashlib.sha256(data).hexdigest() != entry['sha256']):
            failures.append(f"{entry['path']}: byte/hash mismatch")
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f"Verified {len(manifest['files'])} source files from {manifest['source_commit']}.")
    print('Integrity verified; archival labels and model performance remain unvalidated.')


if __name__ == '__main__':
    main()
