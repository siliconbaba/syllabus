import collections, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=read(HERE/'cases-before-import.json'); bankpath=ROOT/'InteractiveBook/TrainerContent/cases.json'; bank=read(bankpath)
batchpath=ROOT/'agent-artifacts/test-bank/batch-01-r2/cases_TC026_TC050_r2.json';batch=read(batchpath)
assert {k:v for k,v in before.items() if k!='cases'}=={k:v for k,v in bank.items() if k!='cases'}
rows=bank['cases']; assert len(rows)==50 and [r['id'] for r in rows]==[f'TC-{i:03}' for i in range(1,51)]
assert rows[25:]==batch['cases'], 'Batch content/order changed'
linked_gold={'TC-001','TC-002','TC-003','TC-004','TC-017','TC-018'}
for a,b in zip(before['cases'],rows[:25]):
 expected=dict(a)
 if a['id'] in linked_gold:assert a['assessmentEligible'] is True;expected['assessmentEligible']=False
 assert expected==b, f'Gold regression: {a["id"]}'
casekeys={'id','revision','type','partId','topicId','title','sourceTopicExplanation','trainingEligible','assessmentEligible','domain','requiredLevel','primaryPattern','secondaryPatterns','context','question','options','keyInsight','mentalModel','decisiveFacts','scenarioFamilyId','decisiveMutation','authorRationale'}
optionkeys={'id','text','decisionQuality','isBest','reasoningPattern','failurePattern','explanation','whyTempting','whyNotBest','whenItWouldBeBest'}
families=collections.defaultdict(list)
for r in rows:
 assert not(set(r)-casekeys)
 assert len(r['options'])==4 and {o['id'] for o in r['options']}==set('ABCD')
 assert sum(o['isBest'] for o in r['options'])==1
 for o in r['options']:
  assert not(set(o)-optionkeys)
  assert 0<=o['decisionQuality']<=1 and (o['decisionQuality']==1)==o['isBest']
 assert r['trainingEligible'] is True
 assert r['assessmentEligible']==(r.get('scenarioFamilyId') is None)
 if r.get('scenarioFamilyId'):families[r['scenarioFamilyId']].append(r)
for family,members in families.items():
 assert len(members)>=2
 assert len({c['topicId'] for c in members})==1
 assert len({c['decisiveMutation'] for c in members})==len(members)
manifest=read(ROOT/'agent-artifacts/manifests/v2.2/production_manifest_masterplan_v2_2.json')
planned={r['plannedId']:r for r in manifest['manifest']}
newfamilies={r['scenarioFamilyId'] for r in rows[25:] if r.get('scenarioFamilyId')}
assert len(newfamilies)==4
family_positions={}
for family in newfamilies:
 members=families[family]; contract=next(f for f in manifest['familyManifest'] if f['scenarioFamilyId']==family)
 assert {r['id'] for r in members}==set(contract['memberIds'])
 positions=[planned[r['id']]['familyPosition'] for r in members]
 assert len(set(positions))==len(positions)
 assert set(positions)==set(range(1,len(members)+1))
 assert len(members)==(2 if contract['type']=='pair' else 3)
 family_positions[family]={r['id']:planned[r['id']]['familyPosition'] for r in members}
levels=dict(collections.Counter(r['requiredLevel'] for r in rows));assert levels=={'junior':6,'middle':30,'senior':10,'head':4}
stats={'caseCount':50,'standaloneCount':sum(not r.get('scenarioFamilyId') for r in rows),'linkedCount':sum(bool(r.get('scenarioFamilyId')) for r in rows),'trainingEligibleCount':sum(r['trainingEligible'] for r in rows),'assessmentEligibleCount':sum(r['assessmentEligible'] for r in rows),'levels':levels,'familyCount':len(families),'newFamilyCount':len(newfamilies),'families':{k:[r['id'] for r in v] for k,v in families.items()},'manifestFamilyPositions':family_positions,'positionNote':'Production schema has no familyPosition field; positions validated against authoritative manifest v2.2, not imported as auxiliary metadata. Gold families validated by membership/topic/distinct mutations.','correctPositionDistributionBatch01':dict(sorted(collections.Counter(o['id'] for r in rows[25:] for o in r['options'] if o['isBest']).items())),'sha256':sha(bankpath),'candidateSha256':sha(batchpath),'goldRegression':'PASS','batchExactSemanticEquality':'PASS'}
assert (stats['standaloneCount'],stats['linkedCount'],stats['trainingEligibleCount'],stats['assessmentEligibleCount'],stats['familyCount'])==(35,15,50,35,7)
(HERE/'production-bank-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False,indent=2))
