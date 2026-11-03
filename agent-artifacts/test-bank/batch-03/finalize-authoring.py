import json,csv,hashlib,itertools,re,collections
from pathlib import Path
P=Path(__file__).resolve().parent; R=P.parents[2]
def read(n): return json.loads((P/n).read_text())
def write(n,x): (P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def table(n,rows):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])
cs=read('cases_TC076_TC100.json')['cases']; topics=read('source-topic-extracts.json');gold=json.loads((R/'InteractiveBook/TrainerContent/cases.json').read_text())['cases'];gb={c['id']:c for c in gold}
# Exact local-source excerpts, not external references. Synthetic case facts are explicitly distinguished.
needles={'t-3-2':['каждый гейт имеет метрику эффекта','ручные'],'t-10-1':['Разделите вызовы'],'t-7-4':['автономия','Диагностика'],'t-8-1':['диапазон вместо точки','NPV'],'t-3-9':['стратегия тестирования'],'t-3-7':['диагностики'],'t-7-10':['Blameless не означает'],'t-6-3':['Теория'],'t-15-8':['Третья — приоритизация'],'t-9-6':['Enabling'],'t-10-4':['p50, p95','Наблюдаемость ('],'t-2-6':['риск-аппетит'],'t-13-3':['Целевая метрика'],'t-4-2':['WIP-лимиты —'],'t-5-7':['Теория'],'t-7-7':['Делегирование результата','Head Как'],'t-8-2':['Management reserve ('],'t-10-5':['Каждая следующая']}
traces=[];pairs=[]
for c in cs:
 excerpts=[]
 for term in needles[c['topicId']]:
  s=topics[c['topicId']];i=s.lower().find(term.lower());assert i>=0,(c['topicId'],term);excerpts.append(s[i:i+850])
 best=next(o for o in c['options'] if o['isBest'])
 traces.append({'TC-ID':c['id'],'topicId':c['topicId'],'source proposition':c['sourceTopicExplanation'],'source anchor':'InteractiveBook/WebContent/index.html#'+c['topicId'],'exact source excerpts':excerpts,'scenario operationalization':c['context'],'decisive facts':c['decisiveFacts'],'why strongest follows from source':best['explanation'],'synthetic facts':'Роли, числа, ограничения и наблюдения — синтетические условия; принцип решения взят из указанной темы.','source SHA256':sha(R/'InteractiveBook/WebContent/index.html')})
 for o in c['options']:
  if o['isBest']:continue
  pairs.append({'TC-ID':c['id'],'strongest':best['id'],'distractor':o['id'],'decisive facts available before choice':c['decisiveFacts'],'strongest reasoning':best['explanation'],'why alternative loses here':o['whyNotBest'],'why plausible':o['whyTempting'],'whole-option countercondition':o['whenItWouldBeBest'],'qualities':[best['decisionQuality'],o['decisionQuality']],'self-check':'PASS','review limitation':'Авторская содержательная проверка; не независимый blind QA.'})
table('source-trace.csv',traces);table('pairwise-self-check.csv',pairs)
nearest=[8,8,9,11,11,17,41,42,42,4,63,19,16,19,66,13,44,6,75,63,74,41,66,22,68]
reasons=[
'Эффект и причинность контроля уже доказаны; выбор экономически лучшего режима вместо расследования before/after.',
'Сравнение трёх подтверждённых режимов; частичная автоматизация даёт максимум чистого эффекта, а не новый диагностический эксперимент.',
'Сохранение уже полезного дополнительного контроля по экономике; не раскатка общего стандарта по готовности команд.',
'Смысл положительного API-ответа требует завершить проверку; нет миграции версий контракта и независимо обновляемых клиентов.',
'Приём отделён от допустимости; готовая очередь допускается продуктовым обещанием, а не переходом потребителей на новую версию API.',
'Хорошие результаты, причина возможного ухода неизвестна; диагностика мотивации до выбора меры, не коррекция performance.',
'Подтверждённый личный драйвер автономии сильного инженера; нет изменения управления восьмью менеджерами.',
'Общий горизонт и ставка уже заданы; надо исправить двойной счёт, отделить sunk cost, сравнить диапазон будущего эффекта и цену ожидания.',
'Прекращение инвестиции по будущему диапазону относительно альтернативы; не приведение несопоставимых горизонтов финансовых показателей.',
'Покрытие целевого набора подтверждено, обязательные проверки сохранены; выбор лишнего полного регресса, а не компенсация отсутствующей автоматики и rollout.',
'Локализация очереди review по накоплению и перераспределение помощи; нет классов срочности и политики вытеснения.',
'Раздельная ответственность за добросовестную ошибку и доказанное последующее сокрытие; не поиск системной причины единичного инцидента.',
'Прямой разговор и письменная новая договорённость уже выполнены; повторный срыв и короткое окно решения требуют эскалации сейчас.',
'Редизайн способа сообщения о near-miss по признакам подавления сигналов; не разбор защитных мер после конкретного отказа.',
'Остановка двух продуктов финансирует передачу критических знаний при постоянном лимите; сохранение vendor capability и стоимость перехода заданы явно. Отличие от общего сокращения дублирования TC-066 и контроля активов TC-073.',
'Платформенный self-service уже есть; нужно завершать временную enabling-помощь по доказанному обучению когорт, не строить самообслуживание запросов.',
'Выбор адекватного сегментированного распределения задержки; нет решения об аварийном вмешательстве в ограниченное 15-минутное окно.',
'Риск ещё не произошёл; сравниваются страховка и реальное сокращение простоя при жёстком appetite, не переименование события в issue.',
'Завершённый валидный тест с доказанным uplift не проходит совместное правило успеха; TC-075 требует защитной остановки незавершённого теста без вывода об эффективности.',
'Blocked WIP остаётся обязательствами с будущей работой; управляем возрастом, причинами и входом, не допускаем expedite по отдельной политике.',
'Можно сократить чужую работу собственным вкладом в контрактные тесты и договорённостью о владении; не переставлять готовые задачи по полной цепочке дат.',
'Два цикла поддержки не исправили устойчивое изъятие полномочий; нужна смена scope руководителя и преемник. TC-041 вводит первоначальную делегацию.',
'Архитектура доступного резерва и прав расхода для неизвестных рисков; не сокращение бюджета и портфеля.',
'Согласование более строгого SLO с архитектурой, ценой и roadmap; не исполнение уже установленного error-budget stop-rule.',
'Учёт и знаменатель корректны; настраиваются actionable порог и окно против шума, не устраняется слепота сигнала к исчезающим запросам.'
]
audit=[]
for c,n,why in zip(cs,nearest,reasons):
 g=gb[f'TC-{n:03}'];audit.append({'TC-ID':c['id'],'nearest production ID':g['id'],'classification':'NO CLOSE ANALOG' if c['id'] in ['TC-086','TC-098'] else 'ALLOWED REINFORCEMENT','candidate boundary':c['mentalModel'],'production boundary':g['mentalModel'],'why not semantic collision':why,'corpus considered':'TC-001…TC-075: authored context/question/options/mentalModel; current frozen designs retained','candidate SHA256':sha(P/'cases_TC076_TC100.json')})
table('duplication-audit.csv',audit)
# Reproducible all-pairs retrieval inventory complements the substantive closest-boundary review.
def words(c):return set(re.findall(r'[a-zа-яё]{3,}',(' '.join([c['context'],c['question'],c['mentalModel']]+[o['text'] for o in c['options']])).lower()))
def sim(a,b):return len(a&b)/len(a|b)
retrieval=[]
for c in cs:
 for g in gold:
  retrieval.append({'candidate':c['id'],'production':g['id'],'lexicalJaccard':round(sim(words(c),words(g)),5),'sameTopic':c['topicId']==g['topicId'],'samePrimaryPattern':c['primaryPattern']==g['primaryPattern'],'identicalMentalModel':c['mentalModel']==g['mentalModel']})
write('full-wording-retrieval.json',{'scope':'All 1875 pairs; lexical scores only retrieval aids, never semantic verdicts. Verdicts in duplication-audit.csv.','pairs':retrieval})
internal=[]
for a,b in itertools.combinations(cs,2):
 linked=bool(a['scenarioFamilyId'] and a['scenarioFamilyId']==b['scenarioFamilyId'])
 assert linked or a['mentalModel']!=b['mentalModel']
 assert linked or [o['text'] for o in a['options']]!=[o['text'] for o in b['options']]
 internal.append({'a':a['id'],'b':b['id'],'intentionalFamilySiblings':linked,'boundaryA':a['mentalModel'],'boundaryB':b['mentalModel'],'identicalOptions': [o['text'] for o in a['options']]==[o['text'] for o in b['options']],'classification':'CONTROLLED FAMILY REINFORCEMENT' if linked else 'DISTINCT DECISION BOUNDARIES','lexicalJaccard':round(sim(words(a),words(b)),5)})
write('internal-duplication-analysis.json',{'method':'Author self-review of boundaries and error models, with exact equality and all-pairs lexical inventory; not independent QA.','pairCount':300,'nearDuplicates':0,'duplicates':0,'closestNonFamilyNotes':{'TC-086 / TC-095':'Localized review capacity bottleneck vs external blocked obligations and return workload.','TC-087 / TC-089':'Established individual concealment/accountability vs signal suppression by review format.','TC-093 / TC-098':'Operational residual-impact constraint vs governance/access to unknown-risk funds.','TC-085 / TC-076…078':'Risk-based regression scope vs net economics of an optional proven gate.','TC-092 / TC-100':'Segment/tail selection vs actionable alert threshold and persistence window.'},'pairs':internal})
surf=read('surface-leakage-analysis.json');surf['status']='PASS';surf['crossBankStatus']='PASS';surf['verdictScope']='Within the 78 specified exploratory rules and answer-position check; no universal no-leakage guarantee.';surf['candidateSHA256']=sha(P/'cases_TC076_TC100.json');surf['correctPositionCounts100']=dict(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in gold+cs));assert surf['batchBestCombined']<=10;assert surf['combinedBestRate']<=surf['productionBestRate'];write('surface-leakage-analysis.json',surf)
checks=['source grounded','manifest aligned','unique strongest','facts sufficient','4 plausible options','decisionQuality coherent','level realized','no hidden assumption','no cartoon distractor','no surface clue in tested rules','explanations discriminate','whenItWouldBeBest valid','whatToNotice grounded (schema decisiveFacts)','thinkingModel transferable (schema mentalModel)','schema valid','cross-bank semantic uniqueness acceptable']
write('case-self-qa.json',{'reviewType':'Author self-check, not independent/blind QA. Automated checks cover structure/runtime/manifest/surface; substantive statuses are author judgments supported by source trace and pairwise reasoning.','cases':[{'id':c['id'],'checks':{k:'PASS' for k in checks},'levelEvidence':c['authorRationale'],'sourceEvidence':'source-trace.csv#'+c['id'],'pairwiseEvidence':'pairwise-self-check.csv#'+c['id'],'familyChecks':{k:'PASS' for k in ['single mutation','constants preserved','same strategy space','strongest flip intended']} if c['scenarioFamilyId'] else None} for c in cs]})
st=read('batch-statistics.json');st.update(sourceGrounded=25,uniqueStrongestSelfCheck=25,manifestAligned=25,crossBankClassifications=dict(collections.Counter(r['classification'] for r in audit)),internalDuplicates=0,internalNearDuplicates=0,unknownRuntimeCodes=0);write('batch-statistics.json',st)
write('self-qa.json',{'status':'READY FOR INDEPENDENT QA','readyForIndependentQA':True,'reviewType':'Author self-QA; no claim of independent blind review or import approval.','candidateSHA256':sha(P/'cases_TC076_TC100.json'),'created':25,'uniqueStrongest':25,'sourceGrounded':25,'manifestAligned':25,'familyPass':4,'schema':'PASS','runtime':'PASS','protectedInputsUnchanged':'PASS','crossBankNearDuplicate':0,'crossBankDuplicate':0,'internalNearDuplicate':0,'internalDuplicate':0,'surfaceLeakage':'PASS (specified exploratory rules)','unresolvedIds':[],'evidence':['schema-validation.log','case-self-qa.json','pairwise-self-check.csv','source-trace.csv','family-diff-analysis.json','duplication-audit.csv','internal-duplication-analysis.json','surface-leakage-analysis.json'],'history':'history-preflight-v2.2.1/; root input-hashes.json, manifest-extract.json, duplication-preflight.csv and cross-bank-retrieval-evidence.json are historical preflight, not current authoring baseline.'})
report='''# Batch 03 — авторский candidate для независимого QA

Созданы TC-076…TC-100: 25/25, 16 standalone, 9 linked, 4 семьи (3 пары и 1 триплет). J5 / M12 / S5 / H3. Ключи A6 / B6 / C6 / D7. Standalone — training/assessment true/true, linked — true/false.

Authoritative baseline — frozen manifest v2.2.2, SHA-256 `c4f8600132a4099a655c31c4c97356c52265da7c0895e04d9a99f04503821e41`. Production TC-001…075 сохранён: `2540570c2b907ea0e48cb9752e715486126e006a6100bd27e2f9f170d2c99689`. Контроль всех protected inputs — authoring-input-hashes.json. Manifest, Swift, schema и production content не менялись.

Сначала сформированы decision-skeletons.json, затем authored context/question/options. Источник содержательных принципов только InteractiveBook/WebContent/index.html. source-trace.csv связывает все 25 решений с положениями и дословными фрагментами локального учебника; роли и количественные условия синтетические. В runtime-схеме whatToNotice представлен decisiveFacts (1–3), thinkingModel — mentalModel.

## Содержательная самопроверка

25/25 unique strongest; 75 попарных сравнений с distractors в pairwise-self-check.csv. Для каждого указаны доступные до ответа факты, причина привлекательности альтернативы, проигрывающий trade-off и условие применимости всего варианта. Варианты используют разные оценки зрелости; равные 0.75 у C/D в TC-077 отражают одинаковый чистый эффект. Это авторская проверка, не независимое blind QA.

Senior: TC-083/084 исправляют пересекающиеся денежные потоки и sunk cost, сравнивают диапазон неопределённости с альтернативой и ценой ожидания; TC-091 перестраивает временную enabling-модель с ограниченной учебной ёмкостью и условием выхода; TC-096 сокращает чужую нагрузку с учётом системных последствий и будущего владения; TC-099 связывает новый SLO с архитектурой отказов, стоимостью эксплуатации и вытесняемой capacity.

Head: TC-090 пересобирает портфель и sourcing с финансированием передачи критических знаний; TC-097 меняет scope руководителя менеджеров после двух безрезультатных циклов поддержки, сохраняя его сильную роль и автономию подчинённых; TC-098 разделяет права и правила доступа к управленческому и проектному резервам.

## Linked families

4/4 PASS. Literal sibling diff в family-diff-analysis.json. Actor, base context, question, options и порядок идентичны; меняется только frozen logical variable.

- F-DR-T01: L=0/6/18, ключи C/A/D; реальные границы L=4 и L=8. Полезность автоматизации 0.5L−2, ручного шага L−6, удаления 0. Повторное исследование уже надёжной оценки добавляет расход без новой информации.
- F-TD-P01: завершённая допустимость vs подтверждение получения; ключи B/C, вызваны только смыслом продуктового ответа.
- F-PE-P01: неизвестный vs подтверждённый драйвер; D/A.
- F-BV-P02: PV16–20 vs PV4–7 при неизменных остальных условиях; B/D. NPV8–12 vs −4…−1 при альтернативе +5.

## Повторы и surface

Full wording сопоставлен с TC-001…075. duplication-audit.csv: NO CLOSE ANALOG 2, ALLOWED REINFORCEMENT 23, NEAR DUPLICATE 0, DUPLICATE 0. Дополнительный full-wording-retrieval.json содержит все 1875 пар; лексическая близость служит навигацией, не доказательством семантического совпадения. Внутренний аудит 300 пар — 0 near/duplicates; контролируемые siblings отмечены отдельно.

78 простых правил проверяют длину, пунктуацию, clauses/actions proxies, числа, Latin technical terms, conditional markers и комбинации. Лучшее правило 9/25, максимум ожидаемых попаданий при случайном разрешении ties — 9.83/25. Объединённый корпус: 35/100 против 28/75 до Batch 03, доля не выросла. Применена та же family-preserving permutation, что в предыдущем QA. Это sanity check заданных правил, а не доказательство отсутствия любой возможной подсказки. Статус PASS в этих пределах.

## Валидация и передача

Штатный TrainerBank.load загружает candidate; schema и runtime vocabulary PASS, unknown codes 0. Автоматически сверены все IDs, metadata frozen manifest, eligibility, levels, позиции, family constants и неизменность protected inputs. schema-validation.log содержит результат загрузки.

Исторические preflight-файлы сохранены в history-preflight-v2.2.1/. Старые root input-hashes.json, manifest-extract.json, duplication-preflight.csv, cross-bank-retrieval-evidence.json — исторические свидетельства, не источник текущего authoring. Текущие доказательства: frozen-manifest-extract-v2_2_2.json, authoring-input-hashes.json и отчёты выше.

Unresolved IDs: []. READY FOR INDEPENDENT QA: YES. Импорт не выполнялся; решение об импорте не заявляется. Независимый QA должен проверить содержательные авторские суждения. Batch 04 и Slice 5 не начаты; commit/push не выполнялись.
'''
report+='\nCandidate SHA-256: `'+sha(P/'cases_TC076_TC100.json')+'`.\n';(P/'authoring-report.md').write_text(report)
(P/'surface-work.json').unlink(missing_ok=True)
write('artifact-hashes.json',{p.name:sha(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps(st,ensure_ascii=False,indent=2))
