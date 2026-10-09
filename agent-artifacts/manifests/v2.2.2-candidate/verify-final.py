import json,csv,hashlib,collections
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent/'v2.2.1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(B/'production_manifest_masterplan_v2_2_1.json');b=read(P/'production_manifest_masterplan_v2_2_2_candidate.json');allowed={'TC-076','TC-077','TC-078','TC-079','TC-080','TC-087','TC-088','TC-091','TC-093'};families={'F-DR-T01','F-TD-P01'}
changed={x['plannedId'] for x,y in zip(a['manifest'],b['manifest']) if x!=y};assert changed==allowed
assert len(a['manifest'])==len(b['manifest'])==275
assert {x['scenarioFamilyId'] for x,y in zip(a['familyManifest'],b['familyManifest']) if x!=y}==families
assert {x['scenarioFamilyId'] for x,y in zip(a['changedFamilyDesigns'],b['changedFamilyDesigns']) if x!=y}==families
assert {k for k in a if a[k]!=b.get(k)}=={'manifestVersion','coverageSummary','manifest','familyManifest','changedFamilyDesigns'}
assert set(b)-set(a)=={'targetedRevisionV2_2_2'}
def encoded(v):return json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else 'true' if v is True else 'false' if v is False else '' if v is None else str(v)
for stem,key,idfield in [('production_manifest_TC026_TC300','manifest','plannedId'),('linked_family_manifest','familyManifest','scenarioFamilyId')]:
 old=list(csv.DictReader((B/(stem+'_v2_2_1.csv')).open(encoding='utf-8-sig')));new=list(csv.DictReader((P/(stem+'_v2_2_2_candidate.csv')).open(encoding='utf-8-sig')))
 assert len(new)==len(b[key]);assert set(new[0])==set(old[0])
 for flat,obj in zip(new,b[key]):assert all(flat[k]==encoded(obj.get(k)) for k in flat),(idfield,obj[idfield])
 assert {x[idfield] for x,y in zip(old,new) if x!=y}==(allowed if key=='manifest' else families)
# Independent reconstruction of weights from authoritative audit categories.
rt=read(P/'runtime-output.json');mp={x['id']:x for x in rt['rows']};inp=read(P/'runtime-input.json');cov=read(P/'runtime_coverage_v2_2_2_candidate.json');assert cov==b['coverageSummary']
groups={'gold':inp['rows'][:25],'new':inp['rows'][25:],'all300':inp['rows'],'newAssessment':[r for r in inp['rows'][25:] if r['assessmentEligible']],'assessment200':[r for r in inp['rows'] if r['id'] in inp['assessmentIDs']]}
for name,rows in groups.items():
 totals=collections.defaultdict(float);primary=collections.defaultdict(set);secondary=collections.defaultdict(set);union=collections.defaultdict(set)
 for r in rows:
  x=mp[r['id']];w={};p=x['primaryThinking']
  if p!='context':w[p]=1.;primary[p].add(r['id'])
  for p in x['secondaryThinking']:
   if p!='context':w[p]=max(w.get(p,0),.5);secondary[p].add(r['id'])
  den=max(1,sum(w.values()))
  for p,v in w.items():totals[p]+=v/den;union[p].add(r['id'])
 for p,v in cov[name]['thinking'].items():
  assert set(v['primaryCaseIDs'])==primary[p] and set(v['secondaryCaseIDs'])==secondary[p] and set(v['unionCaseIDs'])==union[p]
  assert abs(v['normalizedEvidenceWeightSum']-totals[p])<1e-8
 for p,v in cov[name]['thinking'].items():
  old=a['coverageSummary'][name]['thinking'][p]
  for k in ['primaryCaseIDs','secondaryCaseIDs','unionCaseIDs']:assert (set(v[k])^set(old[k]))<=allowed
# Strict uniqueness of triplet utility maxima, not just different labels.
proof=read(P/'family-proof.json')['F_DR_T01'];expected=['remove','automate','manual']
for value,winner in zip(['0','6','18'],expected):
 utilities=proof['strategyNetValues'][value];assert max(utilities,key=utilities.get)==winner;assert sum(v==max(utilities.values()) for v in utilities.values())==1
assert len(read(P/'cross-bank-pairwise-audit.json')['comparisons'])==675
assert len(read(P/'internal-batch03-audit.json')['comparisons'])==300
assert all(x['classification'] not in ['NEAR DUPLICATE','DUPLICATE'] for x in read(P/'cross-bank-pairwise-audit.json')['comparisons'])
protected=read(P/'protected-input-hashes.json');assert all(sha(R/p)==h for p,h in protected.items()),'Protected inputs changed'
assert not (R/'agent-artifacts/test-bank/batch-03/cases_TC076_TC100.json').exists()
write(P/'final-regression-check.json',dict(status='PASS',method='Separate structural/CSV/coverage assertions; not independent semantic QA.',changedRows=sorted(changed),unchangedRows=266,changedFamilies=sorted(families),unchangedFamilies=41,csvJsonConsistency='PASS',unexpectedRegression=0,coverageRecomputedIndependently=True,tripletUniqueMaxima=True,protectedInputsUnchanged=True,authoringStarted=False))
required=['production_manifest_masterplan_v2_2_2_candidate.json','production_manifest_TC026_TC300_v2_2_2_candidate.csv','linked_family_manifest_v2_2_2_candidate.csv','manifest-hotfix-report.md','change-log-v2_2_1-to-v2_2_2.csv','duplication-audit-v2_2_2.csv','runtime_coverage_v2_2_2_candidate.json','validation-result.json']
assert all((P/n).is_file() for n in required)
write(P/'artifact-hashes.json',{p.name:sha(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
assert all(sha(P/n)==h for n,h in read(P/'artifact-hashes.json').items())
print('PASS: scope, CSV/JSON, coverage, family maxima, protected inputs, required artifacts and hashes')
