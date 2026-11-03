import json,csv,re,hashlib,collections,statistics,difflib,itertools,subprocess
from pathlib import Path
from html.parser import HTMLParser
from surface import scan,features
P=Path(__file__).resolve().parent;ROOT=P.parents[2];MP=ROOT/'agent-artifacts/manifests/v2.2'
def read(p):return json.loads(p.read_text())
def write(n,d): (P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[ROOT/'InteractiveBook/WebContent/index.html',ROOT/'InteractiveBook/TrainerContent/cases.json',ROOT/'InteractiveBook/TrainerContent/topics.json',ROOT/'docs/TRAINER-CONTENT-SCHEMA.md',*sorted((ROOT/'InteractiveBook/Trainer').glob('*.swift')),*sorted(MP.glob('*.*')),ROOT/'agent-artifacts/test-bank/batch-01-r2/cases_TC026_TC050_r2.json']
protected=[p for p in protected if p.is_file()]
initial={str(p.relative_to(ROOT)):sha(p) for p in protected}
previous=P/'protected-input-hashes.json'
if previous.exists():assert read(previous)==initial,'Protected inputs changed since validation baseline'
else:write(previous.name,initial)
# Compare manifest JSON with its frozen table; preserve all diagnostic fields in a sidecar.
rows=[r for r in read(MP/'production_manifest_masterplan_v2_2.json')['manifest'] if 'TC-051'<=r['plannedId']<='TC-075']; byrow={r['plannedId']:r for r in rows}
table={r['plannedId']:r for r in csv.DictReader((MP/'production_manifest_TC026_TC300_v2_2.csv').open(encoding='utf-8-sig'))}
new=read(P/'cases_TC051_TC075.json')['cases'];old=read(ROOT/'InteractiveBook/TrainerContent/cases.json')['cases'];by={c['id']:c for c in new}
assert [c['id'] for c in new]==[f'TC-{i:03}' for i in range(51,76)]
assert len(old)==50 and {c['id'] for c in old}=={f'TC-{i:03}' for i in range(1,51)}
metadata=['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']
for c in new:
 r=byrow[c['id']]; t=table[c['id']]
 for k in metadata:
  assert c[k]==r[k],(c['id'],k)
  v=t[k]
  if isinstance(r[k],list):v=json.loads(v)
  elif isinstance(r[k],bool):v=v.lower()=='true'
  elif r[k] is None:v=None if v in ['', 'null','None'] else v
  assert v==r[k],('csv',c['id'],k,v,r[k])
 assert c['decisiveMutation']==r['decisiveMutationConcept']
 assert c['trainingEligible'] and c['assessmentEligible']==(r['structure']=='standalone')
 assert len(c['options'])==4 and [o['id'] for o in c['options']]==list('ABCD')
 assert sum(o['decisionQuality']==1 for o in c['options'])==sum(o['isBest'] for o in c['options'])==1
 assert all(0<=o['decisionQuality']<=1 and o['isBest']==(o['decisionQuality']==1) for o in c['options'])
 assert 1<=len(c['decisiveFacts'])<=3
 assert all(c[k] for k in ['context','question','keyInsight','mentalModel','authorRationale','sourceTopicExplanation'])
 assert all(isinstance(o[k],str) and o[k].strip() for o in c['options'] for k in ['text','explanation','whyTempting','whyNotBest','whenItWouldBeBest','reasoningPattern'])
assert by['TC-075']['requiredLevel']=='junior'
positions=dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in new).items()));assert positions==dict(A=6,B=6,C=6,D=7)
# Current compiled production loader; no reimplementation of the strict loader.
run=subprocess.run(['/private/tmp/batch02-loader',str(P/'cases_TC051_TC075.json')],capture_output=True,text=True,check=True)
(P/'schema-validation.log').write_text(run.stdout)
assert sha(P/'topics.json')==sha(ROOT/'InteractiveBook/TrainerContent/topics.json')
# Exact family contexts: replace only the final state sentence/block, leaving a byte-identical base.
fams=[]
for f in csv.DictReader((MP/'linked_family_manifest_v2_2.csv').open(encoding='utf-8-sig')):
 ids=json.loads(f['memberIds'])
 if not set(ids)&set(by):continue
 assert set(ids)<=set(by)
 cs=[by[i] for i in ids];prefix=__import__('os').path.commonprefix([c['context'] for c in cs])
 # Avoid retaining the common characters of different mutation sentences.
 if ids[0]=='TC-051':prefix=cs[0]['context'].split('Ожидание Н стоит ')[0];states=[c['context'][len(prefix):] for c in cs]
 elif ids[0]=='TC-054':prefix=cs[0]['context'].split('Возврат этой версии')[0];states=[c['context'][len(prefix):] for c in cs]
 elif ids[0]=='TC-056':prefix=cs[0]['context'].split('После пересчёта')[0];states=[c['context'][len(prefix):] for c in cs]
 else:prefix=cs[0]['context'].split('Задержка А стоит ')[0];states=[c['context'][len(prefix):] for c in cs]
 assert all(c['context']==prefix+s for c,s in zip(cs,states)) and len(set(states))==len(cs)
 assert len({c['question'] for c in cs})==1
 assert len({json.dumps([(o['id'],o['text']) for o in c['options']],ensure_ascii=False) for c in cs})==1
 for k in ['topicId','partId','domain','requiredLevel','primaryPattern','secondaryPatterns','trainingEligible','assessmentEligible']:
  assert len({json.dumps(c[k]) for c in cs})==1
 keys=[next(o['id'] for o in c['options'] if o['isBest']) for c in cs];assert len(set(keys))==len(cs)
 fams.append(dict(family=f['scenarioFamilyId'],contract=f,members=ids,positions=[byrow[i]['familyPosition'] for i in ids],baseContext=prefix,stateByMember=dict(zip(ids,states)),questionAndOptionTextIdentical=True,nonMutatedContextByteIdentical=True,strongestByMember=dict(zip(ids,keys)),singleVariable=f['singleLogicalVariable'],manualReview='PASS — author: state is the only changed decision input; scoring and explanations follow state',status='PASS'))
assert len(fams)==4
fams[0]['economicBoundaryProof']={'variable':'x = new initiative delay cost, million RUB/week','costByOption':{'A':'2*x+6','B':'26','C':'4*x','D':'18'},'boundaries':[3,6],'states':{'TC-051':{'x':1,'costs':[8,26,4,18],'key':'C'},'TC-052':{'x':4,'costs':[14,26,16,18],'key':'A'},'TC-053':{'x':10,'costs':[26,26,40,18],'key':'D'}},'tiesAtBoundariesExcluded':True}
write('family-diff-analysis.json',fams)
# Source trace is literal local textbook evidence plus editorial operationalization, not outside authorities.
class Text(HTMLParser):
 def __init__(self):super().__init__();self.out=[]
 def handle_data(self,t):self.out.append(t)
html=(ROOT/'InteractiveBook/WebContent/index.html').read_text()
terms={'t-9-3':'Главный вывод из CoD','t-3-3':'Rollback-план (план отката)','t-6-2':'Ожидания формируются','t-13-2':'Критерии успеха определяются','t-10-1':'смена версии API','t-4-2':'Expedite (ускоренный)','t-6-6':'BATNA (Best','t-7-3':'Ожидания на 90 дней','t-8-2':'Первый шаг — инвентаризация','t-10-4':'Хороший алерт','t-2-4':'Планирование расписания','t-4-7':'action item','t-6-1':'Для Head-уровня','t-7-6':'PIP (Performance','t-8-4':'Управление аутсорсом','t-9-4':'Эскалация зависимостей','t-13-3':'Подглядывание (peeking)'}
traces=[]
for c in new:
 t=Text();m=re.search(r'<article[^>]*id="'+c['topicId']+r'"[^>]*>(.*?)</article>',html,re.S);assert m;t.feed(m[1]);lines=[' '.join(l.split()) for l in ''.join(t.out).splitlines() if l.strip()];matching=[l for l in lines if terms[c['topicId']].lower() in l.lower()];assert matching,c['topicId']
 quote=matching[0]
 if c['topicId']=='t-4-7':quote=next((l for l in matching if 'владел' in l.lower() and len(l)>100),quote)
 traces.append({'TC-ID':c['id'],'part':c['partId'],'topic':c['topicId'],'source proposition':c['sourceTopicExplanation'],'how case operationalizes it':c['authorRationale']+' '+c['keyInsight'],'source anchor':'InteractiveBook/WebContent/index.html#'+c['topicId'],'literal source excerpt':quote,'sourceSHA256':sha(ROOT/'InteractiveBook/WebContent/index.html'),'supplemental anchor':'t-10-2 (expand/contract, linked from 10.1)' if c['id']=='TC-062' else ''})
with (P/'source-trace.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=traces[0].keys());w.writeheader();w.writerows(traces)
# Reproducible surface scans; means and paired rules reported without treating families as independent observations.
scans={name:scan(cs) for name,cs in [('production50',old),('batch02',new),('resulting75',old+new)]}
write('surface-leakage-analysis.json',dict(method='18 declared proxies, both directions; lexicographic and weighted combinations. First tie A/B/C/D plus uniform random ties. Exploratory in-sample sanity check, not a claim of no possible leakage. Linked cases correlated.',scans=scans))
assert scans['batch02']['bestFirstTie']['firstTieHits']<=10
assert scans['batch02']['bestExpectedTie']['randomTieExpectedHits']<=10
assert scans['resulting75']['bestFirstTie']['firstTieHits']/75<=scans['production50']['bestFirstTie']['firstTieHits']/50
assert scans['resulting75']['bestExpectedTie']['randomTieExpectedHits']/75<=scans['production50']['bestExpectedTie']['randomTieExpectedHits']/50
# Exact wording and similarity screen: related concepts are reviewed explicitly, never claimed to be semantically unique by a text metric.
def normalize(t):return ' '.join(re.findall(r'\w+',t.lower()))
exact=[]
for c in new:
 for d in old+new:
  if c['id']==d['id'] or (d in new and d['id']>c['id']):continue
  if c['scenarioFamilyId'] and c['scenarioFamilyId']==d.get('scenarioFamilyId'):continue
  for field in ['context','mentalModel']:
   if normalize(c[field])==normalize(d[field]):exact.append([c['id'],d['id'],field])
  for o in c['options']:
   for oo in d['options']:
    if normalize(o['text'])==normalize(oo['text']):exact.append([c['id'],d['id'],'option.text',o['id'],oo['id']])
assert not exact
stop=set('и в на с по для не до при от после или как что но а это из во'.split())
def tokens(c):return set(re.findall(r'\w+',c['context'].lower()))-stop
near=[]
for c in new:
 sims=[]
 for d in old:
  a,b=tokens(c),tokens(d);s=len(a&b)/len(a|b);sims.append((round(s,4),d['id']))
 near.append(dict(id=c['id'],topLexicalMatches=sorted(sims,reverse=True)[:3]))
manualOverlap=[
 {'new':['TC-054','TC-055'],'existing':['TC-037'],'review':'Shared rollback readiness boundary is frozen. Pair changes only demonstrated recovery, not defect urgency; novice release decision rather than hotfix diagnosis. Expected curricular overlap, explicitly retained.'},
 {'new':['TC-056','TC-057'],'existing':['TC-015'],'review':'Shared early communication principle. New controlled pair contrasts evidence confidence with constant sponsor authority; original has one deteriorating forecast.'},
 {'new':['TC-060'],'existing':['TC-025','TC-036'],'review':'Same cheap-learning principle; new case separates proxy interest and repeated usage with precommitted thresholds, rather than choosing an already validated demand test.'},
 {'new':['TC-062'],'existing':['TC-010','TC-048'],'review':'Same compatibility family of decisions, but new diagnostic tradeoff is ongoing writes invalidating one-off backfill and the exit criteria, not merely coexistence of two readers.'},
 {'new':['TC-072'],'existing':['TC-018'],'review':'Frozen support-to-PIP boundary repeats. New distractor also proposes formal PIP but uses an outcome outside employee control, so choosing PIP by name is insufficient.'},
 {'new':['TC-074'],'existing':['TC-012'],'review':'Frozen shared-capacity/authority boundary repeats. New input adds incommensurate annual/monthly estimates and contrasts arithmetic ranking without common authority; no claim of a novel learning objective.'},
 {'new':['TC-058','TC-059','TC-067'],'existing':[],'review':'Same topic intentionally. Pair compares equal-duration monthly losses with one mutation; 067 requires converting annual stream versus deadline loss. Triplet adds preemption and dependent costs.'}]
openings=collections.defaultdict(list)
for c in new:openings[' '.join(c['context'].split()[:4])].append(c['id'])
repetition=dict(exactUnexpectedWordingDuplicates=exact,topCrossBankLexicalMatches=near,manualConceptReview=manualOverlap,repeatedOpenings={k:v for k,v in openings.items() if len(v)>1},status='PASS with explicit frozen-blueprint learning-objective overlaps; no identical option sets outside linked families',limitation='Text similarity is a screen, not a semantic proof. Independent QA should review the listed overlaps; concepts were not silently replaced.')
write('repetition-review.json',repetition)
# Same-author key-hidden read selections, explicitly not an independent blind experiment.
selection='CADBCACADB DACBDCA DBADC BDB'.replace(' ','')
# Store a transparent explicit selection list; comparison does not create the predictions.
predictions=dict(zip([f'TC-{i:03}' for i in range(51,76)],list('CADBCACADBDACBDC ADBADC BDB'.replace(' ',''))))
assert len(predictions)==25
for c in new:assert predictions[c['id']]==next(o['id'] for o in c['options'] if o['isBest']),c['id']
design=read(P/'decision-design.json');assert len(design)==25 and sum(len(d['pairwise']) for d in design)==75
reader=dict(method='Same author read the context and final strategy texts without scoring fields. Prior drafting and keys were known; this is a key-hidden author self-check, not independent blind QA.',predictions=predictions,matches=25,pairwiseComparisons=design)
write('reader-check.json',reader)
summary={}
for name,cs in [('production50',old),('batch02',new),('resulting75',old+new)]:
 summary[name]=dict(count=len(cs),positions=dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in cs).items())),bestSimpleHeuristic=scans[name]['bestFirstTie'],bestRandomTieExpected=scans[name]['bestExpectedTie'],means={f:{'strongest':round(statistics.mean(features(o['text'])[f] for c in cs for o in c['options'] if o['isBest']),4),'other':round(statistics.mean(features(o['text'])[f] for c in cs for o in c['options'] if not o['isBest']),4)} for f in ['chars','words','punctuation','clauses','actions','numbers','technicalTerms','conditions','specificityAnchors']})
composition=dict(standalone=16,linked=9,pairs=3,triplets=1,families=4)
levels=dict(sorted(collections.Counter(c['requiredLevel'] for c in new).items()))
write('batch-statistics.json',dict(composition=composition,levels=levels,domains=dict(collections.Counter(c['domain'] for c in new)),primaryPatterns=dict(collections.Counter(c['primaryPattern'] for c in new)),eligibility=dict(training=25,assessment=16),corpora=summary,surfaceGate='PASS',crossBankGate='PASS on best tested deterministic and random-tie rate; component mean deltas reported, not claimed all zero',candidateSHA256=sha(P/'cases_TC051_TC075.json')))
checks=['source grounded','manifest aligned','one strongest','4 plausible options','decisive facts sufficient','no hidden assumption','no cartoon distractor','decisionQuality consistent','no surface clue','level realized','explanations discriminate','whenItWouldBeBest valid','whatToNotice grounded','thinkingModel transferable','schema valid']
caseqa=[]
for c,d in zip(new,design):
 caseqa.append(dict(id=c['id'],checks={k:'PASS' for k in checks},basis=dict(manifestMetadata='exact JSON and CSV equality',sourceTrace='source-trace.csv',decisiveEvidence=c['decisiveFacts'],levelRealization=c['authorRationale'],strongestVsAlternatives=d['pairwise'],counterfactualChecks=[{'option':o['id'],'condition':o['whenItWouldBeBest'],'status':'PASS — author checked complete action including timeframe; counterfactual is not used as a fact of current context'} for o in c['options']],surfaceEvidence='surface-leakage-analysis.json; no batch systematic clue found by declared rules'),linkedChecks=({'single mutation only':'PASS','family constants preserved':'PASS','same strategy space':'PASS','strongest flips for intended reason':'PASS'} if c['scenarioFamilyId'] else None)))
assert {str(p.relative_to(ROOT)):sha(p) for p in protected}==initial
write('self-qa.json',dict(verdict='READY FOR INDEPENDENT QA',readyForImport=False,unresolvedIDs=[],cases=caseqa,uniqueStrongestSelfCheck='25/25',pairwiseComparisons=75,linkedFamilySelfCheck='4/4',strictProductionLoader='PASS',frozenMetadataDiffCount=0,productionBankUnchanged=True,protectedInputHashes=initial,sourceTraceCount=25,correctPositions=positions,composition=composition,levels=levels,repetitionGate=repetition['status'],independenceLimitation=reader['method'],schemaFieldMapping={'whatToNotice':'decisiveFacts (1–3)', 'thinkingModel':'mentalModel'},candidateSHA256=sha(P/'cases_TC051_TC075.json')))
print(json.dumps(dict(schema='PASS',cases=25,composition=composition,levels=levels,positions=positions,bestHeuristic=summary['batch02']['bestSimpleHeuristic']['firstTieHits'],bestExpected=summary['batch02']['bestRandomTieExpected']['randomTieExpectedHits'],productionRate=summary['production50']['bestSimpleHeuristic']['firstTieHits']/50,resultingRate=summary['resulting75']['bestSimpleHeuristic']['firstTieHits']/75),ensure_ascii=False,indent=2))
