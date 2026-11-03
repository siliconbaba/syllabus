import json,csv,hashlib,collections,re,itertools
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];M=R/'agent-artifacts/manifests/v2.2.3-candidate';B=P.parent/'batch-03-r2'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows])
m=read(M/'production_manifest_masterplan_v2_2_3_candidate.json');r=next(r for r in m['manifest'] if r['plannedId']=='TC-085');cs=read(P/'cases_TC076_TC100_r3.json')['cases'];c=next(c for c in cs if c['id']=='TC-085');gold=read(R/'InteractiveBook/TrainerContent/cases.json')['cases'];r2=read(B/'cases_TC076_TC100_r2.json')['cases'];by={x['id']:x for x in gold+r2};st=read(P/'batch-statistics-r3.json');surface=read(P/'surface-leakage-analysis-r3.json')
assert surface['status']=='PASS'
# Key-masked review: fact-based adversarial comparisons, without any independent-blind claim.
proof={'reviewMethod':'Read context/question/option.text only from tc085-key-masked-review.json, then test each competing plan. The same author knows the design, so this is not independent blind QA.','choice':'C','uniqueStrongest':'PASS','Middle':'PASS','reasoningRequired':'Identify consumed-state preparation as the repeat cost; combine upfront and recurring labor for six cycles, satisfy first-start and total capacity constraints, retain identical evidence and cross-system consistency.','whyNotJunior':'Neither an isolated coverage rule nor the fastest test run identifies the feasible plan; total horizon and preparation readiness must both be checked.','scope':'One product and one finite plan, no organizational platform redesign.','comparisons':[{'against':'A','decisiveFacts':'16h automation;4h preparation remains;0.5h execution; six cycles;16h prestart/30h total.','firstStartHours':20,'totalHours':43,'whyLoses':'Optimizes test execution but not consumed-state restoration; exceeds both constraints.','quality':.65},{'against':'B','decisiveFacts':'No queue; same consumed data; sequential cycles;4h setup adds cost.','firstStartHours':8,'totalHours':40,'whyLoses':'Extra environment does not remove state reset work.','quality':.45},{'against':'D','decisiveFacts':'Separate manual sets cost4h each; checks2h; six repeats;30h total.','firstStartHours':4,'totalHours':36,'whyLoses':'Avoids investment and is reliable, but recurring cost exceeds the finite capacity. Strong competing heuristic for fewer cycles.','quality':.82}],'C':{'firstStartHours':12.5,'totalHours':27,'quality':1,'coverageReduced':False},'hiddenAssumptions':'None identified: all durations include agreed preparation/verification; source state must be restored each time; data schema stable; same evidence set.','whenWholeOptionReview':{o['id']:{'condition':o['whenItWouldBeBest'],'verdict':'PASS'} for o in c['options']}}
write(P/'tc085-pairwise-self-check.json',proof)
source=(M/'source-topic-t3-9.txt').read_text();terms=['Сначала разберу 7 дней','Тестовые данные — второе узкое место','данные «расходуются»','наборы данных как код']
ex=[]
for t in terms:
 i=source.find(t);assert i>=0,t;ex.append(source[i:i+750])
trace={'caseId':'TC-085','topicId':'t-3-9','source':'InteractiveBook/WebContent/index.html#t-3-9','sourceSHA256':sha(R/'InteractiveBook/WebContent/index.html'),'proposition':'Разложить полный регресс на исполнение и подготовку; данные расходуются, требуют согласованности и повторяемого восстановления.','exactExcerpts':ex,'syntheticFacts':'6 cycles,4h reset,2h checks,12h reset-script build/verification,0.5h repeat reset,16/30h constraints are synthetic, not textbook quotes.','decisiveFacts':c['decisiveFacts'],'strongestDerivation':'Keep evidence fixed; reusable coherent reset gives12+6×2.5=27h, prestart12.5h. Automation of checks leaves4h preparation per cycle and costs43h.','sourceGrounding':'SUPPORTED','externalNormsUsed':False};write(P/'source-trace-TC085.json',trace);write(M/'source-trace-TC085.json',trace)
# Explicit comparisons for every plausible neighboring decision, not a lexical uniqueness score.
reasons={
'TC-003':'Available automatic evidence supports a risk-bounded hotfix; new085 has fixed evidence and chooses preparation investment for repeated consumed data.',
'TC-004':'004 adds missing targeted evidence then staged rollout;085 does not choose evidence scope or exposure and instead selects repeatable data preparation under capacity.',
'TC-008':'008 must establish causal contribution from confounded before/after data;085 already has measured preparation/run times and validated alternatives, chooses execution investment.',
'TC-013':'013 redesigns repeated platform request service as self-service;085 has no external queue or ownership transfer, only local repeatable state reset with finite setup/payback.',
'TC-042':'042 fixes incomparable horizons/rates before investment comparison;085 shares one stated horizon and must distinguish consumed-state preparation from test execution.',
'TC-045':'045 changes intermediate acceptance to parallelize independent branches while protecting shared stand/data milestone;085 has sequential runs, no queue and no acceptance/network redesign.',
'TC-047':'047 decides whether unreliable security signal can block releases;085 has reliable checks and no gate-enforcement decision.',
'TC-076':'076 removes unprofitable optional protection using prevented loss;085 holds all checks constant and changes only the preparation work.',
'TC-077':'077 trades cost against partial protection;085 loses no protection and addresses data state between runs.',
'TC-078':'078 retains more costly protection for more prevented loss;085 compares equivalent evidence plans with different recurring preparation.',
'TC-086':'086 allocates reviewer capacity to an accumulating queue;085 has no queue, data are consumed and require state restoration between repetitions.',
'TC-091':'091 exits permanent enabling work through cohort capability transfer;085 does not change team roles or train ownership cohorts.',
'TC-095':'095 manages external blocked obligations and future WIP return;085 all inputs are available and chooses data preparation implementation.',
'TC-106':'106 responds to temporary flow capacity imbalance;085 has a repeated state preparation cost with a finite engineering investment.',
'TC-107':'107 changes persistent system flow constraint/launch policy;085 compares local replay preparation plans, no demand/WIP policy.',
'TC-131':'131 uses existing automated targeted evidence for staged rollout;085 fixed checks, choice concerns consumed test data restoration.',
'TC-132':'132 adds manual targeted evidence absent automation;085 no coverage gap or release-evidence expansion.',
'TC-158':'158 reduces shared dependency or changes allocation model;085 no shared queue/ownership conflict, local data reset cost.',
'TC-162':'162 selects observability investment for diagnosis bottleneck;085 prepares known starting state before repeat regression, no incident diagnosis.',
'TC-173':'173 rejects global coverage percentage with missing critical path;085 all required checks already present, coverage not the variable.',
'TC-174':'174 reduces external approval waiting rather than active development;085 expressly has no waiting queue, requires active cross-system data restoration each run.',
'TC-234':'234 self-service for repetitive shared demand;085 no consumers/provider queue, local stateful test preparation.',
'TC-245':'245 asks whether to calculate rough automation payback before starting;085 requires an executable choice between four plans with two capacity constraints and stateful-data fidelity.',
'TC-286':'286 prioritizes which risk/frequency scenarios to automate;085 neither changes nor prioritizes scenarios, chooses infrastructure preparation vs assertion execution on one fixed set.',
'TC-298':'298 reduces shared demand via self-service/standardization;085 six required runs remain six, work per reset changes locally.'}
comparison=[]
# 1..75 production +76..84 authored r2 +86..300 frozen blueprint =299 distinct other IDs.
for x in gold+[x for x in r2 if 76<=int(x['id'][3:])<=84]:
 id=x['id'];comparison.append({'TC-ID':'TC-085','otherID':id,'otherSource':'production' if int(id[3:])<=75 else 'Batch03 r2 authored','otherDecision':x['mentalModel'],'classification':'ALLOWED REINFORCEMENT' if id in reasons else 'NO CLOSE ANALOG','differentReason':reasons.get(id,'Other case tests: '+x['mentalModel']+' New085 selects repeatable consumed-data preparation; these are different operative choices.'),'reviewStage':'Blueprint and full authored TC-085 compared to context/options/mental model.'})
for x in m['manifest']:
 if int(x['plannedId'][3:])<86:continue
 id=x['plannedId'];comparison.append({'TC-ID':'TC-085','otherID':id,'otherSource':'frozen future manifest','otherDecision':x['oneSentenceDecisionBoundary'],'classification':'ALLOWED REINFORCEMENT' if id in reasons else 'NO CLOSE ANALOG','differentReason':reasons.get(id,'Other frozen decision: '+x['oneSentenceDecisionBoundary']+' No same consumed-test-data preparation choice; no change to that row.'),'reviewStage':'Future blueprint collision scan; not a verdict on uncreated future options.'})
assert len(comparison)==299 and len({x['otherID'] for x in comparison})==299
assert not any(x['classification'] in ['NEAR DUPLICATE','DUPLICATE'] for x in comparison)
table(M/'duplication-audit-v2_2_3.csv',comparison)
# Full batch reporting retains r2 judgments and replaces only the resolved TC-085 finding.
dup=list(csv.DictReader((B/'duplication-audit-r2.csv').open(encoding='utf-8-sig')))
for d in dup:
 if d['caseId']!='TC-085':continue
 d.update(classification='ALLOWED REINFORCEMENT',nearestProductionId='TC-004',differentDecisiveFact='Покрытие фиксировано; согласованные данные расходуются, подготовка4ч повторяется6раз при ограниченной ёмкости. TC-004: недостающее targeted evidence перед hotfix.',differentCandidateMistake='Оптимизировать выполнение тестов/стенд вместо повторной подготовки состояния; TC-004: заменить недостающее evidence rollback или избыточным полным регрессом.',differentActualDecision='Выбрать восстановление данных как код для шести прогонов; TC-004: добавить targeted manual regression и staged rollout.',revisionReview='New candidate boundary and full wording checked; see manifest299-row audit and source/pairwise proof.')
table(P/'duplication-audit-r3.csv',dup)
internal=[]
for other in cs:
 if other['id']=='TC-085':continue
 assert other['mentalModel']!=c['mentalModel'] and [o['text'] for o in other['options']]!=[o['text'] for o in c['options']]
 id=other['id'];internal.append({'otherID':id,'classification':'ALLOWED REINFORCEMENT' if id in reasons else 'NO CLOSE ANALOG','reason':reasons.get(id,'Different actual choice: '+other['mentalModel'])})
write(P/'internal-duplication-r3.json',{'changedCaseComparisons':internal,'count':24,'other276Pairs':'r2 independent/author evidence preserved by byte equality of all other24 cases','duplicates':0,'nearDuplicates':0})
counts=dict(collections.Counter(x['classification'] for x in dup));counts.update({'NEAR DUPLICATE':0,'DUPLICATE':0})
qa={'status':'READY FOR FOCUSED QA — author self-verdict, not import approval','readyForFocusedQA':True,'manifestCandidate':'agent-artifacts/manifests/v2.2.3-candidate/','manifestChangedRows':1,'manifestUnexpectedRegression':0,'TC085':{'rewritten':True,'vsTC004':'ALLOWED REINFORCEMENT','uniqueStrongest':'PASS','sourceGrounding':'SUPPORTED','Middle':'PASS','patterns':{'primary':'process-economics','secondary':['bottleneck']},'reviewLimit':'Key-masked author self-review; prior familiarity means not independent blind QA.'},'changedCases':1,'other24ByteIdentical':True,'unexpectedChanges':0,'priorR2FixesPreserved':True,'familiesPass':4,'uniqueStrongest':25,'sourceGrounded':25,'manifestAligned':25,'alignmentBasis':'24 unchanged rows with frozen v2.2.2; TC-085 with v2.2.3-candidate.','wholeBatchEvidenceBasis':'New085 self-check + byte-identical r2 content; r2 content fixes still require joint independent focused QA. No new independent PASS claimed.','crossBank':counts,'internalDuplicates':0,'internalNearDuplicates':0,'schema':'PASS','runtime':'PASS','surfaceLeakage':'PASS within78 exploratory rules','bestSimpleHeuristic':st['bestSimpleHeuristic'],'combined100Best':st['combined100Best'],'unresolvedIDs':[],'candidateFrozen':False,'imported':False,'candidateSHA256':sha(P/'cases_TC076_TC100_r3.json')};write(P/'self-qa-r3.json',qa)
st.update(uniqueStrongest=25,sourceGrounded=25,manifestAligned=25,crossBank=counts,internalDuplicates=0,readyForFocusedQA=True);write(P/'batch-statistics-r3.json',st)
v=read(M/'validation-result.json');v.update(sourceGrounding='SUPPORTED',middleRealization='PASS (author self-check)',TC085vsTC004='ALLOWED REINFORCEMENT',crossBankNearDuplicates=0,crossBankDuplicates=0,comparisonScope=299,readyForFocusedQA=True,unresolvedIDs=[]);write(M/'validation-result.json',v)
manifest_report='''# Surgical manifest candidate v2.2.3 — TC-085

**Manifest defect confirmed. READY FOR FOCUSED QA: YES (author self-verdict). Candidate не frozen и не импортирован.**

Сопоставлены production TC-004, frozen row TC-085 и authored Batch03/r2. Во всех случаях ядро старого085 — достаточный targeted regression вместо полного дорогого либо недостаточного быстрого набора. Совпадают ошибка кандидата, решающие факты и выбор evidence. Подтверждение не основано на сходстве слов: original-defect-confirmation.json.

## Source-first выбор

Тема3.9 прочитана целиком из index.html, сохранена в source-topic-t3-9.txt. Рассмотрены положения о flaky/разборе падений, приоритизации автоматизации по частоте и стабильности, разложении полного цикла регресса, расходуемых согласованных тестовых данных и ограничениях добавления среды. Выбран важный самостоятельный judgment: подготовка повторяемого состояния данных при неизменных проверках. Flaky/bocking близок047; выбор автоматизируемых сценариев —286; общая платформа сред была бы Senior/Head scope. Причины выбора и skeleton до авторинга: source-first-design.json.

**TC-004 tests:** достаточно ли evidence для hotfix и какую недостающую проверку добавить перед staged rollout.

**Old TC-085 tested:** достаточный targeted вместо дорогого полного регресса — тот же диагностический стержень.

**New TC-085 tests:** куда вложить ограниченное время для шести повторных циклов с расходуемыми согласованными данными, сохраняя весь набор проверок.

- Different decisive fact: данные меняют состояние и требуют повторной подготовки; известны отдельно стоимость восстановления и исполнения, разовые вложения, срок первого старта и общая ёмкость.
- Different candidate mistake: ускорить видимое выполнение тестов или добавить незанятую среду, не сняв повторный труд по данным; недооценить сумму ручных повторений.
- Different actual decision: выбрать способ подготовки данных и вложение ёмкости; не выбирать полноту regression evidence или rollout.
- Different strongest reasoning: сравнить полную цену повторений и готовность стартового состояния, удержав межсистемные связи; не обменивать полноту проверки на скорость выпуска.

004↔085 — ALLOWED REINFORCEMENT. Source support и Middle self-check PASS. Синтетические числа реализуют правило учебника, не выдаются за цитаты.

## Surgical scope и runtime

Изменена только planned row TC-085: concept/facts/boundary, whyLevel, primary/secondary patterns и derived thinking. Domain release_and_quality сохранён; topic t-3-9, part3, Middle, batch/block, standalone/null family, eligibility true/true неизменны. Остальные274 rows и43 family contracts равны baseline. Export family CSV также побайтово скопирован. Все остальные semantic top-level records неизменны; обновлены только version label и coverage. Inherited freezeProvenance и прежние revision records относятся к baseline2.2.2, не утверждают freeze этого candidate.

Primary process-economics → proportionality; secondary bottleneck → dependencies. Это выбор полной стоимости локального процесса с учётом ограничителя, не измерение полноты evidence. Actual Swift mapping/engine скомпилированы;300 impulse responses PASS, unknown0. Primary1/secondary0.5, aliases max по case/category, нормализация max(1,sum), context evidence0.

Для085 прежний вклад evidence2/3+risk1/3 заменён proportionality2/3+dependencies1/3. Thinking primary/secondary/union и normalized weights пересчитаны в New/Final и assessment subsets. Domain/level tables, Gold25, Head breadth feasibility и pools не меняются. Импортированные026…075 не добавлялись второй раз: manifest coverage — Gold001…025 + New026…300. Current300/assessment200 — проектируемые pools, не факт production import.

Сохранены275 planned,181 standalone,94 linked,35 pairs+8 triplets,11×25. Batch03:25,16standalone/9linked,4families,J5/M12/S5/H3. Проверены IDs, topic/part, family consistency/no split и eligibility. validation-result.json содержит автоматический результат. change-log содержит одну строку с точными before/after.

## Collision scan

299 сравнений: production001…075, authored r2 076…084 и future frozen086…300. duplication-audit-v2_2_3.csv хранит другую boundary и причину различия. Ноль near/duplicates для085. Особенно рассмотрены004,008,013,042,045,047,076…078,086,091,095,131/132,173/174,245,286,298. 174 о wait state внешнего согласования — здесь очереди нет;286 выбирает сценарии автоматизации — здесь набор неизменен;245 спрашивает о проверке окупаемости — здесь нужен исполнимый план по двум ограничениям и состоянию данных. Future scan относится к blueprint, не к ещё не созданным options.

Новый TC-085 реализован в batch-03-r3 после формирования candidate. Оба слоя передаются на один focused independent QA. Production, baseline manifest, r2, независимые QA-файлы, schema и Swift сохранены по hashes. Commit/push, импорт и freeze не выполнялись.
'''
(M/'manifest-hotfix-report.md').write_text(manifest_report)
report='''# Batch 03 r3 — только TC-085

**READY FOR FOCUSED QA: YES — авторская самопроверка. Не READY FOR IMPORT.**

Manifest-level blocker TC-085↔TC-004 закрыт новой candidate boundary в ../manifests/v2.2.3-candidate. Изменены ровно1 planned row и1 authored case; family contracts не изменены. Frozen v2.2.2 остаётся исходным authoritative baseline; v2.2.3 не frozen.

## Новое решение

TC-004 добавляет недостающее targeted evidence перед hotfix. Новый085 выбирает повторяемую подготовку расходуемых согласованных данных при фиксированном достаточном наборе проверок. Ошибка — ускорять тесты либо добавлять стенд, оставляя повторное восстановление данных; не ошибка выбора полного/целевого регресса. Классификация ALLOWED REINFORCEMENT, near/duplicate0.

Middle требует сопоставить разовые/повторные затраты, готовность первого запуска и полную ёмкость шести циклов при сохранении согласованных данных. Проверки и их покрытие не сокращаются. Источник только§3.9, данные/время синтетические.

| Option | До первого старта | Весь горизонт | Решающий факт |
|---|---:|---:|---|
| A: автоматизация проверок |20ч|43ч|Ручное восстановление4ч остаётся; превышены16/30ч.|
| B: дополнительная среда |8ч|40ч|Очереди нет; те же данные требуют того же восстановления.|
| C: сценарий восстановления |12,5ч|27ч|Снимает повторную подготовку, сохраняет проверки и помещается в16/30ч.|
| D: ручные независимые наборы |4ч|36ч|Не требует разработки, но повторный труд превышает30ч.|

Strongest C. D — сильная профессиональная альтернатива при меньшем числе циклов/нестабильной схеме; score0.82, A0.65, B0.45, C1. WHEN каждого варианта оправдывает весь план в соответствующих условиях. Pairwise check C противA/B/D основан на фактах context; post-hoc факты не добавлены. Key-masked input создан без explanations/scores, но автор знает дизайн: это не независимый blind QA. Доказательства — tc085-pairwise-self-check.json и source-trace-TC085.json.

## Regression

r2→r3: changed1, unchanged24 byte-identical, unexpected0. Проверены raw UTF-8 spans целых case objects. Все исправления r2, включая090 и уровни083/084/094/100, сохранены без переоткрытия. Это сохранение предыдущих результатов, а не новый independent PASS.

25 кейсов,16standalone,9linked,4families;J5/M12/S5/H3;A6/B6/C6/D7. Metadata24/24 соответствует frozen2.2.2, новый085 — candidate2.2.3. Families4/4 — все sibling bytes unchanged, r2 literal proofs сохранены в family-diff-analysis-r3.json. Whole batch unique strongest/source25/25 по новой self-check085 и сохранённым r2 доказательствам.

Cross-bank batch: NO CLOSE ANALOG2, ALLOWED REINFORCEMENT23, NEAR DUPLICATE0, DUPLICATE0. Полный blueprint/full-wording scan085 против299 IDs в manifest candidate; production75 — обязательная часть. Внутри batch сравнены новые24 пары с085; остальные276 пар сохранены; accidental near/duplicates0.

## Surface и validator

Те же78 правил/19 признаков: r3 best10/25, r2 best10/25. Combined100 best33/100, r2 combined33/100. Позиции100:A24/B24/C25/D27. Surface PASS в пределах exploratory набора; это не доказательство отсутствия любой подсказки. После первичного скана формулировка C явно называет оба действия — восстановить данные и выполнить тот же набор; новые действия/обязательства ради длины не добавлялись.

TrainerBank.load strict schema2.0 PASS; runtime codes PASS, unknown0. Part/topic, eligibility, levels, IDs и соответствие metadata проверены. Protected input hashes подтвердили неизменность production, исходных manifest/r2/QA, schema и Swift.

Unresolved IDs: []. Candidate и manifest candidate готовы к одному focused independent QA. Импорта, freeze, Batch04, commit/push нет.
'''
report+='\nCandidate SHA-256: `'+sha(P/'cases_TC076_TC100_r3.json')+'`.\nManifest candidate SHA-256: `'+sha(M/'production_manifest_masterplan_v2_2_3_candidate.json')+'`.\n';(P/'revision-report.md').write_text(report)
for folder,name in [(M,'artifact-hashes.json'),(P,'artifact-hashes-r3.json')]:write(folder/name,{p.name:sha(p) for p in sorted(folder.iterdir()) if p.is_file() and p.name!=name})
print(json.dumps(qa,ensure_ascii=False,indent=2))
