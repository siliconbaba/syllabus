"""Independent contract checks. Run after authors/build finish; never mutates sources."""
import json, re, html
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
issues=[]
def check(ok,where,msg):
    if not ok: issues.append({'where':where,'issue':msg})
def words(s):
    return len(re.findall(r"[А-Яа-яЁёA-Za-z0-9]+(?:[-–][А-Яа-яЁёA-Za-z0-9]+)*",html.unescape(re.sub('<[^>]+>',' ',s))))
chapters=[]; packs={}
for f in ROOT.glob('chapters-*.json'):
    data=json.loads(f.read_text())
    if isinstance(data,list) and data and isinstance(data[0],dict) and 'sections' in data[0]:
        packs[f.name]=data;chapters.extend(data)
chapters.sort(key=lambda c:c['id'])
check([c['id'] for c in chapters]==[f'ch-{i:02}' for i in range(1,33)],'course','Exactly 32 distinct ordered chapter IDs required')
counts=[]
for c in chapters:
    cid=c['id']; sec=c.get('sections',[]);ex=c.get('workedExample',{});xp=c.get('expedition',{})
    count=words(' '.join(s.get('html','') for s in sec)+' '+ex.get('html','')+' '+xp.get('html',''))
    counts.append({'id':cid,'words_theory_example_expedition':count,'sections':len(sec),'diagrams':len(c.get('diagrams',[]))})
    check(count>=1400,cid,f'Only {count} words; minimum target 1400')
    check(len(sec)>=5,cid,'Fewer than five theory sections')
    for key in ['briefing','goals','workedExample','expedition','decision','exercise','checkpoint','sources','diagrams']:
        check(bool(c.get(key)),cid,'Missing/empty '+key)
    check(len(c.get('checkpoint',[]))==2,cid,'Exactly two checkpoints required')
    d=c.get('decision',{});opts=d.get('options',[])
    check(len(opts)>=2,cid,'Decision needs two reasonable options')
    check(isinstance(d.get('recommended'),int) and 0<=d.get('recommended',-1)<len(opts),cid,'Invalid recommended index')
    for q in c.get('checkpoint',[]):
        check(isinstance(q.get('answer'),int) and 0<=q.get('answer',-1)<len(q.get('options',[])),cid,'Invalid checkpoint answer')
        check(bool(q.get('explanation')),cid,'Missing checkpoint explanation')
    check(xp.get('world') in 'money inventory search geo collaboration media telemetry saas'.split(),cid,'Invalid expedition world')
    for diagram in c.get('diagrams',[]):
        svg=diagram.get('svg','')
        check(not re.search(r'<\s*(script|foreignObject|svg)\b|\bon\w+\s*=|(?:href|src)\s*=\s*[\"\'](?:https?:|data:|javascript:)',svg,re.I),cid,'Unsafe or nested/external SVG')
        ids=re.findall(r'\bid=[\"\']([^\"\']+)',svg)
        check(len(ids)==len(set(ids)),cid,'Duplicate IDs within SVG')
    body=json.dumps(c,ensure_ascii=False)
    check(not re.search(r'<\s*(script|iframe|object|embed)\b|\bon\w+\s*=',body,re.I),cid,'Active content/event handler in chapter')
for name,pack in packs.items():check(sum(len(c.get('diagrams',[])) for c in pack)>=12,name,'Fewer than 12 diagrams per author pack')
atlas=json.loads((ROOT/'atlas.json').read_text()) if (ROOT/'atlas.json').exists() else []
check(len(atlas)==8 and {w.get('id') for w in atlas}==set('money inventory search geo collaboration media telemetry saas'.split()),'atlas','Eight distinct atlas worlds required')
for w in atlas:
    for key in ['title','briefing','sections','transfer','distinct','sources']:check(bool(w.get(key)),w['id'],'Missing atlas '+key)
report={'atlas_count':len(atlas),'status':'PASS' if not issues else 'FAIL','chapter_count':len(chapters),'packs':list(packs),'counts':counts,'issues':issues,'browser_layout':'NOT_RUN — requires actual browser; Node/static checks are not layout validation'}
(ROOT/'qa'/'content-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(issues))
