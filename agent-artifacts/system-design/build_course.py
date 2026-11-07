#!/usr/bin/env python3
"""Generate the offline course from reviewed content; no network/dependencies."""
import json
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent

def build(output):
    modules = []
    for name in ('content-a.json', 'content-b.json', 'content-c.json'):
        path = ROOT / name
        if not path.exists():
            raise SystemExit(f'Missing reviewed course content: {path}')
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            data = data['modules']
        modules.extend(data)
    # Retain stable IDs for existing workbooks; move the capstone after new material.
    modules.sort(key=lambda m: int(m['id'][3:]) if m['id'] != 'sd-10' else 99)
    assert len(modules) == 13, 'Expected thirteen modules'
    assert sum(m['minutes'] for m in modules) == 1560, 'Expected 26 hours'
    assert len({m['id'] for m in modules}) == len(modules), 'Duplicate module IDs'
    for m in modules:
        assert all(k in m for k in ('title','intro','lessons','practice','quiz','sources')), m['id']
        assert len(m['lessons']) >= 4 and len(m['quiz']) >= 3, m['id']
        for q in m['quiz']:
            assert isinstance(q['answer'], int) and 0 <= q['answer'] < len(q['options']), m['id']
        for s in m['sources']:
            assert s['url'].startswith('https://'), s
    payload = json.dumps(modules, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    html = (ROOT / 'course-template.html').read_text().replace('/*__COURSE_DATA__*/[]', payload)
    assert '/*__COURSE_DATA__*/' not in html
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    print(f'Built {output}: {len(modules)} modules, {sum(len(m["quiz"]) for m in modules)} questions, {sum(m["minutes"] for m in modules)} minutes')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=ROOT/'system-design.html')
    build(p.parse_args().output)
