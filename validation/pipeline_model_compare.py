"""Synthetic integration smoke comparisons using the actual pipeline prompts.

This module never reads real accession files. It is not the full validation rubric.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from scripts.run_describe import PROMPT as TEXT_PROMPT, call_ollama, call_vllm
from scripts.run_vision import PROMPT as VISION_PROMPT

TEXT_CASES = [
    {'id': 'synthetic-minutes', 'text': 'Minutes of the Fictional River Study Committee. The committee met on 14 May 2025. Members approved a revised sampling schedule and agreed to review the results at the next meeting. No personal information or real institutional records are included.', 'expected_genre': 'minutes'},
    {'id': 'synthetic-email', 'text': 'From: researcher@example.invalid\nTo: curator@example.invalid\nSubject: Fictional sample transfer\nPlease find the synthetic experiment summary attached. We propose transferring the test results after the next review. This invented correspondence contains no real accession information.', 'expected_genre': 'correspondence'},
    {'id': 'synthetic-unreadable', 'text': '%%% [unreadable synthetic input] %%%', 'expected_readable': False},
]


def parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = '\n'.join(text.splitlines()[1:-1])
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('Output is not an object')
    return value


def assess(text, lane, case):
    try:
        value = parse_json(text)
    except (ValueError, TypeError):
        return {'json_object': False, 'schema_valid': False}
    if lane == 'text':
        valid = (isinstance(value.get('description'), str)
                 and isinstance(value.get('subjects'), list)
                 and all(isinstance(x, str) for x in value['subjects'])
                 and type(value.get('readable')) is bool
                 and value.get('genre') in {'correspondence', 'report', 'draft', 'minutes', 'form', 'dataset', 'publication', 'notes', 'list traffic', 'administrative', 'unknown'}
                 and value.get('confidence') in {'high', 'medium', 'low'}
                 and (isinstance(value.get('title'), str) if value.get('readable') else value.get('title') is None))
    else:
        valid = (isinstance(value.get('title'), str) and isinstance(value.get('description'), str)
                 and type(value.get('offensive')) is bool
                 and all(k in value for k in ['offense_evidence', 'offense_category', 'offense_reason', 'confidence']))
    result = {'json_object': True, 'schema_valid': valid}
    for field in ['genre', 'readable']:
        if 'expected_' + field in case:
            result[field + '_matches_fixture'] = value.get(field) == case['expected_' + field]
    return result


def vision_cases():
    from PIL import Image, ImageDraw
    rows = []
    for name, color in [('red-square', 'red'), ('blue-circle', 'blue')]:
        image = Image.new('RGB', (256, 256), 'white')
        draw = ImageDraw.Draw(image)
        (draw.rectangle if name.endswith('square') else draw.ellipse)((64, 64, 192, 192), fill=color)
        rows.append({'id': 'synthetic-' + name, 'image': image})
    return rows


def run(models, lane='text', backend='hf', url=None, out=None):
    if backend in {'ollama', 'vllm'} and not url:
        raise ValueError('Supply the endpoint explicitly; do not assume a server service')
    if lane == 'vision' and backend not in {'hf', 'stub'}:
        raise ValueError('The vision smoke comparison currently supports hf or stub only')
    cases = TEXT_CASES if lane == 'text' else vision_cases()
    prompt_source = TEXT_PROMPT if lane == 'text' else VISION_PROMPT
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True).strip()
    rows = []
    revisions = {}
    for model in models:
        pipe = None
        if backend == 'hf':
            import torch
            from huggingface_hub import HfApi
            from transformers import pipeline
            if not torch.cuda.is_available():
                raise RuntimeError('Select a Colab GPU runtime before model comparison')
            revisions[model] = HfApi().model_info(model).sha
            torch.manual_seed(0)
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            pipe = pipeline('text-generation' if lane == 'text' else 'image-text-to-text',
                model=model, revision=revisions[model], device_map='auto', dtype=dtype, trust_remote_code=False)
        for case in cases:
            prompt = TEXT_PROMPT % case['text'] if lane == 'text' else VISION_PROMPT
            started = time.perf_counter()
            row = {'case': case['id'], 'model': model, 'backend': backend, 'lane': lane,
                   'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
            try:
                if backend == 'stub':
                    output = json.dumps({'title': None if case.get('expected_readable') is False else 'Synthetic sample',
                        'description': 'Synthetic test response; no inference performed.', 'subjects': ['synthetic'],
                        'genre': case.get('expected_genre', 'unknown'), 'readable': case.get('expected_readable', True),
                        'confidence': 'low', 'offensive': False, 'offense_category': None,
                        'offense_evidence': None, 'offense_reason': None})
                elif backend in {'ollama', 'vllm'}:
                    output = (call_ollama if backend == 'ollama' else call_vllm)(prompt, url, model, 180)
                elif lane == 'text':
                    generated = pipe([{'role': 'user', 'content': prompt}], max_new_tokens=400, do_sample=False)
                    output = generated[0]['generated_text'][-1]['content']
                else:
                    messages = [{'role': 'user', 'content': [{'type': 'image', 'image': case['image']}, {'type': 'text', 'text': prompt}]}]
                    output = pipe(text=messages, max_new_tokens=400, do_sample=False)[0]['generated_text'][-1]['content']
                row.update(output=output, metrics=assess(output, lane, case))
            except Exception as exc:
                row.update(error=type(exc).__name__ + ': ' + str(exc), metrics={'json_object': False, 'schema_valid': False})
            row['elapsed_seconds'] = round(time.perf_counter() - started, 3)
            rows.append(row)
        if pipe is not None:
            del pipe
            import gc, torch
            gc.collect()
            torch.cuda.empty_cache()
    versions = {}
    for dependency in ['transformers', 'torch', 'pyarrow', 'Pillow', 'requests']:
        try:
            versions[dependency] = importlib.metadata.version(dependency)
        except importlib.metadata.PackageNotFoundError:
            versions[dependency] = None
    report = {'dataset': 'generated-synthetic-smoke-v1', 'code_commit': commit, 'tracked_code_modified': bool(status),
        'created_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
        'generation': {'max_new_tokens': 400, 'do_sample': False, 'seed': 0},
        'versions': versions, 'model_revisions': revisions, 'endpoint': url, 'rows': rows,
        'gpu': __import__('torch').cuda.get_device_name(0) if backend == 'hf' else 'remote or not used; not verified by this harness',
        'limitations': 'Smoke cases only. No real accession data. No appraisal accuracy, calibrated confidence or throughput benchmark established. Stub results are not model results.'}
    if out:
        destination = Path(out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+', required=True)
    parser.add_argument('--lane', choices=['text', 'vision'], default='text')
    parser.add_argument('--backend', choices=['hf', 'ollama', 'vllm', 'stub'], default='stub')
    parser.add_argument('--url')
    parser.add_argument('--out', default='local-runs/synthetic-smoke.json')
    args = parser.parse_args()
    result = run(args.models, args.lane, args.backend, args.url, args.out)
    print(json.dumps({'cases': len(result['rows']), 'backend': args.backend, 'output': args.out}))
