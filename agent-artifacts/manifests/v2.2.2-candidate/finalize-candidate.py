exec((__import__('pathlib').Path(__file__).parent/'build-candidate.py').read_text().split('protected=')[0])
m=read(P/'working-master.json');base=read(B/'production_manifest_masterplan_v2_2_1.json');audit=read(P/'runtime-output.json');mapped={r['id']:r for r in audit['rows']};oldrows={r['plannedId']:r for r in base['manifest']};rows=m['manifest'];allowed={'TC-076','TC-077','TC-078','TC-079','TC-080','TC-087','TC-088','TC-091','TC-093'};af={'F-DR-T01','F-TD-P01'}
for r in rows:
 x=mapped[r['plannedId']];v=dict(derivedRuntimeUiDomain=x['uiDomainTitle'],derivedRuntimePrimaryThinking=x['primaryThinking'],derivedRuntimeSecondaryThinking=x['secondaryThinking'])
 if r['plannedId'] in allowed:r.update(v)
 else:assert all(r[k]==value for k,value in v.items())
# Synchronize only two redundant family summaries; all other summaries remain byte-equivalent as JSON values.
families={f['scenarioFamilyId']:f for f in m['familyManifest']}
for f in m['changedFamilyDesigns']:
 if f['scenarioFamilyId'] in af:
  actual=families[f['scenarioFamilyId']];f.update(status='targeted-collision-redesign-v2.2.2-candidate',singleLogicalVariable=actual['singleLogicalVariable'],expectedStrongestShiftConcept=actual['expectedStrongestShiftConcept'])
def counts(rs,key):return dict(sorted(collections.Counter(r[key] for r in rs).items()))
def coverage(group):
 domains={d:0 for d in audit['domainTitles']};matrix={d:{l:0 for l in ['junior','middle','senior','head']} for d in domains};thinking={p:dict(primaryCaseIDs=[],secondaryCaseIDs=[],unionCaseIDs=[],normalizedEvidenceWeightSum=0.) for p in audit['thinkingTitles']}
 for r in group:
  x=mapped[r['id']];d=x['uiDomain'];domains[d]+=1;matrix[d][r['requiredLevel']]+=1
  if x['primaryThinking']!='context':thinking[x['primaryThinking']]['primaryCaseIDs'].append(r['id'])
  for p in set(x['secondaryThinking'])-{'context'}:thinking[p]['secondaryCaseIDs'].append(r['id'])
  for p,w in x['normalizedWeights'].items():thinking[p]['unionCaseIDs'].append(r['id']);thinking[p]['normalizedEvidenceWeightSum']+=w
 for v in thinking.values():
  v.update(primaryCaseCount=len(v['primaryCaseIDs']),secondaryCaseCount=len(v['secondaryCaseIDs']),evidenceCaseCount=len(v['unionCaseIDs']),normalizedEvidenceWeightSum=round(v['normalizedEvidenceWeightSum'],10));assert set(v['unionCaseIDs'])==set(v['primaryCaseIDs'])|set(v['secondaryCaseIDs'])
 return dict(caseCount=len(group),levels=counts(group,'requiredLevel'),uiDomains=domains,uiDomainByLevel=matrix,seniorPlusHeadByUiDomain={d:v['senior']+v['head'] for d,v in matrix.items()},thinking=thinking)
inp=read(P/'runtime-input.json');allrows=inp['rows'];gold=allrows[:25];new=allrows[25:];assessment=[r for r in allrows if r['id'] in inp['assessmentIDs']];assert len(allrows)==300 and len(assessment)==200
cov=copy.deepcopy(base['coverageSummary'])
for k,g in [('gold',gold),('new',new),('all300',allrows),('newAssessment',[r for r in new if r['assessmentEligible']]),('assessment200',assessment)]:
 cov[k]=coverage(g)
 for field in ['caseCount','levels','uiDomains','uiDomainByLevel','seniorPlusHeadByUiDomain']:assert cov[k][field]==base['coverageSummary'][k][field]
assert cov['gold']==base['coverageSummary']['gold']
for k,v in audit['headFeasibility'].items():
 if isinstance(v,list):assert set(v)==set(cov['headFeasibility'][k])
 else:assert v==cov['headFeasibility'][k]
cov['engineWeightVerification']=audit['engineWeightVerification'];cov['status']='candidate technical-validation-PASS; independent-manifest-QA-pending'
for name,h in cov['runtimeContract']['sourceHashes'].items():assert sha(R/'InteractiveBook/Trainer'/name)==h
m['coverageSummary']=cov;m['manifestVersion']='2.2.2-targeted-collision-revision-candidate'
changed=[r['plannedId'] for r in rows if r!=oldrows[r['plannedId']]];assert set(changed)==allowed
oldf={f['scenarioFamilyId']:f for f in base['familyManifest']};changedf=[f['scenarioFamilyId'] for f in m['familyManifest'] if f!=oldf[f['scenarioFamilyId']]];assert set(changedf)==af
frozenfields=['plannedId','batch','block','partId','topicId','domain','requiredLevel','structure','scenarioFamilyId','familyPosition','trainingEligible','assessmentEligible','futureContextSensitivityCandidate']
assert all(all(r[k]==oldrows[r['plannedId']][k] for k in frozenfields) for r in rows)
assert len(rows)==len({r['plannedId'] for r in rows})==275 and {r['plannedId'] for r in rows}=={f'TC-{n:03}' for n in range(26,301)}
assert counts(rows,'structure')==dict(pair=70,standalone=181,triplet=24);assert len(families)==43
assert collections.Counter(f['type'] for f in families.values())==dict(pair=35,triplet=8)
assert len(counts(rows,'batch'))==11 and all(v==25 for v in counts(rows,'batch').values())
assert all(r['trainingEligible'] and r['assessmentEligible']==(r['structure']=='standalone') for r in rows)
by={r['plannedId']:r for r in rows};topics={t['id']:t['sectionID'] for t in read(R/'InteractiveBook/TrainerContent/topics.json')['topics']};assert all(topics[r['topicId']]==r['partId'] for r in rows)
for f in families.values():
 members=[by[id] for id in f['memberIds']];assert len({(r['batch'],r['topicId'],r['domain'],r['requiredLevel']) for r in members})==1
 assert all(r['scenarioFamilyId']==f['scenarioFamilyId'] and r['topicId']==f['topicId'] and r['requiredLevel']==f['requiredLevel'] for r in members)
 assert [r['familyPosition'] for r in members]==list(range(1,len(members)+1))
 if f['scenarioFamilyId'] in af:
  assert all(r['decisiveMutationConcept']==f['stateByMember'][r['plannedId']] and r['oneSentenceDecisionBoundary']==f['decisionBoundaryByState'][r['plannedId']] for r in members)
  assert all(r['oneSentenceScenarioConcept'].startswith(f['baseSituation']) for r in members)
b3=[r for r in rows if r['batch']=='Batch 03'];assert counts(b3,'requiredLevel')==dict(head=3,junior=5,middle=12,senior=5)
assert counts(b3,'structure')==dict(pair=6,standalone=16,triplet=3)
# Exact changed fields and values, including complete family contract edits.
log=[]
for r in rows:
 if r['plannedId'] in allowed:
  a=oldrows[r['plannedId']];keys=[k for k in r if r[k]!=a[k]];log.append(dict(entityType='row',ID=r['plannedId'],issue='Batch03 semantic collision; includes controlled-family siblings',fieldsChanged=keys,before={k:a[k] for k in keys},after={k:r[k] for k in keys},whyFixed='Different diagnostic boundary grounded in same textbook topic; see duplication-audit-v2_2_2.csv and source-trace.json.'))
for id in changedf:
 a=oldf[id];b=families[id];keys=[k for k in b if a.get(k)!=b[k]];log.append(dict(entityType='family',ID=id,issue='Redesign whole family to preserve controlled mutation while removing collision',fieldsChanged=keys,before={k:a.get(k) for k in keys},after={k:b[k] for k in keys},whyFixed='One logical variable, constant strategy space, distinct strongest states and explicit boundaries; see family-proof.json.'))
csvwrite('change-log-v2_2_1-to-v2_2_2.csv',log)
meta=dict(status='READY FOR MANIFEST QA',baseline='v2.2.1',fixedOriginalBlockers=6,remainingOriginalBlockers=0,changedRows=changed,unchangedRows=266,changedFamilies=changedf,unchangedFamilies=41,unchangedTopicLevelDomainEligibility=True,unexpectedRegression=0,runtimeVocabulary='PASS: compiled production Swift mapping',runtimeEngineWeights=audit['engineWeightVerification'],headFeasibility=cov['headFeasibility'],familyConsistency='PASS',structuralInvariants='PASS',planned=dict(newCases=275,standalone=181,linked=94,pairs=35,triplets=8,batches=11,casesPerBatch=25),batch03=dict(cases=25,standalone=16,linked=9,families=4,levels=counts(b3,'requiredLevel')),crossBankNearest=dict(NO_CLOSE_ANALOG=0,ALLOWED_REINFORCEMENT=9,NEAR_DUPLICATE=0,DUPLICATE=0),internalBatch03=dict(pairs=300,duplicates=0,nearDuplicates=0),unresolvedIDs=[],readyForManifestQA=True,authoringStarted=False,productionChanged=False,scopeNote='Only nine rows, two contracts and their redundant summaries, version/provenance and derived thinking coverage changed. Semantic judgments are author self-review; independent manifest QA remains required.')
m['targetedRevisionV2_2_2']=meta
write('production_manifest_masterplan_v2_2_2_candidate.json',m);csvwrite('production_manifest_TC026_TC300_v2_2_2_candidate.csv',rows);csvwrite('linked_family_manifest_v2_2_2_candidate.csv',m['familyManifest']);write('runtime_coverage_v2_2_2_candidate.json',cov);write('validation-result.json',meta)
assert all(sha(R/p)==h for p,h in read(P/'protected-input-hashes.json').items())
# Report both original diagnosis and new judgment for every blocker, with economics proof.
(P/'manifest-hotfix-report.md').write_text('''# Manifest v2.2.2 candidate — targeted Batch 03 collision revision

READY FOR MANIFEST QA: YES (author self-verdict; not independent QA, not import approval).

Все шесть preflight defects перепроверены по актуальным production context/options/mentalModel и исходным concepts/facts/boundaries. Подтверждены: 076↔047 и 088↔016 NEAR DUPLICATE; 079↔011, 087↔019, 091↔013, 093↔006 DUPLICATE. Доказательства, включая candidate failure modes: original-collision-recheck.json. Лексическое совпадение не использовалось как достаточное основание. DISPUTED: нет.

## Что теперь измеряется

- **076 / F-DR-T01**: вместо ненадёжного сигнала и warning — судьба необязательной проверки по доказанной пользе и полной цене процесса. 047 определяет готовность scanner к блокировке; новые 076/077/078 удаляют, автоматизируют либо сохраняют полезный ручной шаг. Выбран вариант B — новая ось в той же t-3-2; Middle сохранён.
- **079 / F-TD-P01**: вместо versioned migration семи клиентов — допустимость асинхронного подтверждения по смыслу API-ответа. 011 выбирает сосуществование версий; новая пара различает подтверждение результата и подтверждение получения. Junior сохранён, обе технические реализации заранее готовы.
- **087**: 019 отличает человеческий триггер от системных причин. Новый concept отделяет добросовестную ошибку от доказанного сознательного сокрытия; blameless не освобождает от ответственности за второе. Не превращать будущий кейс в наказание за ошибку либо автоматический PIP.
- **088**: 016 требует сначала подготовить impact/ask. Теперь всё подготовлено; второе нарушение договорённости и закрывающееся окно решения требуют своевременной эскалации вместо ещё одного локального круга.
- **091**: 013 превращает типовые заявки в self-service. Новый concept: self-service уже есть, а enabling стала постоянным исполнителем доменных задач; требуется временная facilitation, обучение когортами и выход по доказанной capability с учётом когнитивной нагрузки. Это Senior-перестройка взаимодействия, не название команды.
- **093**: 006 переводит наступивший risk в issue. Новый concept выбирает превентивную меру: дешёвая передача денежного ущерба не уменьшает неприемлемый простой. Сопоставляются стоимость и разные измерения остаточного риска в заданном риск-аппетите; событие не наступило.

## Controlled families

F-DR-T01: одна переменная L — доказанная предотвращаемая потеря за месяц. Чистые эффекты: удалить=0; автоматизировать=0.5L−2; сохранить ручной шаг=L−6. При L=0 получаем 0/−2/−6; при L=6 — 0/1/0; при L=18 — 0/7/12. Strongest различен во всех трёх состояниях; эффективные границы L=4 и L=8, равенства не используются. Стоимости и доля защиты постоянны. Обязательные gates сохраняются, переход бесплатен, остаточный риск всех стратегий допустим, эффект причинно проверен. Поэтому это не повтор расследования before/after из TC-008. Внутреннее отличие от TC-085: частичная полезная защита и цена необязательного процесса, а не достаточность targeted regression перед конкретным релизом.

F-TD-P01: меняется только смысл положительного ответа. Для подтверждения допустимости нужна завершённая проверка — sync. Для согласованного подтверждения получения достаточно принять сообщение — async с отдельным результатом. Время проверки, техническая готовность, честность статуса и отсутствие жёсткого субсекундного SLO одинаковы. Никакого второго изменения зрелости очереди или версии контракта.

## Metadata и runtime

Topic/part, domain, requiredLevel, structure, family membership, eligibility, batches и futureContextSensitivityCandidate сохранены. Patterns изменены только по новому смыслу: 076–078 process-economics + quality-metrics; 079–080 dependency-decoupling + api-contracts; 087 blameless-system-thinking + accountability/postmortem; 091 structural-dependency-reduction + team-topologies/dependency-management; 093 risk-differentiation + mitigation/risk-register. 088 vocabulary сохранён. Неизвестных codes нет.

Derived fields и coverage пересчитаны через скомпилированные текущие production TrainerScoringMapping.swift и TrainerScoringEngine.swift. Технический RuntimeAudit.swift из прежних артефактов используется только как harness, не как content baseline или mapping. Проверены все 300 impulse responses. Primary=1, secondary=0.5, aliases max по категории, нормализация на max(1,sum); context evidence=0. Gold coverage означает только TC-001…025; импортированные 026…075 уже представлены в planned new275, повторно не добавляются. UI-domain/level totals, assessment200 и Head breadth feasibility не изменились; меняется thinking evidence. Head feasibility — структурная проверка синтетическими perfect responses, не оценка учащегося.

## Regression / semantic scan

Изменены 9 rows: 076/077/078/079/080/087/088/091/093 и 2 contracts: F-DR-T01/F-TD-P01; 266 rows и 41 contract неизменны. Две соответствующие redundant summaries в changedFamilyDesigns синхронизированы. Исторические targetedRevision/surgicalHotfix baseline сохранены; текущий статус в targetedRevisionV2_2_2 и validation-result.json.

275 new; 181 standalone; 94 linked; 35 pairs; 8 triplets; 11×25. Batch03: 16 standalone, 9 linked, 4 families; J5/M12/S5/H3. Связи topic/part сверены с production catalog, family consistency и отсутствие split family проверены автоматически. Changelog содержит только девять реально изменённых rows и два contracts, с before/after.

Для 9 изменённых строк ближайшие production-сравнения: 9 ALLOWED REINFORCEMENT, 0 NEAR DUPLICATE, 0 DUPLICATE. Полный inventory 675 сравнений — cross-bank-pairwise-audit.json. Проверены 300 пар внутри Batch03; controlled siblings выделены как допустимое reinforcement. Отдельно различены 087/089 (сознательное сокрытие против подавления reporting), 088/096 (момент готовой эскалации против влияния через trade-off), 091/095 (capability против blocked WIP), 093/098 (мера риска против бюджетной governance). Это concept-stage author review, не независимая оценка будущих options.

Source trace содержит точные положения тех же шести тем index.html. Синтетические числа/сроки — условия blueprint, не цитаты. Production, baseline v2.2.1, preflight, schema и Swift сохранены по SHA-256. Полноценные cases, questions и options не создавались. Не было импорта, commit/push или начала Batch03 authoring.

Remaining blockers: none found in author self-review. Следующий gate — independent manifest QA.
''')
print(json.dumps(meta,ensure_ascii=False,indent=2))
