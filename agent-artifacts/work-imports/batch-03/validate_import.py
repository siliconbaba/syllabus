import collections, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=read(HERE/'cases-before-import.json'); bankpath=ROOT/'InteractiveBook/TrainerContent/cases.json'; bank=read(bankpath)
batchpath=ROOT/'agent-artifacts/test-bank/batch-03-r3/cases_TC076_TC100_r3.json';batch=read(batchpath)
assert {k:v for k,v in before.items() if k!='cases'}=={k:v for k,v in bank.items() if k!='cases'}
rows=bank['cases']; assert len(rows)==100 and [r['id'] for r in rows]==[f'TC-{i:03}' for i in range(1,101)]
assert rows[75:]==batch['cases'], 'Batch content/order changed'
assert before['cases']==rows[:75], 'Existing production cases changed'
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
manifest=read(ROOT/'agent-artifacts/manifests/v2.2.3/production_manifest_masterplan_v2_2_3.json')
planned={r['plannedId']:r for r in manifest['manifest']}
newfamilies={r['scenarioFamilyId'] for r in rows[75:] if r.get('scenarioFamilyId')}
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
levels=dict(collections.Counter(r['requiredLevel'] for r in rows));assert levels=={'junior':16,'middle':53,'senior':21,'head':10}
stats={'caseCount':100,'standaloneCount':sum(not r.get('scenarioFamilyId') for r in rows),'linkedCount':sum(bool(r.get('scenarioFamilyId')) for r in rows),'trainingEligibleCount':sum(r['trainingEligible'] for r in rows),'assessmentEligibleCount':sum(r['assessmentEligible'] for r in rows),'levels':levels,'familyCount':len(families),'newFamilyCount':len(newfamilies),'families':{k:[r['id'] for r in v] for k,v in families.items()},'manifestFamilyPositions':family_positions,'positionNote':'Production schema has no familyPosition field; positions validated against authoritative manifest v2.2.3, not imported as auxiliary metadata. Gold families validated by membership/topic/distinct mutations.','correctPositionDistributionBatch03':dict(sorted(collections.Counter(o['id'] for r in rows[75:] for o in r['options'] if o['isBest']).items())),'sha256':sha(bankpath),'candidateSha256':sha(batchpath),'existingProductionRegression':'PASS','authoritativeManifest':'v2.2.3','batchExactSemanticEquality':'PASS'}
assert (stats['standaloneCount'],stats['linkedCount'],stats['trainingEligibleCount'],stats['assessmentEligibleCount'],stats['familyCount'])==(67,33,100,67,15)
# Freeze metadata to the approved v2.2.3 blueprint, without content re-review.
for r in rows[75:]:
    plan=planned[r['id']]
    for k in ['topicId','partId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']:
        assert r.get(k)==plan.get(k),(r['id'],k)
hotfix=next(r for r in rows if r['id']=='TC-085');plan=planned['TC-085']
assert (hotfix['topicId'],hotfix['domain'],hotfix['requiredLevel'])==('t-3-9','release_and_quality','middle')
assert [o['id'] for o in hotfix['options'] if o['isBest']]==['C']
assert hotfix['primaryPattern']=='process-economics' and hotfix['secondaryPatterns']==['bottleneck']
# Decisive facts are authored text, preserved by exact r3 equality; blueprint metadata checked above.
assert stats['correctPositionDistributionBatch03']=={'A':6,'B':6,'C':6,'D':7}
assert dict(collections.Counter(r['requiredLevel'] for r in rows[75:]))=={'junior':5,'middle':12,'senior':5,'head':3}
assert len(families['F-DR-T01'])==3
stats['tc085HotfixIntegrity']='PASS'
evidence={'existingCaseIds':[r['id'] for r in rows[:75]],'candidateCaseIds':[r['id'] for r in rows[75:]],'unexpectedExistingCaseChanges':[],'candidateDifferences':[],'rootMetadataUnchanged':True,'optionOrderPreserved':True,'tc085EqualsR3':hotfix==next(r for r in batch['cases'] if r['id']=='TC-085'),'tc085ManifestMetadataMatches':True,'beforeSha256':sha(HERE/'cases-before-import.json'),'afterSha256':sha(bankpath),'candidateSha256':sha(batchpath),'manifestSha256':sha(ROOT/'agent-artifacts/manifests/v2.2.3/production_manifest_masterplan_v2_2_3.json')}
# Byte-level old-object preservation: entire old prefix (through last old object) remains unchanged.
oldbytes=(HERE/'cases-before-import.json').read_bytes(); prefix=oldbytes[:-len(b'\n  ]\n}\n')]
assert bankpath.read_bytes().startswith(prefix+b',\n')
evidence['oldObjectFormattingPreserved']=True
evidence['existingCaseCount']=75
(HERE/'regression-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
(HERE/'production-bank-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False,indent=2))
