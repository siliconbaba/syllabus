from pathlib import Path as P
import json,hashlib,csv,collections,math
j=lambda f:json.loads(P(f).read_text())
h=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
d=P('agent-artifacts/manifests/v2.3-completion-05-candidate');q=P(__file__).parent
mf=next(d.glob('production*json')); b=j(mf);rev=b['completion05Revision']; hashes=j(d/'input-hashes.json');assert rev['inputs']==hashes and all(h(k)==v for k,v in hashes.items())
ps=[j(k) for k in hashes if k.endswith('proposed-projection.json')];qa=[j(k) for k in hashes if k.endswith('QA-verdict.json')];assert {x['candidateSHA256'] for x in qa}=={v for k,v in hashes.items() if k.endswith('proposed-projection.json')}
a=j(next(k for k in hashes if 'masterplan' in k));ids=rev['approvedRows'];families=rev['approvedFamilies'];assert set(ids)==set().union(*(set(x['acceptedBlueprintIDs']) for x in qa))
assert {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}=={'coverageSummary','familyManifest','changedFamilyDesigns','completion05Revision','completionRevision','manifest','manifestVersion'}
for k,key,changed in [('manifest','plannedId',ids),('familyManifest','scenarioFamilyId',families),('changedFamilyDesigns','scenarioFamilyId',families)]:
 left,right=a[k],b[k]; assert [r[key] for r in left]==[r[key] for r in right] and sorted(t[key] for r,t in zip(left,right) if r!=t)==sorted(changed)
 exp={r[key]:r for p in ps for r in p.get('familyManifest' if k=='changedFamilyDesigns' else k,[])}
 for r in right:
  if r[key] in changed:
   if k=='changedFamilyDesigns':
    old=next(x for x in left if x[key]==r[key]);assert r==dict(old,**{f:exp[r[key]][f] for f in ['singleLogicalVariable','expectedStrongestShiftConcept']})
   else:assert r==exp[r[key]]
for key,pat in [('familyManifest','linked*.csv'),('manifest','production*.csv')]:
 with next(d.glob(pat)).open(encoding='utf-8-sig') as f:
  reader=csv.DictReader(f); rows=list(reader);assert set(reader.fieldnames)==set.union(*(set(r) for r in b[key])) and len(rows)==len(b[key])
  for row,c in zip(rows,b[key]):
   for k,v in row.items():
    val=c.get(k);assert (json.loads(v)==val if isinstance(val,(dict,list)) else v==('' if val is None else str(val).lower() if isinstance(val,bool) else str(val)))
priorq='agent-artifacts/project-completion/qa-manifest-completion04/QA-verdict.json'
rem=[i for i in j(priorq)['remainingUnresolvedIDs'] if i not in ids];assert len(rem)==59 and rem==rev['remainingUnresolvedIDs']==b['completionRevision']['remainingUnresolvedIDs'] and b['coverageSummary']['remainingUnresolved']==b['completionRevision']['remainingUnresolved']==59
ri=j(d/'runtime-input.json');rt=j(q/'runtime-reproduced.json'); pub=j(next(d.glob('runtime_coverage*')));assert all(h(k)==v for k,v in pub['sourceHashes'].items())
def eq(x,y):
 if isinstance(x,dict):return isinstance(y,dict) and x.keys()==y.keys() and all(eq(x[k],y[k]) for k in x)
 if isinstance(x,float):return math.isclose(x,y,abs_tol=1e-11,rel_tol=1e-12)
 return x==y
assert eq(rt,j(d/'runtime-output.json'))
prod=j('InteractiveBook/TrainerContent/cases.json')['cases']
def make_rows(m):
 return [{k:(r.get('plannedId') or r['id']) if k=='id' else r[k] for k in ri['rows'][0]} for r in [*prod[:25],*m['manifest']]]
rows=make_rows(b);prev=make_rows(a);assert rows==ri['rows'] and ri['assessmentIDs']==[r['id'] for r in rows if r['assessmentEligible']] and ri['template']==prod[0];assert all(all(row[k]==r[k] for k in row) for row,r in zip(rows,prod));assert [r['id'] for x,r in zip(prev,rows) if x!=r]==['TC-135']
oldrt=j('agent-artifacts/project-completion/qa-manifest-completion02/runtime-reproduced.json');oldri=j('agent-artifacts/manifests/v2.3-completion-02-candidate/runtime-input.json');assert all(all(x[k]==r[k] for k in r) for x,r in zip(oldri['rows'],prev))
am={r['id']:r for r in rt['rows']};bm={r['id']:r for r in oldrt['rows']};assert [k for k in bm if not eq(bm[k],am[k])]==['TC-135']
assert rt['headFeasibility']==oldrt['headFeasibility']==pub['headFeasibility'];assert rt['engineWeightVerification']==pub['engineWeightVerification']=='PASS: all 300 impulse responses';assert rt['unknownVocabularyRejected'] and pub['unknownVocabularyRejected'] and pub['contextSensitivityScoredEvidence']==0
sets={'gold':rows[:25],'new':rows[25:],'all300':rows,'newAssessment':[r for r in rows[25:] if r['assessmentEligible']],'assessment200':[r for r in rows if r['assessmentEligible']],'currentProduction125':rows[:125],'remaining175':rows[125:]}
for name,subset in sets.items():
 p=pub['pools'][name];assert p['count']==len(subset) and p['levels']==dict(collections.Counter(r['requiredLevel'] for r in subset))
 for k in rt['domainTitles']:
  levels={lv:sum(am[r['id']]['uiDomain']==k and r['requiredLevel']==lv for r in subset) for lv in ['junior','middle','senior','head']};assert levels==p['uiDomainByLevel'][k] and sum(levels.values())==p['uiDomains'][k]
 for k in rt['thinkingTitles']:
  ps1=[r['id'] for r in subset if am[r['id']]['primaryThinking']==k and k!='context'];ss=[r['id'] for r in subset if k in am[r['id']]['secondaryThinking'] and k!='context'];us=[r['id'] for r in subset if k in am[r['id']]['normalizedWeights']]
  assert eq(dict(primaryCaseIDs=ps1,secondaryCaseIDs=ss,unionCaseIDs=us,primaryCaseCount=len(ps1),secondaryCaseCount=len(ss),unionCaseCount=len(us),normalizedEvidenceWeightSum=sum(am[i]['normalizedWeights'][k] for i in us)),p['thinking'][k])
r=dict(status='PASS',scope='Independent cumulative manifest merge and actual Swift coverage verification. Working authoring base and scoped Batch 05 preparation only.',candidatePath=str(mf),candidateSHA256=h(mf),acceptedAsWorkingBase=True,readyToFreeze=False,importEligible=False,changedRows=ids,unchangedRows=269,changedFamilies=families,unchangedFamilies=41,changedCompactDesigns=families,remainingUnresolvedIDs=rem,remainingUnresolved=59,gates={'projectionMerge':'Exact match for six independently accepted rows, two whole families and two compact designs. Identical order and membership; both CSVs agree field by field, including nested JSON and eligibility.','unresolved':'65 accepted C04 unresolved minus exactly six reconstructed IDs. No extra exclusions.','runtime':'Reconstructed the 300 inputs from current production gold and approved C05 rows; real production125 agrees on every mapping input. Compiled the current production model/mapping/engine with ScoringFixtures and RuntimeAudit, repeated 300 impulses, reproduced published output and all seven pool aggregates. Exactly TC-135 changes from C04.','head':'Identical to independently reproduced prior baseline: 200 eligible items, eight breadth domains, no excluded metadata; maximum synthetic Head. This is structural reachability under perfect responses.'},TC135={'old':bm['TC-135'],'new':am['TC-135']},headFeasibility=rt['headFeasibility'],remainingIssueIDs=[],severityCounts=dict(blocker=0,major=0,minor=0),inputs={**hashes,**pub['sourceHashes'],str(priorq):h(priorq),'InteractiveBook/TrainerContent/cases.json':h('InteractiveBook/TrainerContent/cases.json')},outputHashes={str(x):h(x) for x in [*sorted(d.glob('*')),q/'runtime-reproduced.json']},productionChanged=False,limitations=['No global freeze or import. This audit addresses cumulative blueprint and structural scoring coverage; release of any batch additionally requires its full-case QA and application regression.'])
(q/'QA-verdict.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(h(mf),h(q/'QA-verdict.json'))
