import json,csv,copy,re,hashlib,collections,statistics,itertools,random,subprocess,difflib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvout(n,rows):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])
M=R/'agent-artifacts/manifests/v2.2.2/production_manifest_masterplan_v2_2_2.json';G=R/'InteractiveBook/TrainerContent/cases.json'
assert sha(M)=='c4f8600132a4099a655c31c4c97356c52265da7c0895e04d9a99f04503821e41';assert sha(G)=='2540570c2b907ea0e48cb9752e715486126e006a6100bd27e2f9f170d2c99689'
assert all(sha(R/p)==v for p,v in read(P/'authoring-input-hashes.json').items())
m=read(M);manifest={r['plannedId']:r for r in m['manifest'] if r['batch']=='Batch 03'};bank=read(P/'cases_TC076_TC100.json');cs=bank['cases'];gold=read(G)['cases'];by={c['id']:c for c in cs}
assert len(cs)==25 and list(by)==[f'TC-{n:03}' for n in range(76,101)];assert len(gold)==75
for c in cs:
 r=manifest[c['id']]
 for k in ['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']:assert c[k]==r[k],(c['id'],k)
 assert c['decisiveMutation']==r['decisiveMutationConcept']
 assert [o['id'] for o in c['options']]==list('ABCD')
 assert sum(o['isBest'] for o in c['options'])==1 and sum(o['decisionQuality']==1 for o in c['options'])==1
 assert all(o['isBest']==(o['decisionQuality']==1) and 0<=o['decisionQuality']<=1 for o in c['options'])
 assert 1<=len(c['decisiveFacts'])<=3
 assert c['trainingEligible'] and c['assessmentEligible']==(c['scenarioFamilyId'] is None)
positions=dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in cs).items()));assert positions==dict(A=6,B=6,C=6,D=7)
levels=dict(collections.Counter(c['requiredLevel'] for c in cs));assert levels==dict(junior=5,middle=12,senior=5,head=3)
familyrows=[f for f in m['familyManifest'] if set(f['memberIds'])&set(by)];assert len(familyrows)==4
anchors={'F-DR-T01':'Предотвращаемая ручным ревью потеря за месяц — ','F-TD-P01':'Продуктовый контракт положительного ответа: ','F-PE-P01':'О причинах известно следующее: ','F-BV-P02':'Приведённый будущий поток текущей инициативы в каждом из двух отчётов — '}
expected={'F-DR-T01':['C','A','D'],'F-TD-P01':['B','C'],'F-PE-P01':['D','A'],'F-BV-P02':['B','D']};familychecks=[]
for f in familyrows:
 members=[by[id] for id in f['memberIds']];anchor=anchors[f['scenarioFamilyId']];bases=[c['context'].split(anchor)[0] for c in members];assert len(set(bases))==1
 assert all(c['context'].count(anchor)==1 for c in members);assert len({c['question'] for c in members})==1
 assert all([o['text'] for o in c['options']]==[o['text'] for o in members[0]['options']] for c in members)
 keys=[next(o['id'] for o in c['options'] if o['isBest']) for c in members];assert keys==expected[f['scenarioFamilyId']]
 diffs=[]
 for c in members[1:]:
  a=members[0]['context'];b=c['context'];matcher=difflib.SequenceMatcher(None,a,b,autojunk=False)
  diffs.append(dict(a=members[0]['id'],b=c['id'],literalChanges=[dict(before=a[i:j],after=b[k:l]) for op,i,j,k,l in matcher.get_opcodes() if op!='equal']))
 familychecks.append(dict(familyId=f['scenarioFamilyId'],members=f['memberIds'],contract=f,identicalBaseContext=True,identicalQuestion=True,identicalOptionsAndOrder=True,singleVariableValues={c['id']:c['context'].split(anchor)[1] for c in members},strongestKeys=keys,literalDiffs=diffs,status='PASS'))
familychecks[0]['numericalProof']={'L0':{'A':-2,'B':-7,'C':0,'D':-6},'L6':{'A':1,'B':-1,'C':0,'D':0},'L18':{'A':7,'B':11,'C':0,'D':12},'effectiveBoundaries':[4,8],'fourthStrategy':'B repeats the reliable study at a cost of 1; no new information expected. Always worse than keeping the same manual regime without redundant study.'}
familychecks[-1]['numericalProof']={'TC083':'Deduplicate the two views: PV16..20 - remaining8 = NPV8..12 > alternative5.','TC084':'PV4..7 - remaining8 = NPV-4..-1 < alternative5.','commonSeniorReasoning':'Existing model doubles the same customers and includes sunk cost; waiting cannot resolve future market uncertainty. Correct accounting and comparison across an interval, not rote choice by one NPV sign.'}
write('family-diff-analysis.json',familychecks)
# Actual production load, including sibling topics catalog.
assert sha(P/'topics.json')==sha(R/'InteractiveBook/TrainerContent/topics.json')
v=subprocess.run(['/private/tmp/batch03-validator',str(P/'cases_TC076_TC100.json')],capture_output=True,text=True,check=True);(P/'schema-validation.log').write_text(v.stdout)
# The same independent-QA 78 rules: no execution of its mutation/report-writing portions.
s=(R/'agent-artifacts/qa/batch-02/reproduce-independent-checks.py').read_text();ns=dict(re=re,collections=collections,statistics=statistics,itertools=itertools,random=random);exec(s[s.index('def tokens(s)'):s.index('feats=')],ns);ns['basic']=ns['feat'];exec(s[s.index('\ndef feat(t):'):s.index('\ncorpora=')],ns)
x={name:ns['scan'](group) for name,group in [('batch03',cs),('production75',gold),('combined100',gold+cs)]}
single=lambda v:max(r['firstTieHits'] for r in v['rules'] if len(r['rule'])==1)
# Rates, not absolute hit counts, because comparison pools have different sizes.
surface=dict(method='Same independent-QA feature extractor: 38 min/max and 40 lexical two-feature rules, fixed family-preserving permutation. Rule selection is exploratory, not out-of-sample validation.',results=x,batchBestCombined=x['batch03']['bestFirstTieHits'],batchBestSingle=single(x['batch03']),batchBestExpectedTieHits=x['batch03']['bestRandomTieExpectedHits'],productionBestRate=x['production75']['bestFirstTieHits']/75,combinedBestRate=x['combined100']['bestFirstTieHits']/100,features='words, chars, punctuation, clauses, actions proxy, numbers, Latin technical fragments, condition/order markers, and, specificity proxy',limitations='Morphology/terminology and action counts are proxies. Passing these rules is not proof against every possible cue.')
write('surface-leakage-analysis.json',surface)
write('batch-statistics.json',dict(caseCount=25,standalone=sum(c['scenarioFamilyId'] is None for c in cs),linked=sum(c['scenarioFamilyId'] is not None for c in cs),families=4,pairs=3,triplets=1,levels=levels,correctPositions=positions,bestSimpleSurfaceHeuristic=surface['batchBestCombined'],bestSingleHeuristic=surface['batchBestSingle'],combined100Best= x['combined100']['bestFirstTieHits'],production75Best=x['production75']['bestFirstTieHits'],candidateSHA256=sha(P/'cases_TC076_TC100.json')))
print(json.dumps(dict(schema='PASS',runtime='PASS',families='4/4',positions=positions,levels=levels,bestCombined=surface['batchBestCombined'],bestSingle=surface['batchBestSingle'],expectedTies=surface['batchBestExpectedTieHits'],production75= x['production75']['bestFirstTieHits'],combined100=x['combined100']['bestFirstTieHits']),ensure_ascii=False,indent=2))
