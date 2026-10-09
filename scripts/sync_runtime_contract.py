#!/usr/bin/env python3
"""Generate or verify read-only reference copies of authoritative scoring sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'agent-artifacts/runtime-contract'
NAMES = ('TrainerScoringMapping.swift', 'TrainerScoringEngine.swift')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify without rewriting')
    args = parser.parse_args()
    contents = {name: (ROOT / 'InteractiveBook/Trainer' / name).read_bytes() for name in NAMES}
    manifest = {'authoritativeDirectory': 'InteractiveBook/Trainer', 'referenceOnly': True,
                'files': {name: {'source': 'InteractiveBook/Trainer/' + name,
                                 'sha256': hashlib.sha256(data).hexdigest()}
                          for name, data in contents.items()}}
    contents['runtime-contract-hashes.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    if args.check:
        for name, data in contents.items():
            path = DEST / name
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit(f'Stale runtime reference: {path}; run python3 scripts/sync_runtime_contract.py')
        print('PASS: runtime reference copies and SHA-256 match authoritative Swift sources')
    else:
        DEST.mkdir(parents=True, exist_ok=True)
        for name, data in contents.items():
            (DEST / name).write_bytes(data)
        print(f'Wrote runtime reference copies to {DEST}')


if __name__ == '__main__':
    main()
