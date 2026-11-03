from pathlib import Path
import json,hashlib,csv,collections
R=Path.cwd();C=Path('agent-artifacts/manifests/v2.3-completion-03-candidate');B=Path('agent-artifacts/manifests/v2.3-completion-02-candidate');O=Path('agent-artifacts/project-completion/qa-manifest-completion03');P=Path('agent-artifacts/test-bank/full-cases/pack-104-109-r3');Q=Path('agent-artifacts/project-completion/qa-pack104-109-r3')
r=lambda p:json.loads(p.read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=r(B/'production_manifest_masterplan_v2_3_completion_02_candidate.json');c=r(C/'production_manifest_masterplan_v2_3_completion_03_candidate.json')
for path,sha in r(C/'input-hashes.json').items():assert h(Path(path))==sha,path
assert r(Q/'QA-verdict.json')['candidateSHA256']==h(P/'cases.json')
qe=r(Q/'evidence.json')
for fn,sha in qe['r3Hashes'].items():assert h(P/fn)==sha,fn
assert h(Path('InteractiveBook/WebContent/index.html'))==qe['hashChecks']['InteractiveBook/WebContent/index.html']['actual']
rows=[(x,y) for x,y in zip(b['manifest'],c['manifest']) if x!=y];assert [y['plannedId'] for x,y in rows]==['TC-108','TC-109'];proposed={x['plannedId']:x for x in r(P/'proposed-blueprints.json')}
for x,y in rows:
 assert {k for k in set(x)|set(y) if x.get(k)!=y.get(k)}=={'decisiveFactsConcept'}
 assert x['decisiveFactsConcept'][:3]==y['decisiveFactsConcept'][:3]
 assert y==proposed[y['plannedId']]
fs=[(x,y) for x,y in zip(b['familyManifest'],c['familyManifest']) if x!=y];assert len(fs)==1
x,y=fs[0];assert y['scenarioFamilyId']=='F-PA-P02';assert {k for k in set(x)|set(y) if x.get(k)!=y.get(k)}=={'factsThatMustRemainConstant'}
assert y==next(f for f in r(P/'proposed-families.json') if f['scenarioFamilyId']=='F-PA-P02')
assert rows[0][1]['decisiveFactsConcept'][1:]==rows[1][1]['decisiveFactsConcept'][1:]
assert c['completionRevision']['remainingUnresolvedIDs']==b['completionRevision']['remainingUnresolvedIDs'] and len(c['completionRevision']['remainingUnresolvedIDs'])==68
assert len(c['manifest'])==275 and len({x['plannedId'] for x in c['manifest']})==275
assert len(c['familyManifest'])==43 and collections.Counter(len(x['memberIds']) for x in c['familyManifest'])=={2:35,3:8}
assert collections.Counter(x['requiredLevel'] for x in c['manifest'])=={'junior':42,'middle':122,'senior':76,'head':35}
assert collections.Counter(x['structure'] for x in c['manifest'])==collections.Counter(x['structure'] for x in b['manifest'])
assert c['headAudit']==b['headAudit']
fields=['domain','requiredLevel','primaryPattern','secondaryPatterns','assessmentEligible','trainingEligible']
project=lambda m:[{'id':x['plannedId'],**{k:x[k] for k in fields}} for x in m['manifest']]
assert project(c)==project(b)
ri=r(B/'runtime-input.json');gold=[{k:x[k] for k in ['id',*fields]} for x in r(Path('InteractiveBook/TrainerContent/cases.json'))['cases'][:25]];assert ri['rows']==gold+project(c)
inherit=r(C/'runtime-inheritance.json');assert h(Path(inherit['baselineCoverage']))==inherit['baselineCoverageSHA256']
priorinputs=r(B/'input-hashes.json')
for src in ['InteractiveBook/Trainer/TrainerScoringMapping.swift','InteractiveBook/Trainer/TrainerScoringEngine.swift','InteractiveBook/TrainerContent/cases.json']:assert h(Path(src))==priorinputs[src]
assert r(Path('agent-artifacts/project-completion/qa-manifest-completion02/QA-verdict.json'))['acceptedAsWorkingBase']
for path,expected in [(C/'production_manifest_TC026_TC300_v2_3_completion_03_candidate.csv',c['manifest']),(C/'linked_family_manifest_v2_3_completion_03_candidate.csv',c['familyManifest'])]:
 with path.open(encoding='utf-8-sig',newline='') as f: actual=list(csv.DictReader(f))
 assert len(actual)==len(expected)
 for a,e in zip(actual,expected):
  for k,v in a.items():
   x=e.get(k);want=json.dumps(x,ensure_ascii=False) if isinstance(x,(dict,list,bool)) else '' if x is None else str(x);assert v==want,(path,k)
source=c['coverageSummary']['source'];pointerOK=Path(source).is_file() and h(Path(source))==inherit['baselineCoverageSHA256']
e={'rowChanges':['TC-108','TC-109'],'changedFields':['decisiveFactsConcept[3]'],'unchangedRows':273,'changedFamily':'F-PA-P02','unchangedFamilies':42,'sourceContentQAPinned':True,'exactProposedContracts':True,'sharedMutationRemainsFrequencyOnly':True,'runtimeProjection300ExactlyEqual':True,'runtimeSourcesUnchanged':True,'sevenPoolCoverageInherited':True,'newRuntimeRuns':0,'remainingUnresolved':68,'headBreadth':'PASS inherited unchanged','csvExact':True,'coveragePointerValid':pointerOK,'topChangedKeys':[k for k in set(b)|set(c) if b.get(k)!=c.get(k)],'candidateSHA256':h(C/'production_manifest_masterplan_v2_3_completion_03_candidate.json')}
(O/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n');print(json.dumps(e,ensure_ascii=False,indent=2))
