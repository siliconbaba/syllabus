#!/usr/bin/env python3
"""Index the approved 100-case baseline. Future approvals require explicit registry extension."""
import argparse,hashlib
from common import *
def main():
 p=argparse.ArgumentParser();p.add_argument('--production',default=str(PRODUCTION));p.add_argument('--output',required=True);a=p.parse_args()
 expected='6becf4f8ccdb914e9ebd51ca780902174ecdd7914824408139b40477cd25c6a3'
 if sha(a.production)!=expected:raise ValueError('Unknown approval baseline; add verified QA/import lineage before indexing a new bank')
 raw=raw_cases(a.production);cases=read(a.production)['cases'];index=[]
 for c in cases:
  n=int(c['id'][3:]);batch=(n-1)//25
  qa=None if batch==0 else f'agent-artifacts/qa/batch-{batch:02}'+('-r2' if batch==1 else '-r3')+'/QA-verdict.json'
  imp=f'agent-artifacts/work-imports/batch-{max(batch,1):02}/import-report.md'
  basis=('User-confirmed GOLD-STANDARD READY; original full independent QA verdict is not available in repository. Gold fixture + import regression prove preservation, not a new semantic audit.' if batch==0 else 'Conditional independent QA followed by authorized local TC-045 fix and successful import. The QA verdict predates that local fix; do not describe it as unconditional final QA.' if batch==1 else 'Focused independent QA plus inherited unchanged-case approvals and successful import.')
  if batch:
   filename={1:'batch-01-r2/cases_TC026_TC050_r2.json',2:'batch-02-r3/cases_TC051_TC075_r3.json',3:'batch-03-r3/cases_TC076_TC100_r3.json'}[batch]
   approved=next(x for x in read(ROOT/'agent-artifacts/test-bank'/filename)['cases'] if x['id']==c['id'])
   if approved!=c:raise ValueError('Approved source mismatch '+c['id'])
  else:
   original=next(x for x in read(ROOT/'Tests/Fixtures/trainer-gold-v1.json')['cases'] if x['id']==c['id'])
   # v1 fixtures can already contain type; compare exactly their original keys.
   if {k:c.get(k) for k in original}!=original:raise ValueError('Gold semantic regression '+c['id'])
  refs=[imp]+([qa] if qa else ['Tests/Fixtures/trainer-gold-v1.json'])
  index.append({'id':c['id'],'contentHash':canonical(c),'rawObjectSha256':hashlib.sha256(raw[c['id']]).hexdigest(),'hashMethod':'canonical sorted JSON UTF-8; rawObjectSha256 is exact object span','productionStatus':'APPROVED_PRODUCTION_BASELINE','lastApprovedQAArtifact':qa,'approvalBasis':basis,'evidenceHashes':{s:sha(ROOT/s) for s in refs},'manifestVersion':{0:'gold precedes planned manifest',1:'v2.2',2:'v2.2.2',3:'v2.2.3'}[batch],'currentAuthoritativeManifest':'v2.2.3','level':c['requiredLevel'],'topic':c['topicId'],'domain':c['domain'],'patterns':[c['primaryPattern']]+c['secondaryPatterns'],'familyId':c.get('scenarioFamilyId'),'assessmentEligible':c['assessmentEligible'],'inheritanceRule':'Exact content hash match + unchanged source/runtime/manifest semantics + verified evidence. New cross-bank duplication relationships still require QA.'})
 write(Path(a.output)/'approved-case-evidence.json',{'productionSha256':expected,'cases':index,'contextHashes':{str(p):sha(p) for p in [BOOK,CATALOG,ROOT/'docs/TRAINER-CONTENT-SCHEMA.md',ROOT/'InteractiveBook/Trainer/TrainerScoringMapping.swift',ROOT/'InteractiveBook/Trainer/TrainerScoringEngine.swift']},'scope':'Historical accepted production lineage, not a new independent QA verdict; null QA artifact is intentional.'})
 summary(a.output,indexedCases=len(index),provenanceLimitations=['Gold full QA verdict not local','Batch 01 conditional QA + authorized local fix recorded by import'])
if __name__=='__main__':entry(main)
