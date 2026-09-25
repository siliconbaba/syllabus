#!/usr/bin/env python3
"""Pinned, offline preparation. Validate all sources BEFORE copying anything."""
from pathlib import Path
import hashlib,json,shutil,sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'Config/SileroResources.json').read_text());target=root/'InteractiveBook/SileroResources'
for name,entry in manifest['files'].items():
 source=root/entry['source']
 if not source.is_file():sys.exit(f'Missing verified Silero artifact: {source}. See docs/SILERO_BUILD.md. No automatic download.')
 if source.stat().st_size!=entry['bytes'] or hashlib.sha256(source.read_bytes()).hexdigest()!=entry['sha256']:sys.exit(f'SHA256/size mismatch: {source}; refusing to package models.')
target.mkdir(exist_ok=True)
for name,entry in manifest['files'].items():shutil.copyfile(root/entry['source'],target/name)
shutil.copyfile(root/'Config/SileroResources.json',target/'manifest.json')
allowed=set(manifest['files'])|{'manifest.json','.gitkeep'}
extra=[p.name for p in target.iterdir() if p.name not in allowed]
if extra:sys.exit(f'Unexpected files in canonical resources: {extra}; remove them before building.')
print(f'Prepared {len(manifest["files"])} verified resources, {sum(x["bytes"] for x in manifest["files"].values()):,} bytes; no downloads.')
