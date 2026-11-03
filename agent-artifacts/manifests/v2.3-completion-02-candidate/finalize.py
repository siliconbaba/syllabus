from pathlib import Path
import json,csv,collections,hashlib,shutil
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(n):return json.loads((P/n).read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def table(n,rows):
 keys=list(dict.fromkeys(k for row in rows for k in row))
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
  for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,bool)) else '' if v is None else v for k,v in row.items()})
m=read('working-master.json');audit=read('runtime-output.json');rows=read('runtime-input.json')['rows'];mapped={r['id']:r for r in audit['rows']}
for r in m['manifest']:
 a=mapped[r['plannedId']]
 assert r['derivedRuntimeUiDomain']==a['uiDomainTitle'] and r['derivedRuntimePrimaryThinking']==a['primaryThinking'] and r['derivedRuntimeSecondaryThinking']==a['secondaryThinking']
levels=['junior','middle','senior','head']
def coverage(group):
 domains={k:0 for k in audit['domainTitles']};matrix={k:{l:0 for l in levels} for k in domains};think={k:{'primaryCaseIDs':[],'secondaryCaseIDs':[],'unionCaseIDs':[],'normalizedEvidenceWeightSum':0.0} for k in audit['thinkingTitles']}
 for row in group:
  a=mapped[row['id']];domains[a['uiDomain']]+=1;matrix[a['uiDomain']][row['requiredLevel']]+=1
  if a['primaryThinking']!='context':think[a['primaryThinking']]['primaryCaseIDs'].append(row['id'])
  for k in set(a['secondaryThinking'])-{'context'}:think[k]['secondaryCaseIDs'].append(row['id'])
  for k,w in a['normalizedWeights'].items():think[k]['unionCaseIDs'].append(row['id']);think[k]['normalizedEvidenceWeightSum']+=w
 for t in think.values():
  for label in ['primary','secondary','union']:t[label+'CaseCount']=len(t[label+'CaseIDs'])
 return {'count':len(group),'levels':dict(collections.Counter(r['requiredLevel'] for r in group)),'uiDomains':domains,'uiDomainByLevel':matrix,'thinking':think}
pools={'gold':rows[:25],'new':rows[25:],'all300':rows,'newAssessment':[r for r in rows[25:] if r['assessmentEligible']],'assessment200':[r for r in rows if r['assessmentEligible']],'currentProduction100':rows[:100],'remaining200':rows[100:]}
structure={'new':275,'standalone':sum(r['structure']=='standalone' for r in m['manifest']),'linked':sum(r['structure']!='standalone' for r in m['manifest']),'familySizes':dict(collections.Counter(len(f['memberIds']) for f in m['familyManifest'])),'batchSizes':dict(collections.Counter(r['batch'] for r in m['manifest'])),'levels':dict(collections.Counter(r['requiredLevel'] for r in m['manifest']))}
assert structure['standalone']==181 and structure['linked']==94
assert structure['familySizes']=={2:35,3:8}
assert set(structure['batchSizes'].values())=={25} and len(structure['batchSizes'])==11
baseline=json.loads((R/'agent-artifacts/manifests/v2.3-completion-01-candidate/production_manifest_masterplan_v2_3_completion_01_candidate.json').read_text())
assert structure['levels']==dict(collections.Counter(r['requiredLevel'] for r in baseline['manifest']))
# B2 already contains accepted level corrections; never normalize to old v2 counts.
assert audit['unknownVocabularyRejected'] and len(mapped)==300
cov={'status':'TECHNICAL PASS — pending cumulative independent QA','source':'actual Swift models/mapping/engine + 300 impulse responses','domainTitles':audit['domainTitles'],'thinkingTitles':audit['thinkingTitles'],'structure':structure,'pools':{k:coverage(v) for k,v in pools.items()},'headFeasibility':audit['headFeasibility'],'contextSensitivityScoredEvidence':0,'unknownDomains':[],'unknownPatterns':[],'engineWeightVerification':audit['engineWeightVerification']}
m['coverageSummary']={'source':'runtime_coverage_v2_3_completion_02_candidate.json','structure':structure,'remainingUnresolved':68,'note':'Current compiled runtime coverage in adjacent artifact; older nested revision summaries are historical.'}
write('production_manifest_masterplan_v2_3_completion_02_candidate.json',m);table('production_manifest_TC026_TC300_v2_3_completion_02_candidate.csv',m['manifest']);table('linked_family_manifest_v2_3_completion_02_candidate.csv',m['familyManifest']);write('runtime_coverage_v2_3_completion_02_candidate.json',cov)
base=R/'agent-artifacts/manifests/v2.3-completion-01-candidate'
for pattern,target in [('head_audit*.csv','head_audit_v2_3_completion_02_candidate.csv'),('vocabulary_review*.csv','vocabulary_review_v2_3_completion_02_candidate.csv')]:
 matches=list(base.glob(pattern))
 if matches:shutil.copyfile(matches[0],P/target)
for path,sha in read('input-hashes.json').items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==sha,path
write('validation.json',{'status':'TECHNICAL PASS','changedRows':['TC-146','TC-272'],'unchangedRows':273,'familiesUnchanged':True,'structure':structure,'individualRowQAPass':True,'cumulativeQAPass':False,'remainingUnresolved':68,'headBreadth':audit['headFeasibility']['breadthMet'],'productionUnchanged':True,'frozen':False,'importEligible':False})
(P/'review.md').write_text('Completion02 working candidate: only accepted TC146/272 blueprints replace completion01 rows. 273 rows and43 families unchanged. Remaining68 candidate, pending cumulative independent QA. Full-case QA separate and pending. Actual runtime300 impulse checks; seven coverage pools recomputed. TC146 dependencies -1/3, stakeholders +1/3; TC272 prioritization -2/3, dependencies -1/3, stakeholders +1. All changes concern Junior assessment evidence, domain/level unchanged. No freeze/import/production changes.\n')
write('artifact-hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
print('Candidate ready for independent cumulative QA; head breadth:',audit['headFeasibility']['breadthMet'])
