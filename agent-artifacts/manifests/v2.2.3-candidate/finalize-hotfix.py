import json,csv,copy,hashlib,collections,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent/'v2.2.2'
def read(p):return json.loads(p.read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(n,rs):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else 'true' if v is True else 'false' if v is False else '' if v is None else v for k,v in r.items()} for r in rs])
base=read(B/'production_manifest_masterplan_v2_2_2.json');m=read(P/'working-master.json');audit=read(P/'runtime-output.json');mapped={r['id']:r for r in audit['rows']};old={r['plannedId']:r for r in base['manifest']}
for r in m['manifest']:
 x=mapped[r['plannedId']];v=dict(derivedRuntimeUiDomain=x['uiDomainTitle'],derivedRuntimePrimaryThinking=x['primaryThinking'],derivedRuntimeSecondaryThinking=x['secondaryThinking'])
 if r['plannedId']=='TC-085':r.update(v)
 else:assert all(r[k]==v[k] for k in v)
rows=m['manifest'];new=next(r for r in rows if r['plannedId']=='TC-085');fields=[k for k in new if new[k]!=old['TC-085'][k]]
allowed={'oneSentenceScenarioConcept','decisiveFactsConcept','oneSentenceDecisionBoundary','primaryPattern','secondaryPatterns','whyLevel','derivedRuntimeUiDomain','derivedRuntimePrimaryThinking','derivedRuntimeSecondaryThinking'}
assert set(fields)<=allowed
assert [r['plannedId'] for r in rows if r!=old[r['plannedId']]]==['TC-085'];assert m['familyManifest']==base['familyManifest']
def counts(rs,key):return dict(sorted(collections.Counter(r[key] for r in rs).items()))
def coverage(group):
 domains={d:0 for d in audit['domainTitles']};matrix={d:{l:0 for l in ['junior','middle','senior','head']} for d in domains};thinking={p:dict(primaryCaseIDs=[],secondaryCaseIDs=[],unionCaseIDs=[],normalizedEvidenceWeightSum=0.) for p in audit['thinkingTitles']}
 for r in group:
  x=mapped[r['id']];d=x['uiDomain'];domains[d]+=1;matrix[d][r['requiredLevel']]+=1
  if x['primaryThinking']!='context':thinking[x['primaryThinking']]['primaryCaseIDs'].append(r['id'])
  for p in set(x['secondaryThinking'])-{'context'}:thinking[p]['secondaryCaseIDs'].append(r['id'])
  for p,w in x['normalizedWeights'].items():thinking[p]['unionCaseIDs'].append(r['id']);thinking[p]['normalizedEvidenceWeightSum']+=w
 for v in thinking.values():v.update(primaryCaseCount=len(v['primaryCaseIDs']),secondaryCaseCount=len(v['secondaryCaseIDs']),evidenceCaseCount=len(v['unionCaseIDs']),normalizedEvidenceWeightSum=round(v['normalizedEvidenceWeightSum'],10))
 return dict(caseCount=len(group),levels=counts(group,'requiredLevel'),uiDomains=domains,uiDomainByLevel=matrix,seniorPlusHeadByUiDomain={d:v['senior']+v['head'] for d,v in matrix.items()},thinking=thinking)
inp=read(P/'runtime-input.json');allrows=inp['rows'];gold=allrows[:25];newrows=allrows[25:];assessment=[r for r in allrows if r['id'] in inp['assessmentIDs']];assert len(allrows)==300 and len(assessment)==200
cov=copy.deepcopy(base['coverageSummary'])
for k,g in [('gold',gold),('new',newrows),('all300',allrows),('newAssessment',[r for r in newrows if r['assessmentEligible']]),('assessment200',assessment)]:
 cov[k]=coverage(g)
 for field in ['caseCount','levels','uiDomains','uiDomainByLevel','seniorPlusHeadByUiDomain']:assert cov[k][field]==base['coverageSummary'][k][field]
assert cov['gold']==base['coverageSummary']['gold']
for k,v in audit['headFeasibility'].items():
 assert (set(v)==set(cov['headFeasibility'][k])) if isinstance(v,list) else (v==cov['headFeasibility'][k])
for n,h in cov['runtimeContract']['sourceHashes'].items():assert sha(R/'InteractiveBook/Trainer'/n)==h
assert cov['engineWeightVerification']==audit['engineWeightVerification']
m['coverageSummary']=cov;m['manifestVersion']='2.2.3-TC085-surgical-candidate'
assert all(m[k]==base[k] for k in base if k not in ['manifestVersion','manifest','coverageSummary'])
assert len(rows)==len({r['plannedId'] for r in rows})==275
assert counts(rows,'structure')==dict(pair=70,standalone=181,triplet=24)
assert collections.Counter(f['type'] for f in m['familyManifest'])==dict(pair=35,triplet=8)
assert len(counts(rows,'batch'))==11 and set(counts(rows,'batch').values())=={25}
topics={t['id']:t['sectionID'] for t in read(R/'InteractiveBook/TrainerContent/topics.json')['topics']};by={r['plannedId']:r for r in rows}
for r in rows:
 assert topics[r['topicId']]==r['partId'];assert r['trainingEligible'] and r['assessmentEligible']==(r['structure']=='standalone')
for f in m['familyManifest']:
 members=[by[id] for id in f['memberIds']];assert len({(r['batch'],r['topicId'],r['domain'],r['requiredLevel']) for r in members})==1;assert all(r['scenarioFamilyId']==f['scenarioFamilyId'] for r in members)
b3=[r for r in rows if r['batch']=='Batch 03'];assert counts(b3,'requiredLevel')==dict(junior=5,middle=12,senior=5,head=3)
write('production_manifest_masterplan_v2_2_3_candidate.json',m);table('production_manifest_TC026_TC300_v2_2_3_candidate.csv',rows)
# Exactly preserve exported family CSV bytes, not merely content.
shutil.copyfile(B/'linked_family_manifest_v2_2_2.csv',P/'linked_family_manifest_v2_2_3_candidate.csv')
write('runtime_coverage_v2_2_3_candidate.json',cov)
table('change-log-v2_2_2-to-v2_2_3.csv',[{'TC-ID':'TC-085','issue':'Confirmed manifest-level near duplicate TC-004','fields changed':fields,'before':{k:old['TC-085'][k] for k in fields},'after':{k:new[k] for k in fields},'why fixed':'New judgment selects repeatable test-data preparation within a finite regression horizon; fixed evidence set, no targeted-vs-full decision.'}])
write('validation-result.json',{'status':'TECHNICAL PASS — candidate, pending joint independent QA','manifestDefectConfirmed':True,'changedPlannedRows':1,'changedIDs':['TC-085'],'unchangedPlannedRows':274,'changedFamilyContracts':0,'unchangedFamilyContracts':43,'unexpectedSemanticDiff':0,'allowedOtherChanges':['manifestVersion label','thinking coverage caused solely by TC-085'],'historicalProvenanceNote':'Inherited freezeProvenance and earlier revision records describe baseline v2.2.2 only; this candidate is not frozen.','structure':{'planned':275,'standalone':181,'linked':94,'pairs':35,'triplets':8,'batches':11,'batchSize':25},'batch03':{'cases':25,'standalone':16,'linked':9,'families':4,'levels':counts(b3,'requiredLevel')},'eligibilityUnchanged':True,'validPartTopic':True,'familyConsistency':True,'noSplitFamily':True,'runtime':'PASS compiled actual production Swift','unknownCodes':0,'engineWeightVerification':audit['engineWeightVerification'],'headFeasibility':audit['headFeasibility'],'productionUnchanged':True,'candidateFrozen':False})
assert all(sha(R/p)==h for p,h in read(P/'protected-input-hashes.json').items())
print('Manifest finalized; TC-085',fields,new['derivedRuntimePrimaryThinking'],new['derivedRuntimeSecondaryThinking'])
