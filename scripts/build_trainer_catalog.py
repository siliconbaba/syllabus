#!/usr/bin/env python3
"""Generate bundled trainer topic names from the canonical book TOC, at build time only."""
import argparse
import json
import re
from pathlib import Path
from check_content import Parser

ROOT = Path(__file__).resolve().parents[1]


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--check', action='store_true', help='Fail if bundled metadata is stale')
    check = args.parse_args().check
    parser = Parser()
    parser.feed((ROOT / 'InteractiveBook/WebContent/index.html').read_text())
    sections, topics, seen = [], [], set()
    for node in parser.root.all():
        href = node.attrs.get('href', '')
        if node.tag != 'a' or not href.startswith('#') or href in seen:
            continue
        identifier = href[1:]
        if re.fullmatch(r'part-\d+', identifier):
            title = re.sub(r'^[▶\s]*Часть \d+\.\s*', '', node.text()).strip()
            sections.append(dict(id=identifier, title=title))
        elif re.fullmatch(r't-\d+-\d+', identifier):
            topics.append(dict(id=identifier, sectionID='part-' + identifier.split('-')[1], title=node.text()))
        else:
            continue
        seen.add(href)
    metadata = dict(sections=sections, topics=topics)
    bank = json.loads((ROOT / 'InteractiveBook/TrainerContent/cases.json').read_text())
    missing = {case['topicId'] for case in bank['cases']} - {topic['id'] for topic in topics}
    if missing:
        raise SystemExit('Trainer topics missing from book: ' + ', '.join(sorted(missing)))
    if bank.get('schemaVersion') != '2.0':
        raise SystemExit('Production trainer bank must use schemaVersion 2.0')
    topic_sections = {topic['id']: topic['sectionID'] for topic in topics}
    for case in bank['cases']:
        if case.get('partId') != topic_sections.get(case['topicId']):
            raise SystemExit('Trainer part/topic mismatch: ' + case['id'])
    path = ROOT / 'InteractiveBook/TrainerContent/topics.json'
    if check:
        if json.loads(path.read_text()) != metadata:
            raise SystemExit('Trainer catalog is stale: run python3 scripts/build_trainer_catalog.py')
        print('PASS: trainer catalog matches book and covers bank topics')
    else:
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
        print(f'Wrote {len(sections)} sections and {len(topics)} topic titles')


if __name__ == '__main__':
    main()
