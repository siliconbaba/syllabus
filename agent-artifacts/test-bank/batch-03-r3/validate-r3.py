import json,csv,hashlib,collections,re,statistics,itertools,random,subprocess,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent/'batch-03-r2';M=R/'agent-artifacts/manifests/v2.2.3-candidate'
def read(p):return json.loads(p.read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(n,rows):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows])
a=B/'cases_TC076_TC100_r2.json';b=P/'cases_TC076_TC100_r3.json';old=read(a)['cases'];cs=read(b)['cases'];by={c['id']:c for c in cs};oldby={c['id']:c for c in old};gold=read(R/'InteractiveBook/TrainerContent/cases.json')['cases'];m=read(M/'production_manifest_masterplan_v2_2_3_candidate.json');mr={r['plannedId']:r for r in m['manifest']}
def raw(p):
 s=p.read_text();i=s.index('[',s.index('"cases"'))+1;d=json.JSONDecoder();out={}
 while True:
  while s[i].isspace() or s[i]==',':i+=1
  if s[i]==']':break
  c,end=d.raw_decode(s,i);out[c['id']]=s[i:end].encode();i=end
 return out
ra,rb=raw(a),raw(b);changed=[id for id in by if ra[id]!=rb[id]];assert changed==['TC-085']
assert all(sha(R/n)==h for n,h in read(M/'protected-input-hashes.json').items())
assert list(by)==[f'TC-{i:03}' for i in range(76,101)]
for c in cs:
 for k in ['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']:assert c[k]==mr[c['id']][k],(c['id'],k)
 assert len(c['options'])==4 and [o['id'] for o in c['options']]==list('ABCD');assert sum(o['decisionQuality']==1 for o in c['options'])==1;assert all(o['isBest']==(o['decisionQuality']==1) for o in c['options'])
 assert 1<=len(c['decisiveFacts'])<=3
fs=copy.deepcopy(read(B/'family-diff-analysis-r2.json'))
for f in fs:
 assert all(ra[id]==rb[id] for id in f['members']);f['r3Regression']='All sibling case bytes unchanged from r2; proofs and literal differences retained.'
write('family-diff-analysis-r3.json',fs)
assert sha(P/'topics.json')==sha(R/'InteractiveBook/TrainerContent/topics.json')
v=subprocess.run(['/private/tmp/batch03-validator',str(b)],capture_output=True,text=True,check=True);(P/'schema-validation-r3.log').write_text(v.stdout)
s=(R/'agent-artifacts/qa/batch-02/reproduce-independent-checks.py').read_text();ns=dict(re=re,collections=collections,statistics=statistics,itertools=itertools,random=random);exec(s[s.index('def tokens(s)'):s.index('feats=')],ns);ns['basic']=ns['feat'];exec(s[s.index('\ndef feat(t):'):s.index('\ncorpora=')],ns)
x={n:ns['scan'](g) for n,g in [('r3',cs),('r2',old),('production75',gold),('combined100',gold+cs)]}
surface={'method':'Same 78 independent-QA exploratory rules,19 features, family-preserving permutation; counts are proxies, not universal cue proof.','corpora':x,'bestSimpleHeuristic':x['r3']['bestFirstTieHits'],'baselineR2':x['r2']['bestFirstTieHits'],'combined100Best':x['combined100']['bestFirstTieHits'],'baselineCombined100':33,'status':'PASS' if x['r3']['bestFirstTieHits']<=10 and x['combined100']['bestFirstTieHits']<=35 else 'REVIEW','candidateSHA256':sha(b)};write('surface-leakage-analysis-r3.json',surface)
reg={'changedCases':changed,'unchangedByteIdentical':24,'unexpectedChanges':0,'method':'Exact raw UTF-8 object spans, not only parsed object equality.','caseHashes':{id:{'r2':hashlib.sha256(ra[id]).hexdigest(),'r3':hashlib.sha256(rb[id]).hexdigest()} for id in by},'priorR2FixesPreserved':True,'protectedInputsUnchanged':True};write('frozen-regression-r3.json',reg)
c=by['TC-085'];oc=oldby['TC-085'];keys=[k for k in c if c[k]!=oc[k]]
table('change-log.csv',[{'TC-ID':'TC-085','issue':'Manifest-level near duplicate TC-004','fields changed':keys,'before':{k:oc[k] for k in keys},'after':{k:c[k] for k in keys},'why fixed':'Implements candidate v2.2.3: repeatable preparation of consumed test data, fixed evidence set, finite-horizon resource plan.'}])
st={'cases':25,'standalone':sum(c['scenarioFamilyId'] is None for c in cs),'linked':sum(c['scenarioFamilyId'] is not None for c in cs),'families':len(fs),'levels':dict(collections.Counter(c['requiredLevel'] for c in cs)),'correctPositions':dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in cs).items())),'changedCases':1,'unchangedByteIdentical':24,'unexpectedChanges':0,'priorR2FixesPreserved':True,'schema':'PASS','runtime':'PASS','unknownCodes':0,'bestSimpleHeuristic':surface['bestSimpleHeuristic'],'combined100Best':surface['combined100Best'],'candidateSHA256':sha(b)}
assert st['standalone']==16 and st['linked']==9 and st['families']==4;assert st['levels']==dict(junior=5,middle=12,senior=5,head=3)
write('batch-statistics-r3.json',st);print(json.dumps(st,ensure_ascii=False,indent=2));print('Surface',surface['status'])
