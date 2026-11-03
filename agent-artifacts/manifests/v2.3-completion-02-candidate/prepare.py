from pathlib import Path
import json,hashlib,copy
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
base='agent-artifacts/manifests/v2.3-completion-01-candidate/production_manifest_masterplan_v2_3_completion_01_candidate.json';bqa='agent-artifacts/project-completion/qa-manifest-completion01/QA-verdict.json';m=read(base);bank=read('InteractiveBook/TrainerContent/cases.json')['cases'];original=copy.deepcopy(m);replacements={};approval={};inputs=[base,bqa,'InteractiveBook/TrainerContent/cases.json','InteractiveBook/Trainer/TrainerScoringEngine.swift','InteractiveBook/Trainer/TrainerScoringMapping.swift']
for cid in ['146','272']:
 p=f'agent-artifacts/test-bank/reconstruction/tc{cid}-r1/proposed-manifest-row.json';q=f'agent-artifacts/project-completion/qa-tc{cid}-r1/QA-verdict.json';verdict=read(q)
 assert verdict['candidateSHA256']==sha(p)
 assert verdict['status']=='PASS'
 row=read(p);replacements[row['plannedId']]=row;approval[row['plannedId']]={'candidate':p,'candidateSHA256':sha(p),'qa':q,'qaSHA256':sha(q)};inputs.extend([p,q])
protected=['plannedId','batch','partId','topicId','domain','requiredLevel','structure','scenarioFamilyId','familyPosition','decisiveMutationConcept','trainingEligible','assessmentEligible']
changes=[]
for i,row in enumerate(m['manifest']):
 cid=row['plannedId']
 if cid in replacements:
  n=replacements[cid];assert all(row[k]==n[k] for k in protected)
  changes.append({'id':cid,'fields':{k:{'before':row.get(k),'after':n.get(k)} for k in set(row)|set(n) if row.get(k)!=n.get(k)}});m['manifest'][i]=n
assert len(changes)==2 and m['familyManifest']==original['familyManifest']
remaining=read(bqa)['remainingUnresolvedIDs'];assert set(replacements)<=set(remaining)
m['manifestVersion']='v2.3-completion-02-candidate'
m['completionRevision']={'base':base,'baseSHA256':sha(base),'acceptedRowSources':approval,'closedManifestIDs':sorted(replacements),'remainingUnresolvedIDs':[i for i in remaining if i not in replacements],'remainingUnresolved':len(remaining)-2,'acceptance':'two individual row QA passes; cumulative merge QA pending','readyToFreeze':False,'importEligible':False,'historicalStatusWarning':'Inherited revision/status blocks describe their historical scope. Current unresolved list is completionRevision.remainingUnresolvedIDs, based on completion01 QA minus explicitly approved rows.'}
rows=[{k:c[k] for k in ['id','domain','requiredLevel','primaryPattern','secondaryPatterns','assessmentEligible','trainingEligible']} for c in bank[:25]]
rows +=[{'id':r['plannedId'],**{k:r[k] for k in ['domain','requiredLevel','primaryPattern','secondaryPatterns','assessmentEligible','trainingEligible']}} for r in m['manifest']]
assert len(rows)==300 and len({r['id'] for r in rows})==300
assert sum(r['assessmentEligible'] for r in rows)==200
write('working-master.json',m);write('change-log.json',changes);write('runtime-input.json',{'rows':rows,'template':bank[0],'assessmentIDs':[r['id'] for r in rows if r['assessmentEligible']]});write('input-hashes.json',{p:sha(p) for p in inputs})
print('Prepared two-row cumulative candidate; remaining68; no freeze/import')
