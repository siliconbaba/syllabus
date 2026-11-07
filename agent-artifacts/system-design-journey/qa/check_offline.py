"""Static render dependency and trust-boundary checks; no layout claims."""
from pathlib import Path
from html.parser import HTMLParser
import json,re
ROOT=Path(__file__).resolve().parent.parent
class Scan(HTMLParser):
    def __init__(self):super().__init__();self.errors=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ['script','img','iframe','audio','video','source','link']:
            for k in ['src','href','srcset']:
                if re.search(r'^(https?:)?//',a.get(k,'')):self.errors.append(f'External render dependency: {tag} {k}')
        for k in a:
            if k.startswith('on'):self.errors.append('Inline event attribute: '+tag+' '+k)
file=ROOT/('system-design.html' if (ROOT/'system-design.html').exists() else 'template.html')
text=file.read_text();p=Scan();p.feed(text)
for pattern in [r'@import\b',r'url\([\"\']?https?:',r'\bfetch\(',r'\bXMLHttpRequest\b',r'\bimport\s*\(']:
    if re.search(pattern,text,re.I):p.errors.append('External/code dependency pattern: '+pattern)
result={'file':file.name,'status':'PASS' if not p.errors else 'FAIL','issues':p.errors,'scope':'Static only; real browser layout NOT_RUN'}
(ROOT/'qa'/'offline-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(bool(p.errors))
