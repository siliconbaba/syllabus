import json,csv,re,hashlib,copy,difflib,collections,statistics,itertools,random,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OLD=P.parent/'batch-02';QA=ROOT/'agent-artifacts/qa/batch-02';MP=ROOT/'agent-artifacts/manifests/v2.2'
def read(p):return json.loads(p.read_text())
def write(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=read(OLD/'cases_TC051_TC075.json');new=read(P/'cases_TC051_TC075_r2.json');gold=read(ROOT/'InteractiveBook/TrainerContent/cases.json')['cases'];ob={c['id']:c for c in old['cases']};nb={c['id']:c for c in new['cases']}
ph=read(P/'protected-input-hashes.json');assert all(sha(ROOT/p)==h for p,h in ph.items())
assert len(new['cases'])==25 and list(nb)==[f'TC-{n:03}' for n in range(51,76)]
changed=[i for i in nb if nb[i]!=ob[i]];assert changed==['TC-051','TC-052','TC-053','TC-068','TC-074']
metadata=['id','type','partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','decisiveMutation','trainingEligible','assessmentEligible']
manifest={r['plannedId']:r for r in read(MP/'production_manifest_masterplan_v2_2.json')['manifest']}
for i,c in nb.items():
 assert all(c[k]==ob[i][k] for k in metadata)
 for k in ['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']:assert c[k]==manifest[i][k]
 assert len(c['options'])==4 and [o['id'] for o in c['options']]==list('ABCD')
 assert sum(o['decisionQuality']==1 for o in c['options'])==sum(o['isBest'] for o in c['options'])==1
 assert 1<=len(c['decisiveFacts'])<=3
positions=lambda cs:dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in cs).items()))
assert positions(new['cases'])==dict(A=6,B=6,C=6,D=7)
# Exact raw-fragment preservation, and whole-file proof that only approved object spans differ.
def frag(c):return '\n'.join('    '+line for line in json.dumps(c,ensure_ascii=False,indent=2).splitlines())
a=(OLD/'cases_TC051_TC075.json').read_text();b=(P/'cases_TC051_TC075_r2.json').read_text();reconstructed=a
for i in nb:
 if i in changed:reconstructed=reconstructed.replace(frag(ob[i]),frag(nb[i]),1)
 else:assert frag(ob[i]) in a and frag(ob[i]) in b
assert b==reconstructed

def diff(a,b,path=''):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):return [d for k in a.keys()|b.keys() for d in diff(a.get(k),b.get(k),path+'.'+k if path else k)]
 if isinstance(a,list):return [d for j,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,f'{path}[{j}]')] if len(a)==len(b) else [(path,a,b)]
 return [] if a==b else [(path,a,b)]
changes={i:sorted(diff(ob[i],nb[i])) for i in changed};quality=[dict(id=i,field=k,before=a,after=b) for i,ds in changes.items() for k,a,b in ds if k.endswith('decisionQuality')]
keys=[i for i in nb if next(o['id'] for o in nb[i]['options'] if o['isBest'])!=next(o['id'] for o in ob[i]['options'] if o['isBest'])];assert not keys
issues=list(csv.DictReader((QA/'case-fixes.csv').open(encoding='utf-8-sig')))
write('regression.json',dict(changedCases=changed,unchangedCases=[i for i in nb if i not in changed],frozen19ByteIdentical=True,TC075ByteIdentical=True,unexpectedFrozenRegression=0,metadataChanges=[],strongestKeyChanges=keys,decisionQualityChanges=quality,changedFields={i:[d[0] for d in ds] for i,ds in changes.items()},expectedSixChangedException='TC-075 remains unchanged because the user expressly permits UNRESOLVED for a manifest-level duplicate. No cosmetic revision or false closure.',protectedInputsUnchanged=True))
# All four contracts; only F-DM-T01 may change relative to r1.
families=[]
for f in csv.DictReader((MP/'linked_family_manifest_v2_2.csv').open(encoding='utf-8-sig')):
 ids=json.loads(f['memberIds'])
 if not set(ids)&set(nb):continue
 cs=[nb[i] for i in ids]
 assert len({c['question'] for c in cs})==1
 assert all([(o['id'],o['text']) for o in c['options']]==[(o['id'],o['text']) for o in cs[0]['options']] for c in cs)
 diffs=[]
 for c in cs[1:]:
  sm=difflib.SequenceMatcher(None,cs[0]['context'],c['context'],autojunk=False)
  diffs.append(dict(a=cs[0]['id'],b=c['id'],changes=[dict(before=cs[0]['context'][i:j],after=c['context'][k:l]) for op,i,j,k,l in sm.get_opcodes() if op!='equal']))
 if f['scenarioFamilyId']=='F-DM-T01':
  bases=[c['context'].split('Стоимость задержки принятого Н — ')[0] for c in cs];assert len(set(bases))==1
  assert [c['context'].split('Стоимость задержки принятого Н — ')[1] for c in cs]==['1 млн ₽ в неделю.','4 млн ₽ в неделю.','10 млн ₽ в неделю.']
 else:assert all(nb[i]==ob[i] for i in ids)
 families.append(dict(familyId=f['scenarioFamilyId'],contract=f,positions={i:manifest[i]['familyPosition'] for i in ids},questionOptionsOrderIdentical=True,contextDiffs=diffs,changed=f['scenarioFamilyId']=='F-DM-T01',status='PASS'))
families[0]['proof']={'singleVariable':'Cost of Delay Н; 1 / 4 / 10. Same size, strategic fit, 6 direct switching cost, uncertainty bounds, order-ID overlap and acceptance capacity in every sibling.','costs':{'A':'2x+[5,7]','B':'4x+3','C':'4x','D':'6+[12,14]'},'states':{'TC-051':{'ranges':[[7,9],[7,7],[4,4],[18,20]],'strongest':'C'},'TC-052':{'ranges':[[13,15],[19,19],[16,16],[18,20]],'strongest':'A'},'TC-053':{'ranges':[[25,27],[43,43],[40,40],[18,20]],'strongest':'D'}},'boundary1':'x<2.5 guarantees C; x>3.5 makes A beat C. The uncertainty zone is not sampled.','boundary2':'3.5<x<5.5 guarantees A; x>7.5 guarantees D. States avoid all ties and ranking-uncertainty zones.','sourceOfSeniorReasoning':'Values are an audit proof derived AFTER inferring outcome dependence, overlapping loss registers and acceptance bottleneck; not a ready-made cost table in the question.'}
write('family-diff-analysis-r2.json',families)
# Reuse EXACT independent QA feature extraction/rules/scan with no writes into QA.
s=(QA/'reproduce-independent-checks.py').read_text();ns=dict(re=re,collections=collections,statistics=statistics,itertools=itertools,random=random)
exec(s[s.index('def tokens(s)'):s.index('feats=')],ns);ns['basic']=ns['feat']
exec(s[s.index('\ndef feat(t):'):s.index('\ncorpora=')],ns)
scan=ns['scan'];oldscan=json.loads(json.dumps(scan(old['cases'])));newscan=scan(new['cases']);corpus=scan(gold+new['cases'])
qa_stats=read(QA/'batch-statistics-independent.json')['independentSurface']['batch02']
write('qa-baseline-reproduced.json',oldscan)
assert all(oldscan[k]==qa_stats[k] for k in ['count','rules','bestFirstTieHits','bestRandomTieExpectedHits','positions','keySequence','featureMeans','optionFeatures']),'Independent QA feature/rule reproduction differs'
singles=lambda x:max(r['firstTieHits'] for r in x['rules'] if len(r['rule'])==1)
write('batch-statistics-r2.json',dict(before=oldscan,after=newscan,combined75=corpus,bestSingleBefore=singles(oldscan),bestSingleAfter=singles(newscan),composition=read(QA/'batch-statistics-independent.json')['composition'],correctPositions=positions(new['cases']),metadataChanges=0,qualityChanges=quality,surfaceBaselineReproducedExactly=True,method='Exact independent QA feature extraction and 78 rules, same seed and family-preserving permutation. No QA artifact writes.',candidateSHA256=sha(P/'cases_TC051_TC075_r2.json')))
# Strict loader compiled from production sources, previous harness reads a bank of 25.
r=subprocess.run(['/private/tmp/batch02-r2-loader',str(P/'cases_TC051_TC075_r2.json')],capture_output=True,text=True,check=True);(P/'schema-validation.log').write_text(r.stdout)
assert sha(P/'topics.json')==sha(ROOT/'InteractiveBook/TrainerContent/topics.json')
print(json.dumps(dict(changed=len(changed),unchanged=25-len(changed),positions=positions(new['cases']),qualityChanges=len(quality),combinedHeuristicBefore=oldscan['bestFirstTieHits'],combinedHeuristicAfter=newscan['bestFirstTieHits'],singleHeuristicBefore=singles(oldscan),singleHeuristicAfter=singles(newscan),expectedAfter=newscan['bestRandomTieExpectedHits'],schema='PASS',remaining=['TC-075']),ensure_ascii=False,indent=2))
