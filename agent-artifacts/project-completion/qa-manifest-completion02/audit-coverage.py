from pathlib import Path
import json,collections,math,hashlib
c=Path('agent-artifacts/manifests/v2.3-completion-02-candidate');o=Path('agent-artifacts/project-completion/qa-manifest-completion02');b=Path('agent-artifacts/project-completion/qa-manifest-completion01')
read=lambda p:json.loads(p.read_text())
a=read(o/'runtime-reproduced.json');prior=read(b/'runtime-reproduced.json');assert a==read(c/'runtime-output.json')
# Reuse independently executed accepted baseline only when runtime inputs match exactly.
assert read(o/'baseline-runtime-input.json')==read(Path('agent-artifacts/manifests/v2.3-completion-01-candidate/runtime-input.json'))
ri=read(c/'runtime-input.json')['rows'];oldri=read(o/'baseline-runtime-input.json')['rows'];am={r['id']:r for r in a['rows']};bm={r['id']:r for r in prior['rows']}
assert [k for k in bm if bm[k]!=am[k]]==['TC-146','TC-272'];assert a['headFeasibility']==prior['headFeasibility'];assert a['unknownVocabularyRejected'];assert a['engineWeightVerification']=='PASS: all 300 impulse responses'
sets={'gold':ri[:25],'new':ri[25:],'all300':ri,'newAssessment':[r for r in ri[25:] if r['assessmentEligible']],'assessment200':[r for r in ri if r['assessmentEligible']],'currentProduction100':ri[:100],'remaining200':ri[100:]}
def coverage(rs):
 domains={k:sum(am[r['id']]['uiDomain']==k for r in rs) for k in a['domainTitles']}; matrix={d:{l:sum(am[r['id']]['uiDomain']==d and r['requiredLevel']==l for r in rs) for l in ['junior','middle','senior','head']} for d in domains};thinking={}
 for k in a['thinkingTitles']:
  ps=[r['id'] for r in rs if am[r['id']]['primaryThinking']==k and k!='context'];ss=[r['id'] for r in rs if k in am[r['id']]['secondaryThinking'] and k!='context'];us=[r['id'] for r in rs if k in am[r['id']]['normalizedWeights']]
  thinking[k]={'primaryCaseIDs':ps,'secondaryCaseIDs':ss,'unionCaseIDs':us,'primaryCaseCount':len(ps),'secondaryCaseCount':len(ss),'unionCaseCount':len(us),'normalizedEvidenceWeightSum':sum(am[id]['normalizedWeights'][k] for id in us)}
 return {'count':len(rs),'levels':dict(collections.Counter(r['requiredLevel'] for r in rs)),'uiDomains':domains,'uiDomainByLevel':matrix,'thinking':thinking}

def equivalent(x,y):
 if isinstance(x,dict):return x.keys()==y.keys() and all(equivalent(x[k],y[k]) for k in x)
 if isinstance(x,float):return math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12)
 return x==y

recalc={k:coverage(rs) for k,rs in sets.items()};published=read(c/'runtime_coverage_v2_3_completion_02_candidate.json');assert equivalent(recalc,published['pools']);assert published['contextSensitivityScoredEvidence']==0 and published['unknownDomains']==published['unknownPatterns']==[]
(o/'coverage-reproduced.json').write_text(json.dumps(recalc,ensure_ascii=False,indent=2)+'\n')
deltas={};empty=[]
for pool,rs in sets.items():
 result={}
 for level in ['all','junior','middle','senior','head']:
  selected=[r for r in rs if level=='all' or r['requiredLevel']==level]
  for k in a['thinkingTitles']:
   before=[r['id'] for r in selected if k in bm[r['id']]['normalizedWeights']];after=[r['id'] for r in selected if k in am[r['id']]['normalizedWeights']];bw=sum(bm[id]['normalizedWeights'][k] for id in before);aw=sum(am[id]['normalizedWeights'][k] for id in after)
   if before!=after or not math.isclose(bw,aw):result[k+'/'+level]={'countBefore':len(before),'countAfter':len(after),'weightBefore':bw,'weightAfter':aw,'weightDelta':aw-bw,'removedIDs':sorted(set(before)-set(after)),'addedIDs':sorted(set(after)-set(before))}
   if before and not after:empty.append([pool,k,level])
 deltas[pool]=result
head={d:sum(r['assessmentEligible'] and r['requiredLevel'] in ['senior','head'] and am[r['id']]['uiDomain']==d for r in ri) for d in a['domainTitles']}
assert sum(n>=3 for n in head.values())==8
(o/'coverage-delta-evidence.json').write_text(json.dumps({'onlyRuntimeChangedIDs':['TC-146','TC-272'],'headFeasibilityUnchanged':True,'headSeniorPlusEvidence':head,'newEmptyThinkingLevelCells':empty,'deltas':deltas},ensure_ascii=False,indent=2)+'\n')
assert equivalent(recalc['currentProduction100'],read(b/'coverage-reproduced.json')['pools']['currentProduction100'])
print('PASS seven pools; engine impulse300; head unchanged; new empty cells:',empty);print(json.dumps(deltas['assessment200'],indent=2));print('Head',head)
