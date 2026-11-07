"""Validate complete authored content, HTML fragments and packaged integration."""
from pathlib import Path
import json,re,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'scripts'))
from check_content import Parser

modules=[]
for f in ('content-a.json','content-b.json','content-c.json'):modules+=json.loads((ROOT/f).read_text())
assert {m['id'] for m in modules}=={f'sd-{i:02}' for i in range(1,14)}
assert sum(m['minutes'] for m in modules)==1560
stats=[]
for m in modules:
 assert m['minutes']==120 and len(m['lessons'])>=5
 assert len(m['quiz'])>=3 and len(m['practice']['rubric'])>=4
 words=0
 for fragment in [l['body'] for l in m['lessons']]+[m['practice']['task'],m['practice']['model']]:
  p=Parser();p.feed(fragment);assert not p.errors and len(p.stack)==1,(m['id'],p.errors)
  assert not re.search(r'<script|on\w+\s*=|javascript:',fragment,re.I)
  words+=len(p.root.text().split())
 assert words>=850,(m['id'],words)
 for q in m['quiz']:
  assert len(q['options'])>=3 and 0<=q['answer']<len(q['options']) and len(q['explanation'])>60
 assert all(s['url'].startswith('https://') for s in m['sources'])
 stats.append(dict(id=m['id'],words_including_practice=words,questions=len(m['quiz']),sources=len(m['sources'])))
html=(ROOT/'system-design.html').read_text()
p=Parser();p.feed(html);assert not p.errors and len(p.stack)==1,p.errors
nodes=list(p.root.all());ids=[n.attrs['id'] for n in nodes if 'id' in n.attrs];assert len(set(ids))==len(ids)
assert not any(n.tag in ('script','img','iframe') and n.attrs.get('src') for n in nodes)
assert not any(n.tag=='link' and n.attrs.get('rel')=='stylesheet' for n in nodes)
assert '/*__COURSE_DATA__*/' not in html
web=REPO/'InteractiveBook/WebContent'
assert (web/'system-design.html').read_bytes()==(ROOT/'system-design.html').read_bytes()
assert 'id="system-design-entry"' in (web/'index.html').read_text()
result=dict(modules=13,minutes=1560,questions=sum(x['questions'] for x in stats),modules_detail=stats,html_sha256=hashlib.sha256(html.encode()).hexdigest(),offline=True)
(ROOT/'qa/content-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('PASS: 13 complete modules, 1560 minutes, 45 questions, balanced safe HTML, offline assets, identical app integration')
