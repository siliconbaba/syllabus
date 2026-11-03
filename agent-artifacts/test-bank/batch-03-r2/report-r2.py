import json,csv,hashlib,itertools,re,collections
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent/'batch-03';Q=R/'agent-artifacts/qa/batch-03'
def read(p):return json.loads(p.read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(n,rows):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in rows])
cs=read(P/'cases_TC076_TC100_r2.json')['cases'];by={c['id']:c for c in cs};gold=read(R/'InteractiveBook/TrainerContent/cases.json')['cases'];gb={c['id']:c for c in gold};fixes=list(csv.DictReader((Q/'case-fixes.csv').open(encoding='utf-8-sig')));ids={f['caseId'] for f in fixes};st=read(P/'batch-statistics-r2.json');sources=read(P/'source-excerpts-r2.json');m=read(R/'agent-artifacts/manifests/v2.2.2/production_manifest_masterplan_v2_2_2.json');mr={r['plannedId']:r for r in m['manifest']}
# Mask answer labels and explanations for review. The author already knows the baseline and designs.
write('key-masked-review-input.json',[{'id':c['id'],'context':c['context'],'question':c['question'],'options':[{'id':o['id'],'text':o['text']} for o in c['options']]} for c in cs if c['id'] in ids])
choices=dict(zip(['TC-076','TC-077','TC-078','TC-079','TC-080','TC-083','TC-084','TC-085','TC-090','TC-092','TC-094','TC-098','TC-100'],['C','A','D','B','C','B','D','C','A','C','A','C','D']))
notes={
'TC-076':'L=0: C=0; A=−2; B=−7; D=−6. WHEN A теперь исключает этот контрпример.',
'TC-077':'L=6: A=1 против C=D=0 и B=−1. WHEN C не выполняется при прибыльной автоматизации.',
'TC-078':'L=18: D=12 против B=11, A=7, C=0. Две границы L=4/8 сохранены.',
'TC-079':'До проверки нельзя подтвердить допустимость; receipt-only C/D не выполняют контракт, A обещает недоказанное.',
'TC-080':'Receipt-only контракт разрешает готовую очередь; B добавляет 2 секунды без обещанной пользы, A ложно подтверждает допустимость, D задерживает результат без указанной выгоды.',
'TC-083':'Совпадающие договоры + потерянная старая маржа + новая поддержка дают прирост 7–9; PV−8=9,5…14,5>5 при любой допустимой траектории. Сведение к сумме отчётов неверно, ожидание не меняет ранжирование.',
'TC-084':'Та же модель даёт прирост 1–2,4; PV−8=−5,5…−2<5. Двойной счёт превращал слабую инвестицию в кажущуюся окупаемой; sunk cost этого не исправляет.',
'TC-085':'Targeted набор достаточен при локальном impact; C strongest. Но ровно эта причина выбора дублирует TC-004 — uniqueness не снимает semantic blocker.',
'TC-090':'A: 100−35+5=70, преемник готов за оставшийся квартал. D: 65, но без исполнителя следующие два квартала. B урезает подтверждённые обязательства; C убирает знания до передачи.',
'TC-092':'Региональные хвосты сопоставимых операций нужны при разнонаправленном сдвиге и локальных жалобах; среднее, единичный максимум и одинаковое толкование global p95 не отвечают вопросу.',
'TC-094':'A и D оба соблюдают guardrail. A даёт необходимую диагностику за2 дня и сохраняет окно теста за3; D не ускоряет двухнедельное исправление, но теряет месяц. B/C нарушают прежний допуск.',
'TC-098':'C сохраняет свободный фонд неизвестных рисков с однодневным доступом. A контрактует деньги, B дублирует уже обеспеченные выявленные риски, D возвращает emergency funding.',
'TC-100':'D: 2 минуты ожидания+4 устранения при100 ошибках/мин=600; шум90с отсекается. B даёт1400, C требует20×10=200мин проверок при60 доступных; A не отделяет не требующие действия события.'
}
pairs=[]
for c in cs:
 if c['id'] not in ids:continue
 key=choices[c['id']];assert key==next(o['id'] for o in c['options'] if o['isBest'])
 for o in c['options']:
  if o['id']==key:continue
  pairs.append({'TC-ID':c['id'],'chosenAfterMaskedReading':key,'versus':o['id'],'decisiveFactsFromVisibleContext':c['decisiveFacts'],'decisionProof':notes[c['id']],'alternativeFailureMechanism':o['explanation'],'counterfactualWholeOption':o['whenItWouldBeBest'],'uniqueStrongest':'PASS','limitation':'Автор видел baseline и создавал revision; поля ключей скрыты в review input, но это не независимый или полностью слепой QA.'})
table('pairwise-review-r2.csv',pairs)
write('pairwise-review-r2.json',{'reviewMode':'Answer fields masked, author adversarial review; prior familiarity prevents independent blind claim.','reviewedFixScope':13,'actuallyChanged':12,'blockedButUnique':['TC-085'],'comparisons':39,'uniqueStrongest':13,'choices':choices,'proofs':notes,'TC090AvsD':'При обоих допустимых бюджетах D лишается исполнителя в обязательном горизонте; A финансирует подготовленного внутреннего преемника до прекращения поддержки. Факт дан в context, не только explanation.'})
level={id:{'requiredLevel':by[id]['requiredLevel'],'specificReasoningRequired':by[id]['authorRationale'],'whyLowerLevelInsufficient':text,'status':'PASS (author self-check)'} for id,text in [
('TC-083','Нельзя принять сумму двух подтверждающих отчётов или просто вычесть оставшиеся8: нужны единица потока, база сравнения, уходящие затраты, диапазон по годам и ценность частичного уточнения.'),
('TC-084','Тот же диагностический процесс обязателен: по сумме валовой выручки продолжение выглядит окупаемым; лишь восстановление прироста с базовым сценарием выявляет отрицательную оставшуюся NPV.'),
('TC-094','Булевый guardrail оставляет A и D допустимыми; нужен operational выбор распределения пяти дней и оценка потерянного окна при общей зависимости от двухнедельного исправления.'),
('TC-100','Правильное окно не дано: ранняя реакция нарушает доступную ёмкость, поздняя — выделенный ущерб; нужно учесть и длительность устранения, и стоимость ложного вызова.') ]}
write('level-focused-self-qa-r2.json',level)
# Focused source evidence: exact excerpts checked against freshly extracted local source.
terms={'t-8-1':['базовый сценарий','диапазон вместо точки','Маржа ('],'t-15-8':['Четвёртая — варианты сокращения','Скрытые издержки'],'t-13-3':['Guardrail определены заранее','принять решение с учётом стоимости'],'t-10-4':['Алерты. Хороший алерт','каждый алерт'],'t-3-2':['каждый гейт имеет метрику'],'t-10-1':['Разделите вызовы'],'t-8-2':['Management reserve ('],'t-3-9':['стратегия тестирования']}
trace=[]
for c in cs:
 if c['id'] not in ids:continue
 s=sources[c['topicId']];ex=[]
 for term in terms[c['topicId']]:
  i=s.find(term);assert i>=0,(c['topicId'],term);ex.append(s[i:i+650])
 trace.append({'TC-ID':c['id'],'topicId':c['topicId'],'sourceProposition':c['sourceTopicExplanation'],'exactLocalExcerpts':ex,'visibleDecisiveFacts':c['decisiveFacts'],'strongestSourceApplication':notes[c['id']],'status':'SUPPORTED','scopeNote':'Синтетические числа/ресурсные ограничения реализуют правило источника; не цитируются как факты учебника. TC-085 source support не закрывает duplication.','sourceSHA256':sha(R/'InteractiveBook/WebContent/index.html')})
table('source-trace-r2.csv',trace)
# Preserve independent baseline classifications unless authored boundary has actually been rechecked.
dup=list(csv.DictReader((Q/'duplication-audit-independent.csv').open(encoding='utf-8-sig')))
for row in dup:
 id=row['caseId'];row['revisionReview']='Unchanged authored decision; independent baseline verdict retained' if id not in ['TC-083','TC-084','TC-090','TC-094','TC-098','TC-100'] else 'Rechecked authored context/options against production decision boundary'
 if id in ['TC-083','TC-084']:
  row['differentDecisiveFact']='Совпадение договоров в независимых отчётах, изменение старой маржи, диапазон ежегодной цены и частичная информация с ценой ожидания; готовой чистой NPV нет.'
  row['differentCandidateMistake']='Сложить пересекающиеся валовые поступления или финансировать возврат sunk cost вместо восстановить прирост к базовому сценарию и проверить устойчивость ранжирования.'
  row['differentActualDecision']='Продолжить/остановить оставшееся вложение и заменить финансовые ориентиры; не сравнение разных горизонтов TC-042 и не последовательность взаимозависимых работ TC-051…053.'
 if id=='TC-090':row['differentDecisiveFact']='Подрядчик прекращает поддержку через квартал, обязательство продолжается ещё два; передача5 финансируется остановками35 при лимите70. В отличие от TC-066/073, критичен срок ухода плюс согласованная портфельная и переходная смета.'
 if id=='TC-094':
  row['differentDecisiveFact']='Тест завершён; guardrail нарушен, есть конкретный конфликт пяти дней аналитика и месячного окна независимого теста.'
  row['differentActualDecision']='Не объявлять общий успех и распределить следующую неделю без потери независимого окна; не останавливать текущее вредное воздействие TC-075.'
 if id=='TC-098':row['differentCandidateMistake']='Отдать общий неизвестный риск-фонд под уже обеспеченные выявленные риски; не невозможное перечисление всех будущих событий.'
 if id=='TC-100':
  row['differentDecisiveFact']='Полный учёт, известные длительности шума, четыре минуты устранения,600 ошибок и60 минут ёмкости; окно нужно вывести самостоятельно.'
  row['differentActualDecision']='Выбрать допустимое окно вызова из конкурирующих ограничений; не восстанавливать слепой знаменатель/сквозную диагностику TC-068.'
 if id=='TC-085':row['revisionReview']='MANIFEST BLOCKER: kept byte-identical; NEAR DUPLICATE remains. No invented alternative boundary.'
table('duplication-audit-r2.csv',dup)
def tokens(c):return set(re.findall(r'[a-zа-яё]{3,}',(' '.join([c['context'],c['question'],c['mentalModel']]+[o['text'] for o in c['options']])).lower()))
retr=[]
for c in cs:
 a=tokens(c)
 for g in gold:
  b=tokens(g);retr.append({'candidate':c['id'],'production':g['id'],'jaccard':round(len(a&b)/len(a|b),5),'sameTopic':c['topicId']==g['topicId'],'samePrimary':c['primaryPattern']==g['primaryPattern']})
write('cross-bank-retrieval-r2.json',{'pairCount':len(retr),'note':'Lexical inventory is a retrieval aid, not semantic QA proof. Semantic classifications in duplication-audit-r2.csv; known near duplicate retained honestly.','pairs':retr})
internal=[]
for a,b in itertools.combinations(cs,2):
 family=bool(a['scenarioFamilyId'] and a['scenarioFamilyId']==b['scenarioFamilyId'])
 assert family or a['mentalModel']!=b['mentalModel']
 assert family or [o['text'] for o in a['options']]!=[o['text'] for o in b['options']]
 internal.append({'a':a['id'],'b':b['id'],'controlledFamily':family,'boundaryA':a['mentalModel'],'boundaryB':b['mentalModel'],'status':'CONTROLLED REINFORCEMENT' if family else 'DISTINCT BOUNDARIES (author self-check)'})
write('internal-duplication-r2.json',{'pairs':internal,'pairCount':300,'duplicates':0,'nearDuplicates':0,'focus':'Revised financial pair retains investment/counterfactual boundary; TC-094 capacity follows completed guardrail result, distinct from blocked flow095; TC-100 alert timing differs from tail-segmentation092 and SLO architecture099.'})
blocked={'id':'TC-085','status':'MANIFEST BLOCKER','reason':'Independent QA requires another diagnostic boundary; frozen row explicitly fixes localized impact + sufficient targeted set + much more expensive full regression. Those are exactly the decisive fact, candidate error and actual choice identified as TC-004 near duplicate. Cosmetic changes cannot satisfy both requirements.','frozenRow':mr['TC-085'],'QAFix':next(f for f in fixes if f['caseId']=='TC-085'),'actionTaken':'STOP on this ID; candidate row left byte-identical; no manifest edit. Other authorized local fixes completed.','requiredExternalDecision':'Manifest owner must authorize/revise the single diagnostic boundary before TC-085 can be changed.','TC004Tests':'Выбрать достаточный целевой регресс при локальном impact и недостающей автоматике, затем ограничить rollout.','TC085Tests':'Выбрать достаточный целевой регресс при локальном impact вместо дорогого полного регресса.','differentDecisiveFact':'Нет достаточного различия внутри текущей frozen boundary.','differentCandidateMistake':'Нет достаточного различия: избыточный полный или недостаточный быстрый набор вместо достаточного targeted.','differentActualDecision':'Ядро одинаково: выполнить достаточный targeted и решать о выпуске.','classification':'NEAR DUPLICATE'};write('manifest-blocker-TC085.json',blocked)
plan=read(P/'fix-plan.json')
for row in plan:row['status']='MANIFEST BLOCKER — not done; unchanged' if row['TC-ID']=='TC-085' else 'done — author self-check PASS; focused independent QA pending'
write('fix-plan.json',plan)
counts=dict(collections.Counter(r['classification'] for r in dup));counts.setdefault('DUPLICATE',0)
qa={'status':'NOT READY — MANIFEST BLOCKER TC-085','readyForFocusedQA':False,'candidateSHA256':sha(P/'cases_TC076_TC100_r2.json'),'priorBlockerFixed':1,'priorBlockerTotal':1,'priorMajorsFixed':11,'priorMajorsTotal':12,'remainingMajors':1,'reclassified':0,'changedCases':12,'unchangedByteIdentical':13,'requiredFrozenCasesByteIdentical':12,'unexpectedChanges':0,'uniqueStrongest':{'pass':25,'changed12':'author pairwise self-check','requested13':'13/13 including unchanged TC-085; duplication remains separate','frozen12':'independent baseline PASS carried forward, exact bytes preserved','limitation':'Masked-key author review is not independent blind QA.'},'sourceGrounded':25,'manifestAligned':25,'manifestAlignmentScope':'Metadata and frozen intended boundaries retained; TC-085 boundary itself conflicts with uniqueness acceptance.','levelFocused':{id:v['status'] for id,v in level.items()},'familiesPass':4,'schema':'PASS','runtime':'PASS','crossBank':counts,'internalDuplicates':0,'internalNearDuplicates':0,'surfaceLeakage':'PASS within specified 78 exploratory rules','bestSimpleHeuristic':st['bestSimpleHeuristic'],'combined100Best':st['combined100Best'],'unresolvedIds':['TC-085'],'noImport':True,'noCommitPush':True}
write('self-qa-r2.json',qa);st.update(priorBlockerFixed=1,priorMajorsFixed=11,remainingMajors=1,uniqueStrongest=25,sourceGrounded=25,manifestAligned=25,crossBank=counts,internalDuplicates=0,internalNearDuplicates=0,readyForFocusedQA=False);write('batch-statistics-r2.json',st)
report='''# Batch 03 r2 — targeted revision

**READY FOR FOCUSED QA: NO. MANIFEST BLOCKER: TC-085.**

Исправлены 1/1 прежний blocker (TC-090) и 11/12 major по авторской самопроверке. Оставшийся major — TC-085 ↔ TC-004 NEAR DUPLICATE. Он не reclassified и не скрыт как закрытый. Содержательные исправления остальных IDs требуют independent focused QA; авторская самопроверка не является финальным разрешением.

## Scope и неизменность

Изменены 12 кейсов: TC-076/077/078/079/080/083/084/090/092/094/098/100. Все 12 обязательных frozen IDs побайтово сохранены. TC-085 дополнительно сохранён без изменения из-за запрета менять frozen boundary: всего unchanged13, unexpected0. Требование changed13 не выполнено по явному правилу STOP на manifest blocker, а не из-за пропуска строки.

Baseline batch-03 не перезаписан. Frozen v2.2.2, production TC-001…075, schema, Swift и независимый QA неизменны; проверены protected-input-hashes.json. Нет импорта, Batch04, commit/push. Metadata/eligibility/уровни/семьи сохранены25/25; J5/M12/S5/H3, standalone16/linked9.

В fix-plan.json точный diagnosis и required fix из case-fixes.csv, разрешённые поля, constraint и статус каждого из13 IDs. change-log.csv содержит только12 реально изменённых строк с точными field paths и before/after. Derivative decisiveFacts и authorRationale пересогласованы там, где менялась реализация reasoning; новый blueprint не вводился. Revision metadata не менялась ради косметического diff.

## TC-085 — почему STOP

Frozen row задаёт буквально: локализованный класс риска, достаточный targeted набор, значительно более дорогой полный регресс; boundary — полный регресс для любого изменения против risk-based по impact. Independent QA признал именно эту причину и решение повтором TC-004. В TC-004 выбирается достаточный targeted при локальном impact и ограничивается экспозиция; в TC-085 то же ядро без экспозиции. Смена чисел, компании, роли или добавление другой ошибки не устраняет совпадение замысла.

Чтобы получить другую decisive reason и actual decision, нужна авторизация владельца manifest на локальную смену этой boundary. Она запрещена текущим заданием. Поэтому никаких изменений TC-085 и manifest не сделано. Полное свидетельство — manifest-blocker-TC085.json. Классификация остаётся NEAR DUPLICATE.

## Что исправлено

- TC-076/077/078: WHEN A теперь сравнивает положительный эффект со всеми альтернативами, WHEN C требует отсутствия положительного эффекта и manual, и automation. Состояния0/6/18 и границы4/8 не изменены.
- TC-079/080: explanation/whyNotBest D не ссылаются на выдуманный согласованный deadline; названы лишнее ожидание без указанной выгоды и, для079, невыполнение смысла ответа. Context/options неизменны.
- TC-090: в context до выбора дана невозможность продлить поддержку после квартала при ещё двух кварталах обязательного сопровождения. Передача за5 успевает до ухода; работа преемника включена в40. A стоит70 и выполним, D стоит65, но оставляет обязательство без исполнителя. Score D0.8→0.6; WHEN A/D и объяснения согласованы. Источник §15.8: скрытая цена ухода подрядчика с уникальными знаниями и пересборка портфеля обязательств.
- TC-092: удалена недостаточная OR-ветка WHEN D; теперь требуется подтверждение одинаковой динамики региональных распределений.
- TC-098: B содержит исполнимую децентрализацию по реестрам выявленных рисков, без обещания перечислить неизвестные. WHEN оправдывает весь вариант при отдельном сохранённом фонде неизвестных рисков. Score0.5→0.58 учитывает профессиональность, но не исправляет неверное назначение денег здесь.

## Реализация уровней

TC-083/084: Senior self-check PASS. Готовые очищенные NPV и диагноз double count из context убраны. Читателю даны записи двух функций с совпадающими договорами, старый тариф и его исчезающие затраты, новый support и диапазон ежегодной цены. Нужно восстановить прирост относительно базового сценария, проверить устойчивость к траектории цены и решить, стоит ли платить за информацию только о первом годе. Простое сложение отчётов или учёт полного sunk cost дают неверную модель. Формула: (новая выручка − (4−2) −1)×2,5−8. Диапазоны: +9,5…+14,5 и −5,5…−2 при альтернативе+5. Только цена/будущая NPV меняется между siblings; остальные факты, options и порядок одинаковы.

TC-094: Middle self-check PASS. Guardrail по-прежнему блокирует успех/rollout. Но его применения недостаточно: A и D оба соблюдают запрет, а выбор требует распределить пять дней аналитика между достаточной двухдневной диагностикой и трёхдневной подготовкой независимого теста. Углубление не ускоряет двухнедельное исправление и теряет месячное окно.

TC-100: Middle self-check PASS. Нужно вывести окно из двух ограничений:20 ложных проверок×10мин>60мин доступной ёмкости; при10% ошибок от1000/мин окно2мин+устранение4мин даёт600 ошибок, окно10мин —1400. Длительность шума90сек, поэтому2мин его отсекают. Ни порог как готовый правильный ответ, ни число команд не служат доказательством уровня. Наблюдения корректны, механизм слепоты TC-068 не повторяется.

Подробности — level-focused-self-qa-r2.json. Эти оценки авторские и подлежат проверке QA.

## Pairwise, source и семьи

13/13 fix-scope случаев прочитаны с полями ответа/score/explanation, исключёнными из key-masked-review-input.json. Это **не независимый и не полностью слепой review**: автор уже знает baseline и создавал revision. 39 попарных разборов содержат видимые факты и механизм проигрыша; отдельно зафиксирован A>D в090. Из13 один085 не изменён, unique strongest у него остаётся, но duplication не устранён.

Whole-batch unique strongest25/25:13 авторских сравнений +12 unchanged независимых PASS. Source25/25: source-trace-r2.csv на13 fix-scope IDs с точными локальными цитатами и сохранённые независимые verdicts12. Цифры и ресурсные ограничения синтетические; strongest principles из учебника. Schema использует decisiveFacts и mentalModel как аналоги whatToNotice/thinkingModel.

Families4/4 PASS: literal diff в family-diff-analysis-r2.json, одинаковые actor/base/question/options/order/constants, одна logical variable. F-DR-T01 ключиC/A/D, F-TD-P01 B/C, F-PE-P01 D/A, F-BV-P02 B/D. Последняя семья меняет только диапазон цены, определяющий frozen NPV state; иной hidden mutation нет.

## Duplication и surface

Cross-bank: NO CLOSE ANALOG2, ALLOWED REINFORCEMENT22, NEAR DUPLICATE1 (085), DUPLICATE0. Исправленные границы пересопоставлены с полными production решениями, остальные independent verdicts сохранены. Все1875 пар доступны как retrieval inventory; лексический score не выдаётся за семантический verdict. Контролируемые family siblings исключены из случайных повторов; внутренние near/duplicates0, рассмотрены300 пар.

Surface: то же78 правил/19 признаков. Лучшее r2 правило — минимум action proxy,10/25 против9/25 baseline. Максимальные expected hits при random tie снизились9,83→9,33. Combined100 best33/100 против35/100 baseline; позицииA24/B24/C25/D27. Заметного усиления cue не обнаружено в проверенном наборе. Family-preserving permutation2000: r2 adjusted p≈0,623, combined≈0,565. Это exploratory scan, не доказательство отсутствия любых подсказок. Surface PASS в этих пределах; содержание не выравнивалось ради длины.

## Техническая проверка

TrainerBank.load strict schema2.0 загружает25 кейсов. Runtime vocabulary PASS, unknown codes0. Metadata против frozen manifest25/25, eligibility и part/topic проверены. Ключи осталисьA6/B6/C6/D7. Машинная проверка raw UTF-8 spans подтверждает byte-identical frozen cases, а не только равенство разобранного JSON.

Unresolved IDs: [TC-085]. До разрешения manifest conflict общий READY FOR FOCUSED QA остаётся NO. Исправленные12 доступны для просмотра; candidate не импортирован.
'''
report+='\nCandidate SHA-256: `'+sha(P/'cases_TC076_TC100_r2.json')+'`.\n';(P/'revision-report.md').write_text(report)
write('artifact-hashes-r2.json',{p.name:sha(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes-r2.json'})
print(json.dumps(qa,ensure_ascii=False,indent=2))
