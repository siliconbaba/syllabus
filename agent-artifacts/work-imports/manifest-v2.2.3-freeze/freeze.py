import collections,csv,hashlib,json,pathlib,subprocess,os,copy,math
HERE=pathlib.Path(__file__).resolve().parent; ROOT=HERE.parents[2]
C=ROOT/'agent-artifacts/manifests/v2.2.3-candidate'; B=ROOT/'agent-artifacts/manifests/v2.2.2'; F=ROOT/'agent-artifacts/manifests/v2.2.3'; Q=ROOT/'agent-artifacts/qa/batch-03-r3'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
q=read(Q/'QA-verdict.json'); assert q['verdict']=='READY FOR FREEZE + IMPORT' and q['severity']=={'blocker':0,'major':0,'minor':0} and q['remainingIds']==[]
assert not F.exists(), 'Frozen destination already exists; do not overwrite'
required=['production_manifest_masterplan_v2_2_3_candidate.json','production_manifest_TC026_TC300_v2_2_3_candidate.csv','linked_family_manifest_v2_2_3_candidate.csv','manifest-hotfix-report.md','change-log-v2_2_2-to-v2_2_3.csv','duplication-audit-v2_2_3.csv','runtime_coverage_v2_2_3_candidate.json','validation-result.json','artifact-hashes.json']
assert all((C/n).is_file() for n in required)
for n,h in read(C/'artifact-hashes.json').items():assert sha(C/n)==h,n
protected={str(p.relative_to(ROOT)):sha(p) for folder in [B,C,Q,ROOT/'InteractiveBook',ROOT/'docs',ROOT/'Tests',ROOT/'scripts'] for p in folder.rglob('*') if p.is_file()}
write(HERE/'protected-input-hashes.json',protected)
(HERE/'git-status-before.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
prod=ROOT/'InteractiveBook/TrainerContent/cases.json';prodhash=sha(prod);assert prodhash=='2540570c2b907ea0e48cb9752e715486126e006a6100bd27e2f9f170d2c99689'
b=read(B/'production_manifest_masterplan_v2_2_2.json');c=read(C/required[0])
expected=['TC-085'];ef=[]
def diff(a,z,key):
 x={r[key]:r for r in a};y={r[key]:r for r in z}; assert x.keys()==y.keys()
 return sorted(k for k in x if x[k]!=y[k])
assert diff(b['manifest'],c['manifest'],'plannedId')==expected
assert diff(b['familyManifest'],c['familyManifest'],'scenarioFamilyId')==ef
assert diff(b['changedFamilyDesigns'],c['changedFamilyDesigns'],'scenarioFamilyId')==ef
rootdiff=[k for k in b.keys()|c.keys() if b.get(k)!=c.get(k)]
assert set(rootdiff)=={'manifest','manifestVersion','coverageSummary'}
# Non-thinking aggregates must stay exactly unchanged.
def leaves(a,z,path=''):
 if isinstance(a,dict) and isinstance(z,dict):
  out=[]
  for k in a.keys()|z.keys():out+=leaves(a.get(k),z.get(k),path+'/'+k)
  return out
 return [] if a==z else [path]
aggregate_diff=leaves(b['coverageSummary'],c['coverageSummary'])
assert all(p=='/status' or '/thinking/' in p for p in aggregate_diff),aggregate_diff
rows=c['manifest'];fam=c['familyManifest']; ids={r['plannedId']:r for r in rows}
assert len(rows)==275 and set(ids)=={f'TC-{i:03}' for i in range(26,301)}
assert collections.Counter(r['structure'] for r in rows)=={'standalone':181,'pair':70,'triplet':24}
assert collections.Counter(f['type'] for f in fam)=={'pair':35,'triplet':8}
assert len(collections.Counter(r['batch'] for r in rows))==11 and set(collections.Counter(r['batch'] for r in rows).values())=={25}
for old,new in zip(b['manifest'],rows):
 for k in ['partId','topicId','domain','requiredLevel','batch','structure','scenarioFamilyId','familyPosition','trainingEligible','assessmentEligible']:
  assert old[k]==new[k],(new['plannedId'],k)
for r in rows:assert r['trainingEligible'] is True and r['assessmentEligible']==(r['structure']=='standalone')
seen=[]
for f in fam:
 members=[ids[i] for i in f['memberIds']]; seen+=f['memberIds']
 assert len(members)==(2 if f['type']=='pair' else 3)
 assert all(r['scenarioFamilyId']==f['scenarioFamilyId'] for r in members)
 assert {r['familyPosition'] for r in members}==set(range(1,len(members)+1))
 for k in ['topicId','domain','requiredLevel','batch']:assert len({r[k] for r in members})==1
 assert members[0]['topicId']==f['topicId'] and members[0]['requiredLevel']==f['requiredLevel']
 assert len({r['decisiveMutationConcept'] for r in members})==len(members)
 if f['scenarioFamilyId'] in ef:
  for r in members:
   assert f['stateByMember'][r['plannedId']] in r['decisiveMutationConcept']
   assert f['decisionBoundaryByState'][r['plannedId']]==r['oneSentenceDecisionBoundary']
  assert f['singleLogicalVariable'] and f['factsThatMustRemainConstant'] and f['whyMutationIsControlled']
assert len(seen)==len(set(seen))==94
batch=[r for r in rows if 76<=int(r['plannedId'][3:])<=100]
assert len(batch)==25 and sum(r['structure']=='standalone' for r in batch)==16
assert len({r['scenarioFamilyId'] for r in batch if r['scenarioFamilyId']})==4
assert collections.Counter(r['requiredLevel'] for r in batch)=={'junior':5,'middle':12,'senior':5,'head':3}
def csvcheck(path,records):
 csvrows=list(csv.DictReader(path.open(encoding='utf-8-sig')));assert len(csvrows)==len(records)
 for r,ref in zip(csvrows,records):
  for k,v in r.items():
   e=ref.get(k)
   if isinstance(e,list):
    try: value=json.loads(v)
    except (ValueError,TypeError):value=v.split(' | ') if v else []
    assert value==e,(path.name,k)
   elif isinstance(e,dict):assert json.loads(v)==e
   elif isinstance(e,bool):assert v.lower()==str(e).lower()
   elif e is None:assert v in ['', 'null']
   else:assert v==str(e),(path.name,k)
 # Ensure no non-null data silently absent from CSV.
 assert all(k in csvrows[0] for ref in records for k,v in ref.items() if v is not None)
csvcheck(C/required[1],rows);csvcheck(C/required[2],fam)
# Build inputs from the actual manifest rather than trusting a cached runtime output.
gold=read(prod)['cases'][:25]; allrows=gold+[dict(r,id=r['plannedId']) for r in rows]
assessment=[r['id'] for r in allrows if not r.get('scenarioFamilyId')]
assert len(assessment)==200
write(HERE/'runtime-input.json',{'rows':allrows,'template':gold[0],'assessmentIDs':assessment})
sources=['TrainerScoringMapping.swift','TrainerScoringEngine.swift'];coverage=read(C/required[6])
for n in sources:assert sha(ROOT/'InteractiveBook/Trainer'/n)==coverage['runtimeContract']['sourceHashes'][n]
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer');exe=ROOT/'build/checks/freeze-runtime-audit'
subprocess.run(['xcrun','swiftc',str(ROOT/'InteractiveBook/Trainer/TrainerModels.swift'),*[str(ROOT/'InteractiveBook/Trainer'/n) for n in sources],str(ROOT/'Tests/ScoringFixtures.swift'),str(HERE/'RuntimeAudit.swift'),'-o',str(exe)],check=True,env=env)
subprocess.run([str(exe),str(HERE/'runtime-input.json'),str(HERE/'runtime-output.json')],check=True)
audit=read(HERE/'runtime-output.json');cached=read(C/'runtime-output.json')
def near(a,z):
 if isinstance(a,dict):return a.keys()==z.keys() and all(near(a[k],z[k]) for k in a)
 if isinstance(a,list):return len(a)==len(z) and all(near(x,y) for x,y in zip(a,z))
 if isinstance(a,float):return math.isclose(a,z,abs_tol=1e-10)
 return a==z
assert near(audit,cached),'Runtime recalculation differs from candidate'
mapped={r['id']:r for r in audit['rows']}
for r in rows:
 m=mapped[r['plannedId']];assert (r['derivedRuntimeUiDomain'],r['derivedRuntimePrimaryThinking'],r['derivedRuntimeSecondaryThinking'])==(m['uiDomainTitle'],m['primaryThinking'],m['secondaryThinking'])
print('ALL PRE-FREEZE GATES PASS',flush=True)
# Promote by copying data; only root freeze metadata changes.
F.mkdir()
frozen=copy.deepcopy(c);frozen['manifestVersion']='2.2.2-frozen'
frozen['freezeProvenance']={'baseline':'v2.2.2','candidate':'v2.2.3-candidate','independentQA':'READY FOR FREEZE + IMPORT','qaVerdictSha256':sha(Q/'QA-verdict.json'),'candidateMasterplanSha256':sha(C/required[0]),'authoritativeFor':'Batch 04+','authoringStarted':False}
write(F/'production_manifest_masterplan_v2_2_3.json',frozen)
renames={required[1]:'production_manifest_TC026_TC300_v2_2_3.csv',required[2]:'linked_family_manifest_v2_2_3.csv',required[6]:'runtime_coverage_v2_2_3.json','change-log-v2_2_2-to-v2_2_3.csv':'change-log-v2_2_2-to-v2_2_3.csv','duplication-audit-v2_2_3.csv':'duplication-audit-v2_2_3.csv'}
for src,dst in renames.items():(F/dst).write_bytes((C/src).read_bytes())
assert {k:v for k,v in frozen.items() if k not in ['manifestVersion','freezeProvenance']}=={k:v for k,v in c.items() if k not in ['manifestVersion','freezeProvenance']}
csvcheck(F/'production_manifest_TC026_TC300_v2_2_3.csv',frozen['manifest']);csvcheck(F/'linked_family_manifest_v2_2_3.csv',frozen['familyManifest'])
for n,h in protected.items():assert sha(ROOT/n)==h,n
result={'freeze':'PASS','authoritativeManifest':'v2.2.3','plannedRows':275,'standalone':181,'linked':94,'pairFamilies':35,'tripletFamilies':8,'batches':11,'batch03':{'cases':25,'standalone':16,'linked':9,'families':4,'levels':{'junior':5,'middle':12,'senior':5,'head':3}},'changedRows':expected,'changedFamilies':ef,'unchangedRows':274,'unchangedFamilies':43,'unexpectedSemanticChanges':0,'candidateFrozenEquality':'PASS except manifestVersion and updated freezeProvenance','runtimeVocabulary':'PASS','derivedRuntimeMetadata':'PASS: exact candidate equality','engineWeightVerification':audit['engineWeightVerification'],'unknownDomains':0,'unknownPrimaryPatterns':0,'unknownSecondaryPatterns':0,'structuralValidation':'PASS','csvConsistency':'PASS','familyValidation':'PASS','productionUnchanged':True,'productionSha256':prodhash,'candidateHashRecordsVerified':len(read(C/'artifact-hashes.json')),'unexpectedChanges':0,'batch03ImportApproved':True,'authoringStarted':False,'commitPushPerformed':False}
write(F/'validation-result.json',result);write(HERE/'validation-result.json',result)
evidence={'baseline':'v2.2.2','allowedChangedRows':expected,'allowedChangedFamilies':ef,'unchangedRows':274,'unchangedFamilies':43,'unexpectedSemanticDiffCount':0,'rootDiff':rootdiff,'derivedAggregateDiffPaths':aggregate_diff,'candidateFrozenEquality':'PASS','permittedFreezeChanges':['manifestVersion','freezeProvenance'],'copiedFilesByteEquality':{dst:sha(C/src)==sha(F/dst) for src,dst in renames.items()},'productionHashBefore':prodhash,'productionHashAfter':sha(prod),'protectedInputHashes':'protected-input-hashes.json'}
write(HERE/'regression-evidence.json',evidence)
review='# Frozen manifest v2.2.3\n\nCURRENT AUTHORITATIVE MANIFEST = v2.2.3. Baseline v2.2.2, approved candidate v2.2.3-candidate. Independent QA: qa/batch-03-r3, READY FOR FREEZE + IMPORT; Blocker/Major/Minor 0, remaining IDs [].\n\nOnly planned TC-085 changed; 274 rows and all 43 family contracts unchanged. Unexpected semantic changes 0. TC-085 hotfix approved: source SUPPORTED, unique strongest PASS, Middle PASS, TC-004 comparison ALLOWED REINFORCEMENT. This promotion does not perform content editing.\n\n275 planned rows:181 standalone/94 linked;35 pair/8 triplet families;11×25 batches. Batch03:25,16 standalone,9 linked,4 families,J5/M12/S5/H3. CSV/JSON, family contracts and runtime vocabulary verified. Compiled authoritative mapping/engine reproduced all derived values and 300 impulse responses, matching candidate.\n\nCandidate→frozen semantic equality PASS except root version/freeze provenance. Historical embedded statuses retained, superseded by this freeze evidence. v2.2.2 and candidate preserved unchanged. Production SHA before this separate import stage:2540570c2b907ea0e48cb9752e715486126e006a6100bd27e2f9f170d2c99689. Subsequent Batch03 import evidence lives in work-imports/batch-03/.\n\nNo application/schema/scoring changes, commit/push or Batch04 authoring.\n'
(F/'manifest-review-v2_2_3.md').write_text(review);(HERE/'freeze-report.md').write_text(review)
write(F/'artifact-hashes.json',{p.name:sha(p) for p in sorted(F.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
for name,h in read(F/'artifact-hashes.json').items():assert sha(F/name)==h
for path in F.glob('*.json'):read(path)
(ROOT/'agent-artifacts/manifests/CURRENT.md').write_text('# Authoritative frozen blueprint\n\nCURRENT AUTHORITATIVE MANIFEST = **v2.2.3**.\n\nBatch 04+ source of truth: [v2.2.3](v2.2.3/manifest-review-v2_2_3.md).\n\nv2.2, v2.2.2 and v2.2.3-candidate are historical/audit only and must not be used as authoring baselines.\n\nMasterplan SHA-256: `'+sha(F/'production_manifest_masterplan_v2_2_3.json')+'`.\n')
write(HERE/'artifact-hashes.json',{str(p.relative_to(ROOT)):sha(p) for p in [*sorted(F.iterdir()),*[p for p in sorted(HERE.iterdir()) if p.name!='artifact-hashes.json'],ROOT/'agent-artifacts/manifests/CURRENT.md'] if p.is_file()})
print(json.dumps(result,indent=2))
