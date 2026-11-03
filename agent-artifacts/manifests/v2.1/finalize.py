#!/usr/bin/env python3
"""Reproduce the technical pass from immutable v2 inputs and production Swift sources."""
import collections, copy, csv, hashlib, json, os, pathlib, shutil, subprocess
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def read(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name, obj): (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
def csvwrite(name, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list,dict,bool)) else v for k,v in r.items()})
def counts(rows, key): return dict(sorted(collections.Counter(r[key] for r in rows).items()))
original = read(HERE/'inputs/production_manifest_masterplan_v2.json')
master = copy.deepcopy(original)
rows = master['manifest']; families = master['familyManifest']
assert len(rows) == 275 and {r['plannedId'] for r in rows} == {f'TC-{i:03}' for i in range(26,301)}
assert counts(rows,'structure') == {'pair':70,'standalone':181,'triplet':24}
assert counts(families,'type') == {'pair':35,'triplet':8}
assert counts(rows,'requiredLevel') == {'junior':43,'middle':99,'senior':88,'head':45}
assert len(counts(rows,'batch')) == 11 and set(counts(rows,'batch').values()) == {25}
for r in rows:
    assert r['trainingEligible'] is True and r['assessmentEligible'] == (r['structure']=='standalone')
byid = {r['plannedId']:r for r in rows}
family_members = []
for f in families:
    members = [byid[i] for i in f['memberIds']]; family_members += f['memberIds']
    assert len(members) == (2 if f['type']=='pair' else 3)
    assert all(r['scenarioFamilyId']==f['scenarioFamilyId'] for r in members)
    for key in ['topicId','domain','requiredLevel','batch']: assert len({r[key] for r in members})==1
assert len(set(family_members))==94 and set(family_members)=={r['plannedId'] for r in rows if r['structure']!='standalone'}
with (HERE/'inputs/head_audit_v2.csv').open(encoding='utf-8-sig') as f: head_rows=list(csv.DictReader(f))
assert len(head_rows)==45
for r in head_rows:
    assert byid[r['plannedId']]['requiredLevel']=='head'
    assert all(byid[r['plannedId']][k]==v for k,v in r.items())
migrations = {f'TC-{i:03}':'negotiation-batna' for i in [64,168,255,256]}
migrations.update({f'TC-{i:03}':'interest-based-negotiation' for i in [121,192]})
for id, pattern in migrations.items():
    assert byid[id]['primaryPattern'] is None and byid[id]['vocabularyReviewRef']=='VR-BATNA'
    byid[id]['primaryPattern']=pattern; byid[id]['vocabularyReviewRef']=None
sources = ['TrainerScoringMapping.swift','TrainerScoringEngine.swift']
expected = ['a0e578503d7a13868326ffaa786ad363cddbe0782cecfa42a74f6cb2646d3cad','13e6a94d5deb5483d9cdf87fd6369540ad36cff821e220e6418409788dbeb5a4']
hashes = {n:digest(ROOT/'InteractiveBook/Trainer'/n) for n in sources}
assert list(hashes.values())==expected
for n in sources: assert digest(ROOT/'agent-artifacts/runtime-contract'/n)==hashes[n]
goldpath=ROOT/'InteractiveBook/TrainerContent/cases.json'; goldhash=digest(goldpath)
gold=read(goldpath)['cases']
assert len(gold)==25
excluded={'TC-001','TC-002','TC-003','TC-004','TC-017','TC-018'}
assert {r['id'] for r in gold if r.get('scenarioFamilyId')}==excluded
allrows = gold + [dict(r,id=r['plannedId']) for r in rows]
assessment = [r for r in allrows if r['assessmentEligible'] and r['id'] not in excluded]
assert len(assessment)==200
runtime_input={'rows':allrows,'template':gold[0],'assessmentIDs':[r['id'] for r in assessment]}
build=ROOT/'build/manifest-v2.1'; build.mkdir(parents=True,exist_ok=True)
(build/'input.json').write_text(json.dumps(runtime_input,ensure_ascii=False))
env=dict(os.environ); env.setdefault('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer')
subprocess.run(['/usr/bin/xcrun','swiftc',str(ROOT/'InteractiveBook/Trainer/TrainerModels.swift'),*[str(ROOT/'InteractiveBook/Trainer'/n) for n in sources],str(ROOT/'Tests/ScoringFixtures.swift'),str(HERE/'RuntimeAudit.swift'),'-o',str(build/'audit')],check=True,env=env)
subprocess.run([str(build/'audit'),str(build/'input.json'),str(build/'output.json')],check=True)
audit=read(build/'output.json'); mapped={r['id']:r for r in audit['rows']}
for r in rows:
    m=mapped[r['plannedId']]
    r.update(derivedRuntimeUiDomain=m['uiDomainTitle'],derivedRuntimePrimaryThinking=m['primaryThinking'],derivedRuntimeSecondaryThinking=m['secondaryThinking'],runtimeDerivationStatus='authoritative-swift-mapping',runtimeClassificationSource='authoritative-swift-mapping')
# Strict content preservation, allowing only the specifically authorized technical edits.
allowed={'derivedRuntimeUiDomain','derivedRuntimePrimaryThinking','derivedRuntimeSecondaryThinking','runtimeDerivationStatus','runtimeClassificationSource'}
for before,after in zip(original['manifest'],rows):
    ignored=allowed | ({'primaryPattern','vocabularyReviewRef'} if before['plannedId'] in migrations else set())
    assert {k:v for k,v in before.items() if k not in ignored}=={k:v for k,v in after.items() if k not in ignored}
for k in ['familyManifest','changedFamilyDesigns','headAudit','batchPlan']: assert master[k]==original[k]
protected={'manifest':[{k:v for k,v in r.items() if k not in allowed|{'primaryPattern','vocabularyReviewRef'}} for r in rows], 'familyManifest':families, 'headAudit':master['headAudit'],'batchPlan':master['batchPlan']}
fingerprint=hashlib.sha256(json.dumps(protected,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
# This explicitly defined fingerprint is new; no unverified legacy fingerprint is reused.
def coverage(group):
    domains={d:0 for d in audit['domainTitles']}; matrix={d:{l:0 for l in ['junior','middle','senior','head']} for d in domains}
    thinking={p:dict(primaryCaseCount=0,secondaryCaseCount=0,evidenceCaseCount=0,normalizedEvidenceWeightSum=0.0) for p in audit['thinkingTitles']}
    for r in group:
        m=mapped[r['id']]; d=m['uiDomain']; domains[d]+=1; matrix[d][r['requiredLevel']]+=1
        if m['primaryThinking']!='context':thinking[m['primaryThinking']]['primaryCaseCount']+=1
        for p in set(m['secondaryThinking'])-{'context'}:thinking[p]['secondaryCaseCount']+=1
        for p,w in m['normalizedWeights'].items():
            thinking[p]['evidenceCaseCount']+=1;thinking[p]['normalizedEvidenceWeightSum']+=w
    for p in thinking.values():p['normalizedEvidenceWeightSum']=round(p['normalizedEvidenceWeightSum'],10)
    return dict(caseCount=len(group),levels=counts(group,'requiredLevel'),uiDomains=domains,uiDomainByLevel=matrix,seniorPlusHeadByUiDomain={d:v['senior']+v['head'] for d,v in matrix.items()},thinking=thinking)
new=allrows[25:]
report=dict(authoritative=True,status='PASS',runtimeContract={'sourceHashes':hashes,'sourcePaths':['InteractiveBook/Trainer/'+n for n in sources],'referenceSync':'PASS'},
    domainTitles=audit['domainTitles'],thinkingTitles=audit['thinkingTitles'],
    gold=coverage(gold),new=coverage(new),all300=coverage(allrows),newAssessment=coverage([r for r in new if r['assessmentEligible']]),assessment200=coverage(assessment),
    assessmentPolicy={'excludedGoldLinkedIds':sorted(excluded),'appliedOnlyInThisReport':True,'productionBankChanged':False,'currentFlagsPoolBeforeGoldPolicyChange':206},
    structure=original['coverageSummary']['structure'],contextSensitivityScoredEvidence=0,
    thinkingRule='Primary 1, secondary 0.5, max per mapped category within case; exclude context, divide by max(1,sum); one evidence count per category per case.',
    engineWeightVerification=audit['engineWeightVerification'],unknownDomains=[],unknownPatterns=[],unknownVocabularyRejected=audit['unknownVocabularyRejected'],
    headFeasibility=audit['headFeasibility'],migrations=migrations,
    contentIntegrity={'protectedFieldsEqualToV2':True,'protectedPayloadSha256':fingerprint,'fingerprintDefinition':'Canonical JSON UTF-8 sorted keys, compact separators: manifest excluding derived/status/primaryPattern/vocabularyReviewRef + familyManifest + headAudit + batchPlan; separately assert primaryPattern/ref unchanged except six approved IDs.', 'goldBankSha256':goldhash},
    inputHashes={p.name:digest(p) for p in sorted((HERE/'inputs').iterdir())})
report['headFeasibility']['result']='PASS' if audit['headFeasibility']['breadthMet'] and audit['headFeasibility']['maximumSyntheticLevel']=='head' else 'FAIL'
report['headFeasibility']['seniorPlusHeadByUiDomain']=report['assessment200']['seniorPlusHeadByUiDomain']
assert report['headFeasibility']['eligibleCount']==200 and report['headFeasibility']['excludedMetadataCount']==0
master['manifestVersion']='2.1-runtime-finalized'
master['runtimeMappingStatus']={'authoritativeSwiftAvailable':True,'source':'authoritative-swift-mapping','sourceHashes':hashes,'validation':'PASS'}
master['coverageSummary']=copy.deepcopy(report)
master['remainingDisputedRows']=[]
master['productionTasksBeforeOrdinaryDiagnosticExpansion']=original['productionTasksBeforeOrdinaryDiagnosticExpansion'][:1]
master['batnaMigration']={'assignments':migrations,'status':'RESOLVED','runtimeThinking':'stakeholders'}
vocabulary=master['vocabularyReview']
vocabulary[0].update(affectedCaseIds=[i for i,p in migrations.items() if p=='negotiation-batna'],status='resolved-authoritative-runtime',approvedPattern='negotiation-batna',approvedThinkingCategory='stakeholders')
vocabulary.append(dict(concept='Interest-based / package negotiation',affectedCaseIds=['TC-121','TC-192'],approvedPattern='interest-based-negotiation',approvedThinkingCategory='stakeholders',status='resolved-authoritative-runtime',proposedPatternMeaning='Переход от позиций к интересам и обмен уступками по нескольким условиям; не подмена BATNA.'))
write('production_manifest_masterplan_v2_1.json',master)
csvwrite('production_manifest_TC026_TC300_v2_1.csv',rows)
# Validate the reference family CSV against the authoritative master before copying.
with (HERE/'inputs/linked_family_manifest_v2.csv').open(encoding='utf-8-sig') as f:
    family_csv = list(csv.DictReader(f))
assert len(family_csv) == len(families)
for row, ref in zip(family_csv, families):
    for k, value in row.items():
        expected_value = ref.get(k)
        if isinstance(expected_value, list): assert value == ' | '.join(expected_value)
        elif isinstance(expected_value, dict): assert json.loads(value) == expected_value
        elif expected_value is None: assert value == ''
        else: assert value == str(expected_value)
# The family CSV is unchanged content; preserve exact source bytes.
shutil.copyfile(HERE/'inputs/linked_family_manifest_v2.csv',HERE/'linked_family_manifest_v2_1.csv')
shutil.copyfile(HERE/'inputs/head_audit_v2.csv',HERE/'head_audit_v2.csv')
csvwrite('vocabulary_review_v2_1.csv',vocabulary)
write('runtime_coverage_v2_1.json',report)
review=f'''# Manifest v2.1 — authoritative technical finalization

Technical validation: PASS. Head breadth feasibility: {report['headFeasibility']['result']}.

Source: inputs/production_manifest_masterplan_v2.json and inputs/head_audit_v2.csv. No reconstruction. Previous v2.1 candidate was not used as authoritative input.

All 275 rows mapped by compiled production Swift sources. Unknown domain/pattern codes: 0. Six approved pattern migrations applied; all other row fields protected by deep equality. Family design, level, eligibility, batch and Head rationale unchanged. Context sensitivity scored evidence: 0.

Structure: 275 new = 181 standalone + 94 linked; 35 pairs + 8 triplets; 11 × 25 batches. Levels: J43 / M99 / S88 / H45.

Runtime UI-domain coverage (enum keys):
{json.dumps(report['all300']['uiDomains'],ensure_ascii=False)}

Assessment-only future pool: 200 = 19 gold standalone + 181 new standalone. Levels: J31 / M85 / S58 / H26. This assumes a separate approved exclusion of six linked gold cases; current production flags still yield 206. No cases.json changes were made.

Head senior+head breadth in assessment pool:
{json.dumps(report['assessment200']['seniorPlusHeadByUiDomain'],ensure_ascii=False)}

Actual engine with synthetic perfect responses confirms Head is structurally attainable; this is not a real diagnostic score or a guarantee for a shorter sampled session. Every level bucket has at least 5 cases; at least 5 UI domains have at least 3 senior/head cases, including People or Stakeholders and Portfolio or Finance.

Thinking coverage uses max mapped-category weight per case (primary 1, secondary .5), normalized by max(1, sum), context excluded. All 300 single-case impulse responses verified against TrainerScoringEngine; details and all coverage tables are in runtime_coverage_v2_1.json.

Content equality: PASS. Explicit protected-payload fingerprint: {fingerprint}. This uses a documented new fingerprint definition, not the undocumented prior candidate fingerprint.

Source hashes:
{json.dumps(hashes,indent=2)}

Reproduce: from repository root run `python3 agent-artifacts/manifests/v2.1/finalize.py`, then `bash scripts/check.sh`. Checks execution result is recorded separately in validation-result.json after execution. No production source modifications, commit or push are part of this pass. QA reads this shared directory directly.
'''
(HERE/'production_manifest_review_v2_1.md').write_text(review)
finals=['production_manifest_masterplan_v2_1.json','production_manifest_TC026_TC300_v2_1.csv','linked_family_manifest_v2_1.csv','production_manifest_review_v2_1.md','runtime_coverage_v2_1.json','vocabulary_review_v2_1.csv','head_audit_v2.csv']
for name in finals:
    assert (HERE/name).is_file() and (HERE/name).stat().st_size>0
    assert 'provisional-reconstruction' not in (HERE/name).read_text(encoding='utf-8-sig')
assert digest(goldpath)==goldhash
write('artifact-hashes.json',{n:digest(HERE/n) for n in finals})
print(json.dumps({'result':'PASS','head':report['headFeasibility'],'uiDomains':report['all300']['uiDomains'],'files':finals},ensure_ascii=False,indent=2))
