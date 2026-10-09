#!/usr/bin/env python3
"""Build a standalone offline HTML from the canonical app content (stdlib only)."""
from pathlib import Path
import argparse
import re
from check_content import Parser, check

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'InteractiveBook' / 'WebContent'

def build(output):
    check()
    original = (SOURCE / 'index.html').read_text(encoding='utf-8')
    counts = {'style': 0, 'script': 0}

    def embed(tag, filename):
        asset = (SOURCE / filename).resolve()
        if not asset.is_relative_to(SOURCE.resolve()):
            raise ValueError('Asset outside WebContent: ' + filename)
        content = asset.read_text(encoding='utf-8')
        if re.search(r'</' + tag + r'\b', content, re.I):
            raise ValueError('Unsafe embedded closing tag in ' + filename)
        counts[tag] += 1
        return f'<{tag} data-bundled-from="{filename}">\n{content}\n</{tag}>'

    html = re.sub(r'<link\s+rel="stylesheet"\s+href="(?P<file>[^"]+)"\s*>',
                  lambda m: embed('style', m.group('file')), original)
    html = re.sub(r'<(?P<tag>script)\s+src="(?P<file>[^"]+)"\s*>\s*</script>', lambda m: embed('script', m.group('file')), html)
    parsed = Parser()
    parsed.feed(html)
    nodes = list(parsed.root.all())
    if parsed.errors or len(parsed.stack) != 1:
        raise ValueError('Invalid standalone HTML: ' + str(parsed.errors[:5]))
    if any(n.attrs.get('src') or n.tag == 'link' and n.attrs.get('rel') == 'stylesheet' for n in nodes):
        raise ValueError('Unbundled resource remains')
    before = Parser()
    before.feed(original)
    # Only resource wrappers change; every content anchor and question must survive.
    assert [n.attrs['id'] for n in before.root.all() if 'id' in n.attrs] == [n.attrs['id'] for n in nodes if 'id' in n.attrs]
    assert sum(n.has('bank-question') for n in nodes) == 100
    assert sum(n.has('answer-variant') for n in nodes) == 300
    assert counts == {'style': 2, 'script': 6}, counts
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding='utf-8')
    print(f'Built {output} ({output.stat().st_size:,} bytes); 2 stylesheets and 6 scripts embedded.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build' / 'web' / 'Управление процессами и проектами.html')
    build(parser.parse_args().output)
