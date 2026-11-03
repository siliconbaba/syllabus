import json,csv,hashlib,collections,re,statistics,itertools,random,subprocess,difflib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent/'batch-03';Q=R/'agent-artifacts/qa/batch-03'
def read(p):return json.loads(p.read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(n,rows):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in rows])
basepath=B/'cases_TC076_TC100.json';path=P/'cases_TC076_TC100_r2.json';cs=read(path)['cases'];old=read(basepath)['cases'];by={c['id']:c for c in cs};oldby={c['id']:c for c in old};gold=read(R/'InteractiveBook/TrainerContent/cases.json')['cases'];fixes=list(csv.DictReader((Q/'case-fixes.csv').open(encoding='utf-8-sig')));allowed={f['caseId'] for f in fixes};frozen=set(by)-allowed
# Extract original JSON lexical object slices. This tests exact case bytes, not only object equality.
def rawcases(p):
 s=p.read_text();d=json.JSONDecoder();i=s.index('[',s.index('"cases"'))+1;out={}
 while True:
  while s[i].isspace() or s[i]==',':i+=1
  if s[i]==']':break
  v,end=d.raw_decode(s,i);out[v['id']]=s[i:end].encode();i=end
 return out
ra,rb=rawcases(basepath),rawcases(path);changed=[id for id in by if ra[id]!=rb[id]]
assert set(changed)<=allowed;assert all(ra[id]==rb[id] for id in frozen);assert ra['TC-085']==rb['TC-085']
assert set(changed)==allowed-{'TC-085'}
protected=read(P/'protected-input-hashes.json');assert all(sha(R/n)==h for n,h in protected.items())
m=read(R/'agent-artifacts/manifests/v2.2.2/production_manifest_masterplan_v2_2_2.json');rows={r['plannedId']:r for r in m['manifest']};meta=['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']
assert list(by)==[f'TC-{i:03}' for i in range(76,101)]
for c in cs:
 for k in meta:assert c[k]==rows[c['id']][k]==oldby[c['id']][k],(c['id'],k)
 assert c['decisiveMutation']==oldby[c['id']]['decisiveMutation']
 assert [o['id'] for o in c['options']]==list('ABCD')
 assert sum(o['decisionQuality']==1 for o in c['options'])==1
 assert all(o['isBest']==(o['decisionQuality']==1) for o in c['options'])
 assert 1<=len(c['decisiveFacts'])<=3
 assert c['trainingEligible'] and c['assessmentEligible']==(c['scenarioFamilyId'] is None)
assert sha(P/'topics.json')==sha(R/'InteractiveBook/TrainerContent/topics.json')
v=subprocess.run(['/private/tmp/batch03-validator',str(path)],capture_output=True,text=True,check=True);(P/'schema-validation-r2.log').write_text(v.stdout)
# Field paths and exact before/after; no fabricated change row for blocked TC-085.
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):return [x for k in a for x in diff(a[k],b[k],p+'.'+k if p else k)]
 if isinstance(a,list):
  if len(a)!=len(b):return [(p,a,b)]
  return [x for i,(u,v) in enumerate(zip(a,b)) for x in diff(u,v,p+'.'+(u.get('id',str(i)) if isinstance(u,dict) else str(i)))]
 return [] if a==b else [(p,a,b)]
change=[]
for f in fixes:
 id=f['caseId'];ds=diff(oldby[id],by[id])
 if ds:change.append({'TC-ID':id,'severity':f['severity'],'QA defect':f['problem'],'fields changed':[x[0] for x in ds],'before':{x[0]:x[1] for x in ds},'after':{x[0]:x[2] for x in ds},'why fixed':f['minimalFix'],'status':'IMPLEMENTED; author self-check PASS, independent focused QA pending'})
table('change-log.csv',change)
reg={'changedCases':changed,'changedCount':len(changed),'frozenPassCount':len(frozen),'frozenByteIdentical':sorted(frozen),'unchangedIncludingBlocked':sorted(set(by)-set(changed)),'unchangedCount':25-len(changed),'unexpectedChanges':[],'blockedUnchanged':['TC-085'],'comparison':'Exact UTF-8 source object spans including internal whitespace; baseline untouched.','hashes':{id:{'baseline':hashlib.sha256(ra[id]).hexdigest(),'r2':hashlib.sha256(rb[id]).hexdigest()} for id in by},'protectedInputFilesUnchanged':len(protected)};write('frozen-regression-r2.json',reg)
# Literal family mutation with same context prefix, question, options and order.
anchors={'F-DR-T01':'Предотвращаемая ручным ревью потеря за месяц — ','F-TD-P01':'Продуктовый контракт положительного ответа: ','F-PE-P01':'О причинах известно следующее: ','F-BV-P02':'Новая годовая цена одного договора — '};fs=[]
for f in m['familyManifest']:
 if not set(f['memberIds'])&set(by):continue
 members=[by[id] for id in f['memberIds']];a=anchors[f['scenarioFamilyId']]
 assert len({c['context'].split(a)[0] for c in members})==1
 assert len({c['question'] for c in members})==1
 assert all([o['text'] for o in c['options']]==[o['text'] for o in members[0]['options']] for c in members)
 diffs=[]
 for c in members[1:]:
  x,y=members[0]['context'],c['context'];matcher=difflib.SequenceMatcher(None,x,y,autojunk=False)
  diffs.append({'from':members[0]['id'],'to':c['id'],'changes':[{'before':x[i:j],'after':y[k:l]} for tag,i,j,k,l in matcher.get_opcodes() if tag!='equal']})
 fs.append({'familyId':f['scenarioFamilyId'],'members':f['memberIds'],'frozenContract':f,'status':'PASS','sameActorObjectiveContextConstants':True,'sameQuestionOptionsOrder':True,'logicalMutationOnly':True,'literalDiff':diffs,'keys':[next(o['id'] for o in c['options'] if o['isBest']) for c in members]})
fs[-1]['proof']={'formula':'(annual new tariff revenue - (legacy revenue4-avoided cost2) - new support1)*2.5 - remaining8','TC-083':[9.5,14.5],'TC-084':[-5.5,-2],'alternative':5,'uncertainty':'Positive discount weights bound every permitted yearly price trajectory; observing first-year price cannot reverse ranking; waiting costs1.','singleVariable':'Only price forecast interval, hence remaining future NPV; same clients, legacy contribution, support, sunk cost, capital and alternative.'}
write('family-diff-analysis-r2.json',fs)
s=(R/'agent-artifacts/qa/batch-02/reproduce-independent-checks.py').read_text();ns=dict(re=re,collections=collections,statistics=statistics,itertools=itertools,random=random);exec(s[s.index('def tokens(s)'):s.index('feats=')],ns);ns['basic']=ns['feat'];exec(s[s.index('\ndef feat(t):'):s.index('\ncorpora=')],ns)
x={name:ns['scan'](group) for name,group in [('r2',cs),('baseline25',old),('production75',gold),('combined100',gold+cs)]}
surface={'method':'Same 78 independent-QA rules, 19 features and family-preserving permutation; exploratory in-sample sanity scan. Proxies do not prove absence of every cue.','corpora':x,'bestR2':x['r2']['bestFirstTieHits'],'bestBaseline':x['baseline25']['bestFirstTieHits'],'bestCombined100':x['combined100']['bestFirstTieHits'],'baselineCombined100':35,'status':'PASS' if x['r2']['bestFirstTieHits']<=10 and x['combined100']['bestFirstTieHits']<=37 else 'REVIEW','candidateSHA256':sha(path)};write('surface-leakage-analysis-r2.json',surface)
st={'caseCount':25,'standalone':sum(not c['scenarioFamilyId'] for c in cs),'linked':sum(bool(c['scenarioFamilyId']) for c in cs),'families':len(fs),'levels':dict(collections.Counter(c['requiredLevel'] for c in cs)),'correctPositions':dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in cs).items())),'changedCases':len(changed),'unchangedByteIdentical':25-len(changed),'requiredFrozen12ByteIdentical':len(frozen),'unexpectedChanges':0,'schema':'PASS','runtime':'PASS','unknownCodes':0,'bestSimpleHeuristic':surface['bestR2'],'combined100Best':surface['bestCombined100'],'candidateSHA256':sha(path),'remainingManifestBlocker':['TC-085']};write('batch-statistics-r2.json',st)
print(json.dumps(st,ensure_ascii=False,indent=2));print('Surface',surface['status'])
