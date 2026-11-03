from pathlib import Path as P
import json,hashlib,collections
j=lambda f:json.loads(P(f).read_text())
h=lambda f:hashlib.sha256(P(f).read_bytes()).hexdigest()
q=P(__file__).parent;t=P('agent-artifacts/test-bank/batch-05-completion05');p=P(str(t)+'-r2')/'cases.json'; cs=j(p)['cases'];orig=j(t/'cases.json')['cases'];ln=j(t/'lineage.json'); ids=[c['id'] for c in cs];assert ids==[f'TC-{i:03}' for i in range(126,151)]
index=j('agent-artifacts/project-completion/accepted-full-cases.json')['cases'];proj=P('agent-artifacts/manifests/batch-05-scoped-candidate/batch05-projection.json');pr=j(proj)
for k in ['baseline','approvedBlueprintSource']:assert h(pr[k]['path'])==pr[k]['sha256']
m=j(pr['approvedBlueprintSource']['path']);fs={x['scenarioFamilyId'] for x in cs if x.get('scenarioFamilyId')};assert len(fs)==4
for k in ('manifest','familyManifest','changedFamilyDesigns','headAudit'):
 assert pr[k]==[r for r in m[k] if (r['plannedId'] in ids if k in ('manifest','headAudit') else r['scenarioFamilyId'] in fs)]
refs={};log={};cat={r['id']:r for r in j('InteractiveBook/TrainerContent/topics.json')['topics']};html=P('InteractiveBook/WebContent/index.html').read_text()
texts={};dups=collections.defaultdict(list)
for c,o,row in zip(cs,orig,pr['manifest']):
 i=c['id'];la=next(x for x in index if x['id']==i and x['candidate']==ln[i]);assert h(ln[i])==la['sha256'] and h(la['qa'])==la['qaSHA256'] and la['contentAccepted'];refs[ln[i]]=h(ln[i]);refs[la['qa']]=h(la['qa']);raw=next(r for r in j(ln[i])['cases'] if r['id']==i)
 changes=[];assert {k:v for k,v in raw.items() if k not in ['revision','options']}=={k:v for k,v in o.items() if k not in ['revision','options']}=={k:v for k,v in c.items() if k not in ['revision','options']}
 assert c['topicId'] in cat and cat[c['topicId']]['sectionID']==c['partId'] and f'id="{c["topicId"]}"' in html
 assert row['plannedId']==i and all(c.get(k)==row.get(k) for k in ('topicId','partId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible'))
 for a,b in zip(raw['options'],o['options']):
  assert {k:v for k,v in a.items() if k!='whyNotBest'}=={k:v for k,v in b.items() if k!='whyNotBest'}
  if a['whyNotBest']!=b['whyNotBest']:changes.append(a['id'])
 assert o['revision']==raw['revision']+bool(changes)
 minid={x['reasoningPattern']:x for x in o['options']};assert len(minid)==4
 for x in c['options']:
  y=minid[x['reasoningPattern']];assert {k:v for k,v in x.items() if k not in ['id','text']}=={k:v for k,v in y.items() if k not in ['id','text']}
  if x['text']!=y['text']:texts[i]=x['id'];assert x['isBest']
  dups[('option',x['text'])].append((i,c.get('scenarioFamilyId')))
 dups[('context',c['context'])].append((i,c.get('scenarioFamilyId')));dups[('question',c['question'])].append((i,c.get('scenarioFamilyId')))
 assert (c['revision']==o['revision']+1 if c!=o else c['revision']==o['revision'])
 log[i]=dict(acceptedLineage=ln[i],qa=la['qa'],topic=c['topicId'],changedWhyNotBestOriginalIDs=changes,best=next(x['id'] for x in c['options'] if x['isBest']))
assert sum(len(v['changedWhyNotBestOriginalIDs']) for v in log.values())==87 and sum(bool(v['changedWhyNotBestOriginalIDs']) for v in log.values())==22
assert set(texts)=={'TC-138','TC-139','TC-141','TC-142','TC-143','TC-149'}
assert all(len(g)==1 or len({fam for _,fam in g})==1 and g[0][1] for g in dups.values())
for fam in fs:
 members=[c for c in cs if c.get('scenarioFamilyId')==fam];assert all([x['reasoningPattern'] for x in r['options']]==[x['reasoningPattern'] for x in members[0]['options']] or [x['id'] for x in r['options']]==['A','B','C','D'] for r in members)
metrics=j(p.parent/'validation/batch-metrics.json');assert metrics['hashes']['cases']==h(p) and metrics['hashes']['manifest']==pr['approvedBlueprintSource']['sha256'];assert j(p.parent/'validation/runtime-loader.json')['runtime']=='PASS'
evidence={'caseLineage':log,'hashes':refs,'R2TextChanges':texts}; (q/'lineage-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
r=dict(status='FIX REQUIRED',scope='Independent assembled content and scoped projection. Surface heuristics separately reviewed.',candidatePath=str(p),candidateSHA256=h(p),acceptedCaseIDs=[i for i in ids if i!='TC-141'],remainingCaseIDs=['TC-141'],remainingIssueIDs=['ASSEMBLED05-141-A'],severityCounts=dict(blocker=0,major=1,minor=0),inputs={str(f):h(f) for f in [proj,pr['approvedBlueprintSource']['path'],pr['baseline']['path'],t/'cases.json',t/'lineage.json','InteractiveBook/WebContent/index.html','InteractiveBook/TrainerContent/topics.json',q/'lineage-evidence.json']},gates={
'lineage':'All 25 accepted original case and verdict hashes confirmed. Original→R1: 87 whyNotBest fields in 22 cases and only their revision increments. TC-135/145/146 unchanged. Inherited blind choices by action identity. R2→R1: 9 cases consistently permuted within four families, six new keyed texts in standalones, revision +1 for each affected case. No scoring, WHEN, trace or manifest identity changes.',
'whyNotBest':'All 87 reviewed against option and scenario. TC126–128: total-cost lines cross at 2.5,32,48; 126.A comparative refers to duty versus weekly, not perpetual optimum. 129–130: break-even cancellation 20; 131–132: queue, ready suite, equivalent manual coverage and hourly bypass. 133–134: conditional authority and indivisible intervals. 136–140: data boundary, incentives, launch horizon and budget, same-order acceptance, access exception capacity. 141–144: whole-period staffing regime, indivisible quarterly portfolio, launch authority, transactional durability. 147–150: leadership capacity, bounded useful hours, precollection necessity, ownership/contract versus deployment. No changed whyNotBest overturns its best, score, or source evidence.',
'R2VisibleAnswers':'TC-138 preserves acceptance, internal training and separate acceleration. TC-139 gives one owner for acceptance of one end-to-end order after local checks. TC-142 protects mandatory work and selects incident remediation. TC-143 keeps flag off pending owner decision using readiness report. TC-149 keeps owner justification before collection, exceptions and sampling. TC-141 needs local fix below.',
'sourceAndBlueprint':'Part/topic, classification, eligibility and families matched all 25 C05 rows and source catalogue/article IDs. Unchanged approved source traces inherited; new field explanations draw on conditions supplied by each case.',
'scopedProjection':'Exact ordered C05 subsets for all 25 rows, 4 families, 4 compact designs and scoped Head audit. Frozen base and working source references/hash match. No actual freeze performed.',
'duplication':'No repeated exact context, question or option across unrelated cases. Semantic cross-check: 126–128 routing vs 131–132 test readiness vs 148 useful capacity; 133/134 dependency-conditioned approval vs 140 risk delegation vs 143 explicit launch ownership; 135 precedence cycle vs 139 end-to-end verification vs 144 durable send intent vs 150 module ownership. 136 institutionalizes an evidence path; 137 corrects incident incentives, 149 corrects data collection before launch. No new duplicate decision. Previous source/analog QA retained.',
'runtime':'R2 exact candidate Swift/schema PASS. Surface statistics outside this review.'},issues=[{'id':'ASSEMBLED05-141-A','caseID':'TC-141','field':'options.A.text','evidence':'The full-credit action now chooses the forecast after duty is assigned. In the 6–8 week dedicated-team branch duty will not be assigned. The original accepted action was triggered by a decision ABOUT duty, which covers both outcomes.','minimalFix':'Use «после решения о дежурстве» or «когда станет известен режим команды»; retain two conditional reserves and one final plan.','requiredRetest':'Both staffing outcomes produce a final forecast; exact delta and revised candidate hash.'}],importEligible=False,freezePerformed=False)
(q/'QA-verdict.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(h(p),h(q/'QA-verdict.json'))
