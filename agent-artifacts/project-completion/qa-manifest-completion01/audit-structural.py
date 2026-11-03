from pathlib import Path
import json,hashlib,collections,csv,math
root=Path.cwd();c=Path('agent-artifacts/manifests/v2.3-completion-01-candidate');o=Path('agent-artifacts/project-completion/qa-manifest-completion01');bpath=Path('agent-artifacts/manifests/v2.3-hardtail-b2-candidate/production_manifest_masterplan_v2_3_hardtail_b2_candidate.json');base=json.loads(bpath.read_text());candidate=json.loads((c/'production_manifest_masterplan_v2_3_completion_01_candidate.json').read_text());prod=json.loads(Path('InteractiveBook/TrainerContent/cases.json').read_text());bqa=json.loads(Path('agent-artifacts/qa/manifest-v2.3-hardtail-b2/QA-verdict.json').read_text())
for p,h in json.loads((c/'input-hashes.json').read_text()).items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
for p,h in json.loads((c/'artifact-hashes.json').read_text()).items():assert hashlib.sha256((c/p).read_bytes()).hexdigest()==h,p
br=base['manifest'];cr=candidate['manifest'];assert len(br)==len(cr)==275
assert [x['plannedId'] for x in br]==[x['plannedId'] for x in cr]
assert len(set(x['plannedId'] for x in cr))==275
changed=[a['plannedId'] for a,b in zip(br,cr) if a!=b];assert changed==['TC-193','TC-200']
for n in [193,200]:
 p=Path(f'agent-artifacts/test-bank/reconstruction/tc{n}-r2/proposed-manifest-row.json');q=json.loads(Path(f'agent-artifacts/project-completion/qa-tc{n}-r2/QA-verdict.json').read_text());assert q['candidateSHA256']==hashlib.sha256(p.read_bytes()).hexdigest() and q['candidateAccepted'] and not q['importEligible'];assert next(x for x in cr if x['plannedId']==f'TC-{n}')==json.loads(p.read_text())
allowed={'manifest','manifestVersion','coverageSummary','completionRevision'};topchanges=[k for k in set(base)|set(candidate) if base.get(k)!=candidate.get(k)];assert set(topchanges)==allowed,topchanges
assert candidate['familyManifest']==base['familyManifest'] and len(candidate['familyManifest'])==43
assert candidate['headAudit']==base['headAudit']
protected=['plannedId','batch','partId','topicId','domain','requiredLevel','structure','scenarioFamilyId','familyPosition','decisiveMutationConcept','trainingEligible','assessmentEligible']
assert all(all(a.get(k)==b.get(k) for k in protected) for a,b in zip(br,cr))
assert collections.Counter(x['requiredLevel'] for x in cr)=={'junior':42,'middle':122,'senior':76,'head':35}
assert set(collections.Counter(x['batch'] for x in cr).values())=={25};assert len(set(x['batch'] for x in cr))==11
assert sum(x['structure']=='standalone' for x in cr)==181
for r in cr:assert r['trainingEligible'] is True and r['assessmentEligible'] is (r['structure']=='standalone')
remaining=candidate['completionRevision']['remainingUnresolvedIDs'];assert len(remaining)==len(set(remaining))==70 and set(remaining)==set(bqa['remainingUnresolvedIDs'])-{'TC-193','TC-200'}
assert not candidate['completionRevision']['readyToFreeze'] and not candidate['completionRevision']['importEligible']
# CSV must be exact flattened final rows, never the working draft or former baseline.
def verify_csv(path,rows):
 with path.open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
 assert len(actual)==len(rows)
 for a,b in zip(actual,rows):
  expected={k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,bool)) else '' if v is None else str(v) for k,v in b.items()}
  for k in a:assert a[k]==expected.get(k,''),(path,k,a[k],expected.get(k))
verify_csv(c/'production_manifest_TC026_TC300_v2_3_completion_01_candidate.csv',cr)
verify_csv(c/'linked_family_manifest_v2_3_completion_01_candidate.csv',candidate['familyManifest'])
assert (c/'head_audit_v2_3_completion_01_candidate.csv').read_bytes()==next(bpath.parent.glob('head_audit*.csv')).read_bytes()
ri=json.loads((c/'runtime-input.json').read_text());expected=[{k:r[k] for k in ['id','domain','requiredLevel','primaryPattern','secondaryPatterns','assessmentEligible','trainingEligible']} for r in prod['cases'][:25]]+[{ 'id':r['plannedId'], **{k:r[k] for k in ['domain','requiredLevel','primaryPattern','secondaryPatterns','assessmentEligible','trainingEligible']}} for r in cr]
assert ri['rows']==expected and ri['assessmentIDs']==[r['id'] for r in expected if r['assessmentEligible']]
# Baseline actual-runtime input; author-provided outputs are not used for the before vector.
before=json.loads(json.dumps(ri));bm={r['plannedId']:r for r in br}
for r in before['rows']:
 if r['id'] in bm:
  for k in ['domain','requiredLevel','primaryPattern','secondaryPatterns','assessmentEligible','trainingEligible']:r[k]=bm[r['id']][k]
(o/'baseline-runtime-input.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
(o/'structural-evidence.json').write_text(json.dumps({'status':'PASS','inputAndArtifactHashes':'PASS','changedRows':changed,'unchangedRows':273,'topLevelChangedKeys':sorted(topchanges),'protectedFieldsUnchanged':protected,'familyObjectsUnchanged':43,'headAuditBytesUnchanged':True,'csvRowExactness':True,'levels':dict(collections.Counter(x['requiredLevel'] for x in cr)),'remainingUnresolvedBefore':72,'remainingUnresolvedAfter':70,'removedOnlyApprovedIDs':True,'productionSHA256':hashlib.sha256(Path('InteractiveBook/TrainerContent/cases.json').read_bytes()).hexdigest(),'frozenManifestSHA256':hashlib.sha256(Path('agent-artifacts/manifests/v2.2.3/production_manifest_masterplan_v2_2_3.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print('PASS exact273unchanged,2approvedrows,43families,CSV and runtime input consistency')
