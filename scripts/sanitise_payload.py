#!/usr/bin/env python3
"""Build a content-free demo using a closed field allow-list.

Transformation is not publication approval; use only approved source selections.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def build_public(source: dict) -> dict:
    jobs, records, ids = [], [], {}
    for n, job in enumerate(source.get('jobs', []), 1):
        demo_id = f'demo-{n:03d}'
        ids[job.get('id')] = demo_id
        jobs.append({'id': demo_id, 'name': f'Demonstration {n}',
                     'type': 'mixed', 'status': 'draft', 'intake': {},
                     'files': 0, 'sizeKB': 0, 'counts': {}})
    indexed = {j['id']: j for j in jobs}
    kinds = {'image', 'email', 'document', 'tabular', 'other'}
    for n, row in enumerate(source.get('records', []), 1):
        job_id = ids.get(row.get('jobId'))
        if job_id is None:
            raise ValueError('record has no corresponding job')
        kind = row.get('kind')
        kind = kind if isinstance(kind, str) and kind in kinds else 'other'
        size = row.get('sizeKB')
        size = size if type(size) in (int, float) and math.isfinite(size) and size >= 0 else 0
        record = {'id': f'r{n:05d}', 'jobId': job_id, 'kind': kind,
                  'filename': f'item-{n:05d}', 'folder': 'demo-folder',
                  'title': f'Demonstration item {n}', 'sizeKB': size,
                  'description': 'Content withheld from demonstration.',
                  'keywords': [], 'flags': [], 'entities': [], 'generated': [],
                  'rationale': 'Evidence withheld from demonstration.', 'why': {},
                  'dispo': None, 'decidedAt': None}
        for key in ('importance', 'confidence'):
            value = row.get(key)
            record[key] = value if isinstance(value, str) and value in {'high', 'medium', 'low'} else 'low'
        records.append(record)
        job = indexed[job_id]
        job['files'] += 1
        job['sizeKB'] += size
        job['counts'][kind] = job['counts'].get(kind, 0) + 1
    return {'jobs': jobs, 'records': records, 'public': True,
            'notice': 'Content-free demonstration. Source selection and publication require review.'}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('payload')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    try:
        source = json.loads(Path(args.payload).read_text(encoding='utf-8'))
        payload = build_public(source)
    except (ValueError, TypeError, KeyError, AttributeError):
        print('REFUSING TO WRITE: invalid payload')
        return 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, allow_nan=False), encoding='utf-8')
    print(f"wrote {len(payload['records'])} demonstration records")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
