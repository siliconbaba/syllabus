import json,csv,hashlib,re,collections,difflib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OLD=P.parent/'batch-02';QA=ROOT/'agent-artifacts/qa/batch-02'
def read(p):return json.loads(p.read_text())
def write(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bank=read(P/'cases_TC051_TC075_r2.json');by={c['id']:c for c in bank['cases']};old={c['id']:c for c in read(OLD/'cases_TC051_TC075.json')['cases']};gold=read(ROOT/'InteractiveBook/TrainerContent/cases.json')['cases'];gb={c['id']:c for c in gold};reg=read(P/'regression.json');stats=read(P/'batch-statistics-r2.json');scope=['TC-051','TC-052','TC-053','TC-068','TC-074','TC-075']
assert stats['candidateSHA256']==sha(P/'cases_TC051_TC075_r2.json')
assert stats['after']['bestFirstTieHits']<=11
assert stats['bestSingleAfter']<=9
# Selections made after reading only context/question/text; same-author knowledge is disclosed.
predicted={'TC-051':'C','TC-052':'A','TC-053':'D','TC-068':'D','TC-074':'D','TC-075':'B'}
reader=[]
for id in scope:
 c=by[id];key=next(o['id'] for o in c['options'] if o['isBest']);assert key==predicted[id]
 reader.append(dict(id=id,predictedStrongest=predicted[id],productionStrongest=key,decisiveFacts=c['decisiveFacts'],comparisons={o['id']:('SELF — not a competing pair' if o['isBest'] else o['explanation']) for o in c['options']},status='PASS',changed=id in reg['changedCases']))
write('key-hidden-review.json',[dict(id=by[i]['id'],context=by[i]['context'],question=by[i]['question'],options=[dict(id=o['id'],text=o['text']) for o in by[i]['options']]) for i in scope])
write('reader-check-r2.json',dict(method='Author read final context/question/option text separately from scoring fields. Prior context and keys are known; not an independent blind experiment.',cases=reader,unchanged20UniqueStrongest='Prior independent QA 20/20; no content change. TC-075 unique answer remains valid despite duplicate status.',totalUniqueStrongest=25))
proof075={'status':'UNRESOLVED: manifest-level duplicate','frozenConcept':'p=0.03 on day 9 of precommitted 14; sample almost complete; no early-success rule; decide whether to stop','frozenBoundary':'Первая значимость ↔ соблюдение заранее утверждённого протокола.','frozenLevel':'junior','TC024Tests':'Do not stop for intermediate significance or invent a post-hoc stop rule; preserve the precommitted final reading and related product decision.','TC075Tests':'Do not stop for intermediate significance or invent a post-hoc stop rule; preserve the precommitted final reading.','invariantFacts':['14 days precommitted','day 9','p=0.03','almost complete sample','no early-success rule'],'sameStrongestReasoning':'Intermediate significance is not authorization to stop before the precommitted protocol.','rejectedWorkarounds':[{'idea':'change numbers, product, wording or distractors','whyRejected':'Leaves the same decisive fact and strongest reasoning; cosmetic duplicate.'},{'idea':'add an early-success rule','whyRejected':'Contradicts frozen absence of early-stop and changes the decisive boundary.'},{'idea':'stop because guardrail failed or validity broke','whyRejected':'Replaces peeking/protocol boundary with safety or test-validity boundary.'},{'idea':'test sequential methods, multiple comparisons or post-hoc segment selection','whyRejected':'Changes frozen diagnostic task, and potentially level; cannot be authorized by wording alone.'},{'idea':'continue experiment but launch separately','whyRejected':'TC-024 already explicitly tests the separate rollout governance; no new diagnostic distinction.'}],'requiredDecision':'MAIN must explicitly authorize a local change to TC-075 concept/boundary in the manifest before a genuinely different item can be authored. Manifest not edited.','candidateAction':'TC-075 kept byte-identical with revision=1; no cosmetic sixth change.'}
write('manifest-duplicate-blocker.json',proof075)
comparison074={'TC-012 tests':'Where to bring the allocation conflict: recognize the authority of the shared portfolio owner and bring comparable consequences. Alternatives differ in local protection, proportional split, sponsor arbitration and authorized portfolio decision.','TC-074 now tests':'Which concrete shared schedule is valuable when one program has an independent later prerequisite. Program A has higher CoD, but first platform slot does not advance its launch. All proposed decisions explicitly involve the same owner.','why not diagnostically equivalent':'Knowing the right escalation owner cannot discriminate A/C/D in r2. The decisive inference is zero marginal benefit of A-first given gateway readiness; B-first saves its month without delaying A.','decisiveBoundaryBefore':'local arbitration versus authorized common prioritization','decisiveBoundaryAfter':'rank by full program CoD versus evaluate marginal effect of shared slot on complete dependency chains','frozenConceptFidelity':'Still two P0 programs, one shared platform capacity, one cross-program trade-off decided by the common owner; topic/domain/level/patterns unchanged.','TC045 comparison':'TC-045 changes acceptance mechanics to decouple existing work and recalculate a single launch. TC-074 changes allocation order between programs using existing readiness constraints; no acceptance-process redesign.'}
write('diagnostic-comparisons.json',dict(TC074= comparison074,TC075=proof075))
dup=[]
for id in scope:
 if id in ['TC-051','TC-052','TC-053']:
  refs='TC-021; TC-012; TC-045; TC-046';classification='ALLOWED REINFORCEMENT';reason='New initiative defer/next/preempt requires overlapping-outcome accounting, scarce acceptance and uncertainty bounds. TC-021 reprioritizes under budget cuts; 012 tests authority; 045 changes acceptance in one project; 046 chooses information acquisition/plan B. Neither simply running old strongest determines this queue.'
 elif id=='TC-068':
  refs='TC-008; TC-043; TC-044; TC-047; TC-050';classification='ALLOWED REINFORCEMENT';reason='Conditional denominator and absent input require different detection regimes and a tested end-to-end probe. This is not release-gate attribution, SLO release scope, segment rollback, scanner blocking readiness or trace propagation.'
 elif id=='TC-074':refs='TC-012; TC-045; TC-005';classification='ALLOWED REINFORCEMENT';reason=comparison074['why not diagnostically equivalent']+' '+comparison074['TC045 comparison']
 else:refs='TC-024; TC-031; TC-032';classification='DUPLICATE';reason=proof075['sameStrongestReasoning']+' 031/032 instead test completed protocol against minimum useful effect; moving there would change frozen TC-075.'
 dup.append(dict(candidateId=id,referenceIds=refs,classification=classification,reason=reason,status='UNRESOLVED' if id=='TC-075' else 'FIXED / author self-check',allProduction50Screened=True))
with (P/'duplication-audit-r2.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=dup[0].keys());w.writeheader();w.writerows(dup)
# All 300 comparisons retained as lexical/pattern/decision descriptions, never used alone to classify semantics.
screen=[]
for id in scope:
 c=by[id];a=set(re.findall(r'\w+',c['context'].lower()))
 for g in gold:
  b=set(re.findall(r'\w+',g['context'].lower()));screen.append(dict(candidateId=id,referenceId=g['id'],contextJaccard=len(a&b)/len(a|b),samePrimaryPattern=c['primaryPattern']==g['primaryPattern'],referenceDecision=next(o['text'] for o in g['options'] if o['isBest']),referenceModel=g['mentalModel']))
write('cross-bank-screen.json',dict(comparisons=screen,semanticAuthority='duplication-audit-r2.csv and diagnostic-comparisons.json; lexical similarity is not a semantic verdict'))
# Source excerpts from the sole textbook; frozen schemas use mentalModel/decisiveFacts.
from html.parser import HTMLParser
class Text(HTMLParser):
 def __init__(self):super().__init__();self.t=[]
 def handle_data(self,s):self.t.append(s)
html=(ROOT/'InteractiveBook/WebContent/index.html').read_text();evidence={}
for topic,needles in {'t-9-3':['Senior / Lead TPM','фреймворк — основа'], 't-9-4':['Карта зависимостей','Эскалация зависимостей'], 't-10-4':['Развилка по алертам','синтетический мониторинг'], 't-13-3':['Подглядывание (peeking)','Длительность — заранее']}.items():
 m=re.search(r'<article[^>]*id="'+topic+r'"[^>]*>(.*?)</article>',html,re.S);t=Text();t.feed(m[1]);lines=[' '.join(s.split()) for s in ''.join(t.t).splitlines()];evidence[topic]=[l for l in lines if any(n.lower() in l.lower() for n in needles)];assert evidence[topic]
write('source-evidence-r2.json',dict(textbookSHA256=sha(ROOT/'InteractiveBook/WebContent/index.html'),topics=evidence,cases={i:dict(topic=by[i]['topicId'],proposition=by[i]['sourceTopicExplanation'],realization=by[i]['authorRationale']) for i in scope}))
issueRecords=[]
for issue in csv.DictReader((QA/'case-fixes.csv').open(encoding='utf-8-sig')):
 code=issue['issueId'];status='UNRESOLVED' if code=='B02-01' else 'FIXED';ev={'B02-01':'manifest-duplicate-blocker.json; TC-075 unchanged','B02-02':'TC074 diagnostic-comparisons.json: marginal slot value, not owner selection','B02-03':'F-DM-T01: acceptance bottleneck, same-order-ID loss dedupe, no probability assumption; unchanged only-CoD mutation','B02-04':'TC-068: conditional denominator, variable night volume, loss-of-input detection, tested end-to-end alert','B02-05':'TC-053 A=0.70 (25–27), B=0.35 (43); shared acceptance constraints in all sibling contexts now create a real difference. D=1.0 (18–20).'}[code]
 issueRecords.append(dict(issueId=code,severity=issue['severity'],cases=issue['caseIds'],status=status,evidence=ev,originalDiagnosis=issue['problem'],authority='author self-assessment; requires focused independent QA'))
# Detailed change log contains actual changes only, not the unmodified unresolved item.
def dif(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):return [z for k in sorted(a.keys()|b.keys()) for z in dif(a.get(k),b.get(k),p+'.'+k if p else k)]
 if isinstance(a,list):return [z for n,(x,y) in enumerate(zip(a,b)) for z in dif(x,y,f'{p}[{n}]')] if len(a)==len(b) else [(p,a,b)]
 return [] if a==b else [(p,a,b)]
log=[]
for i in reg['changedCases']:
 ds=dif(old[i],by[i]);codes='B02-03; B02-05' if i=='TC-053' else ('B02-03' if i in ['TC-051','TC-052'] else ('B02-04' if i=='TC-068' else 'B02-02'))
 log.append({'TC-ID / family':i,'QA issue':codes,'fields changed':'; '.join(x[0] for x in ds),'before':json.dumps({x[0]:x[1] for x in ds},ensure_ascii=False),'after':json.dumps({x[0]:x[2] for x in ds},ensure_ascii=False),'why fixed':by[i]['authorRationale']})
log.append({'TC-ID / family':'F-DM-T01','QA issue':'B02-03; B02-05','fields changed':'shared base context; shared options; explanations; quality; decision model (contract and positions unchanged)','before':'Known independent full costs: 2x+6 / 26 / 4x / 18; direct minimization','after':'Acceptance bottleneck, outcome overlap and uncertainty bounds must be interpreted before deriving costs: 2x+[5,7] / 4x+3 / 4x / [18,20]; states 1/4/10 remain C/A/D','why fixed':'Common complexity for all three siblings; no second mutation or level/contract change.'})
with (P/'change-log.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=log[0].keys());w.writeheader();w.writerows(log)
levels={i:dict(status='PASS — author assessment',why=by[i]['authorRationale']) for i in ['TC-051','TC-052','TC-053','TC-068']}
when=[dict(id=i,option=o['id'],condition=o['whenItWouldBeBest'],status='PASS — author checks entire action and timing, hypothetical premise not imported into actual context') for i in reg['changedCases'] for o in by[i]['options']]
qa=dict(verdict='NOT READY',readyForFocusedQA=False,readyForImport=False,issues=issueRecords,priorBlockerFixed='0/1',priorMajorFixed='4/4 — author assessment',seniorRealization=levels,TC053DecisionQuality=dict(status='PASS',A=.7,B=.35,why='The plans are no longer equivalent after the common family rewrite. A delivers at week 4, B at week 6 through the same acceptance bottleneck; context supports cost 25–27 vs 43. No advantage is invented in explanation.'),TC074vsTC012='ALLOWED REINFORCEMENT',TC075vsTC024='DUPLICATE',familyStatus='PASS',uniqueStrongest='25/25 (6 same-author rechecks, 19 inherited independent passes)',surfaceLeakage='PASS',schema='PASS',regression=reg,whenChecks=when,remainingUnresolvedIDs=['TC-075'],blockingDecision=proof075['requiredDecision'],candidateSHA256=sha(P/'cases_TC051_TC075_r2.json'),limitations=['Same-author key-hidden review, not independent blind QA.','Family uncertainty transition bands are not sampled; selected states have robust unique keys.','Level and semantic-duplication closures are editorial judgments pending focused QA.'])
write('self-qa-r2.json',qa)
report=f'''# Batch 02 r2 — targeted revision

**NOT READY. READY FOR FOCUSED QA: NO.** Сохраняется B02-01: **TC-075 — UNRESOLVED: manifest-level duplicate**. Остальные четыре MAJOR исправлены по авторскому self-check; независимый focused QA должен подтвердить эти выводы.

Изменены **5** кейсов: TC-051/052/053/068/074. Не изменены **20**: все 19 frozen и TC-075. Это явное отклонение от ожидаемых 6/19: разрешённый unresolved не маскируется косметической шестой правкой. TC-075 сохранён побайтово, включая revision=1. У пяти содержательно изменённых revision=2. Исходные batch-02, QA, manifest, production 001–050, schema, учебник и Swift не изменены.

## Закрытие замечаний

| Issue | Severity | Result |
|---|---|---|
| B02-01, TC-075/024 | BLOCKER | UNRESOLVED — frozen диагностическая граница совпадает |
| B02-02, TC-074/012 | MAJOR | FIXED — выбирается предельная ценность общего слота по двум цепочкам |
| B02-03, F-DM-T01 Senior | MAJOR | FIXED — общая приёмка, пересекающиеся потери, неизвестный объём заказов |
| B02-04, TC-068 Senior | MAJOR | FIXED — риск пропуска входа против шума малой выборки |
| B02-05, TC-053 quality | MAJOR | FIXED — новое различие A/B объяснено фактами всех siblings |

Family issue ссылается на те же B02-03/B02-05 и не увеличивает счётчик.

## F-DM-T01: что изменилось в рассуждении

Старая задача давала готовые полные цены и требовала только min. Теперь внешняя разработка за 3 млн ₽ выглядит дешевле четырёх недель ожидания при низком CoD, но не даёт собственной приёмки: принятый результат появится в шестую неделю. Нужно найти общее ограничение, а не принять обещание локальной скорости. Дополнительно Р и К дают один результат и содержат одни ID заказов: простое суммирование карточек дважды считает клиентскую потерю. Неизвестный объём заказов нельзя заменять произвольной средней вероятностью.

После восстановления зависимостей выводятся, а не выдаются готовыми, диапазоны полных потерь:

| State | A | B | C | D | Strongest |
|---|---|---|---|---|---|
| TC-051, x=1 | 7–9 | 7 | 4 | 18–20 | C |
| TC-052, x=4 | 13–15 | 19 | 16 | 18–20 | A |
| TC-053, x=10 | 25–27 | 43 | 40 | 18–20 | D |

Новая единица обязательства — принятый результат вместе с зависимыми работами, а не завершение карточки разработки. Прямые затраты переключения 6 млн ₽, размер Н, стратегия, окна приёмки и интервалы последствий одинаковы в siblings. Единственная mutation — CoD Н 1/4/10. Все ключи устойчивы на полном диапазоне оценок. Около границ существуют зоны неопределённого ранга, но ни один case в них не расположен. Контракт и family positions 1/2/3 сохранены.

TC-053: **A=0.70, B=0.35, D=1.0**. Требование равных scores относилось к прежним равноценным A/B. После общей содержательной правки A даёт 25–27, B — 43; B не учитывает общий bottleneck. Это основание указано в context всех трёх siblings, не добавлено задним числом в explanation. Новый разрыв требует независимой проверки, но больше не приписывает разное качество двум одинаковым планам.

## Why TC-068 now requires Senior reasoning

{by['TC-068']['authorRationale']}

Нормальные текущие SLI, CPU 90% и запас autoscaling сохранены. Решение касается именно интерпретации сигнала в контексте пользовательского пути и capacity. Само понижение CPU до warning есть в трёх вариантах и не определяет ключ.

## Cross-bank различия

**TC-012 tests:** {comparison074['TC-012 tests']}

**TC-074 now tests:** {comparison074['TC-074 now tests']}

**Why no longer diagnostically equivalent:** {comparison074['why not diagnostically equivalent']}

Общая authority и итоговый cross-program plan сохранены. Frozen concept конкретизируется через влияние общей зависимости на конечные даты; выбирать отдельный местный P0 нельзя. Внешний шлюз А к концу второго месяца делает первый слот А бесполезным для его запуска; Б сейчас сохраняет обе даты.

Для всех шести scoped ID выполнен screen с production 50 (300 сравнений) и содержательное сравнение ближайших аналогов; классификации — `duplication-audit-r2.csv`. Новые family cases не повторяют budget-cut TC-021, authority TC-012 или перепроектирование приёмки одного запуска TC-045. TC-068 не повторяет release freeze, сегментный rollback или trace ID: это выбор наблюдения при исчезающих событиях и неоднородном потоке.

## Почему TC-075 оставлен unresolved

Manifest фиксирует не только topic/pattern, но и конкретные p=0.03 на дне 9 из 14, отсутствие ранней победы и boundary «первая значимость ↔ соблюдение заранее утверждённого протокола». Это тот же решающий вывод TC-024. Иные числа, distractors и объяснения не меняют его. Новое раннее правило нарушит frozen факт; guardrail/ошибка рандомизации/множественные сравнения заменят диагностическую задачу; отдельный rollout уже проверяется TC-024.

Поэтому **TC-024 strongest reasoning = TC-075 strongest reasoning** в разрешённых границах. Нужна отдельная авторизация MAIN на локальное изменение concept/boundary TC-075 в manifest. Сам manifest и candidate TC-075 здесь не менялись. Полное доказательство и отклонённые варианты — `manifest-duplicate-blocker.json`.

## Проверки

- Ключи: A6/B6/C6/D7, strongest-key changes: 0.
- Metadata changes: 0; unexpected frozen regression: 0.
- 19 frozen и дополнительно TC-075 — побайтово прежние; весь новый файл воспроизводится заменой только пяти разрешённых case-фрагментов.
- Unique strongest: 25/25 — все шесть scoped ID прочитаны повторно, 19 прочих наследуют независимый PASS. Автор знал прежние ключи: это не независимый blind test.
- F-DM-T01 и три untouched семьи: PASS. Только одна family изменена.
- Штатный `TrainerBank.load(url:)`, свежая сборка текущих production sources: PASS.
- Тот же независимый набор 78 эвристик воспроизвёл baseline: combined {stats['before']['bestFirstTieHits']}/25, single {stats['bestSingleBefore']}/25.
- После правки: combined **{stats['after']['bestFirstTieHits']}/25**, single **{stats['bestSingleAfter']}/25**, максимум ожидаемых random-tie попаданий **{stats['after']['bestRandomTieExpectedHits']:.3f}/25**. Surface regression: PASS. Это проверенный exploratory набор, не доказательство отсутствия любых cues.
- Resulting75: {stats['combined75']['bestFirstTieHits']}/75; production не записывался.
- Изменений decisionQuality: {len(reg['decisionQualityChanges'])}; точные before/after — `change-log.csv` и `regression.json`.

У каждого изменённого option пересмотрены explanations и WHEN для полного действия, включая дату результата/приёмки. `whatToNotice` и `thinkingModel` представлены schema-полями `decisiveFacts` и `mentalModel`. Source grounding остаётся внутри учебника: §9.3/9.4, §10.4, для критического пути §2.4. Доказательство невозможности TC-075 опирается на §13.3 и финальный manifest, не на старый rationale.

Состав: 25 cases, 16 standalone / 9 linked, 4 families, J5/M11/S6/H3. Eligibility неизменна. Импорт, Batch 03 и изменение blueprint не выполнялись.

**Итог: BLOCKER fixed 0/1; MAJOR fixed 4/4 (self-check). Remaining unresolved IDs: [TC-075]. READY FOR FOCUSED QA: NO.**
'''
(P/'revision-report.md').write_text(report)
assert all(sha(ROOT/p)==h for p,h in read(P/'protected-input-hashes.json').items())
write('artifact-hashes.json',{f.name:sha(f) for f in sorted(P.iterdir()) if f.is_file() and f.name!='artifact-hashes.json'})
print('NOT READY; BLOCKER 0/1 fixed, MAJOR 4/4 author-fixed; changed 5, unchanged 20; unresolved TC-075')
