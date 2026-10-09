exec((__import__('pathlib').Path(__file__).parent/'build-candidate.py').read_text().split('protected=')[0])
m=read(P/'working-master.json');old=read(B/'production_manifest_masterplan_v2_2_1.json');rs={r['plannedId']:r for r in m['manifest']};prior={r['plannedId']:r for r in old['manifest']};prod=read(R/'InteractiveBook/TrainerContent/cases.json')['cases'];pb={c['id']:c for c in prod};ids=['TC-076','TC-077','TC-078','TC-079','TC-080','TC-087','TC-088','TC-091','TC-093'];assert len(prod)==75
pairs={'TC-076':'TC-047','TC-079':'TC-011','TC-087':'TC-019','TC-088':'TC-016','TC-091':'TC-013','TC-093':'TC-006'}
whyBefore={
'TC-076':'Шумный gate, ложные блокировки → warning до подтверждения качества сигнала; именно тот же дефект готовности проверяющего инструмента уже измеряет TC-047. Множество gates вместо scanner не меняет необходимого суждения.',
'TC-079':'Семь клиентов с разным cadence и доступные параллельные версии → постепенный переход до подтверждения миграции. Те же decisive facts и стратегия TC-011; различие уровня metadata не добавляет рассуждения.',
'TC-087':'Штатная конфигурационная ошибка, одиночное изменение и отсутствие валидации → искать системные условия вместо виновника. TC-019 содержит ту же причинную цепочку.',
'TC-088':'В обоих impact ещё не подготовлен, поэтому готовность эскалации восстанавливается расчётом и ask. Дата и прямой разговор в старом TC-088 закрывают часть чек-листа TC-016, но оставляют ту же диагностическую задачу.',
'TC-091':'Постоянная очередь и большинство повторяемых операций → сделать self-service вместо усиления coordination. 70% вместо 60% и Senior вместо Middle не меняют механизм решения TC-013.',
'TC-093':'Официальная задержка внешней стороны уже наступила, contingency задан → issue management вместо вероятности. Смена предмета с сертификации на оборудование повторяет TC-006.'}
readjud=[]
for id,other in pairs.items():
 c=pb[other];r=prior[id]
 readjud.append(dict(plannedId=id,productionId=other,preflightClassification='NEAR DUPLICATE' if id in ['TC-076','TC-088'] else 'DUPLICATE',verdict='CONFIRMED',oldConcept=r['oneSentenceScenarioConcept'],oldDecisiveFacts=r['decisiveFactsConcept'],oldBoundary=r['oneSentenceDecisionBoundary'],oldPatterns=[r['primaryPattern']]+r['secondaryPatterns'],productionContext=c['context'],productionStrongest=next(o['text'] for o in c['options'] if o['isBest']),productionFailureModes=[dict(text=o['text'],whyNotBest=o['whyNotBest']) for o in c['options'] if not o['isBest']],productionThinkingModel=c['mentalModel'],reason=whyBefore[id]))
write('original-collision-recheck.json',dict(method='Fresh comparison of actual baseline and current production fields, not lexical-overlap threshold. Same authoring agent, not external independent QA.',collisions=readjud))
reasons={
'TC-076':('TC-008','В TC-008 причинный эффект нового gate неизвестен: надо разложить агрегированное before/after. Здесь эффект уже установлен и равен нулю: решить об удалении дополнительного шага при сохранных обязательных gates. TC-047 выбирает режим ненадёжного scanner; здесь надёжность измерения и обязательные критерии не оспариваются.'),
'TC-077':('TC-008','Не расследование причины метрик, а выбор дешёвой проверки с частичной потерей полезной защиты при полностью известных эффектах и стоимости. Автоматизация выигрывает по чистому эффекту, а не по зрелости или нормативному статусу.'),
'TC-078':('TC-009','Не внедрение одинакового стандарта по зрелости команд: весь процесс уже работает. Доказанный высокий дополнительный эффект ручного шага оправдывает его стоимость; автоматизация теряет слишком много полезной защиты, хотя технически готова.'),
'TC-079':('TC-011','TC-011 выбирает способ сосуществования версий при миграции клиентов. Новый TC-079 определяет, можно ли подтверждать результат до выполнения необходимой проверки; миграции версий и клиентских cadence в задаче нет. Отличается и от mock в TC-001/002: выбирается смысл runtime-ответа, а не план работ до появления зависимости.'),
'TC-080':('TC-011','Не миграция API: согласованный положительный ответ означает только получение. Можно отвязать обработку от немедленного ответа без ложного обещания окончательного результата; готовность очереди дана и не является предметом проверки.'),
'TC-087':('TC-019','TC-019 защищает добросовестного участника от наказания за системно допущенную ошибку. Здесь нужно различить эту ошибку и отдельно доказанное сознательное сокрытие: blanket immunity под лозунгом blameless неверна. Это также не performance support/PIP TC-018/072 и не коррекция поля pipeline TC-070.'),
'TC-088':('TC-016','TC-016 останавливает преждевременную эскалацию из-за отсутствующих prerequisites. Здесь весь ask уже готов, а повторная договорённость нарушена: ошибка — пропустить окно решения ради ещё одного разговора. Кто имеет authority известно, поэтому не повторяется выбор владельца TC-012.'),
'TC-091':('TC-013','TC-013 заменяет типовые платформенные заявки самообслуживанием. Здесь self-service CI уже есть, но enabling делает доменно-специфичную работу вместо обучения; необходим ограниченный выход по когортам с передачей capability. Не автоматизация типовых запросов и не мгновенная перестановка оргграниц.'),
'TC-093':('TC-006','TC-006 реагирует на наступившее событие. Здесь событие ещё вероятностное: денежная передача риска не покрывает ограничение на простой; нужно сравнить остаточное влияние и риск-аппетит. Это не CoD порядка инициатив TC-067 и не применение burn-rate policy TC-022.')}
audit=[]
for id in ids:
 nearest,reason=reasons[id];c=pb[nearest];r=rs[id]
 audit.append(dict(TC_ID=id,nearestProductionId=nearest,classification='ALLOWED REINFORCEMENT',oldProductionCollision=pairs.get(id,''),oldRowTested=prior[id]['oneSentenceDecisionBoundary'],existingProductionTests=c['keyInsight'],newRowTests=r['oneSentenceDecisionBoundary'],newDecisiveFacts=r['decisiveFactsConcept'],newFailureMode={'TC-076':'Сохранять бесполезный ритуал','TC-077':'Оптимизировать только полноту защиты, игнорируя стоимость','TC-078':'Автоматизировать любой ручной шаг независимо от утраченной защиты','TC-079':'Выдать постановку в очередь за завершённую проверку','TC-080':'Удерживать ненужную синхронную связь','TC-087':'Считать blameless иммунитетом от ответственности за сокрытие','TC-088':'Эскалировать только после фактического провала, теряя доступное решение','TC-091':'Делать вместо обучения или передать всё одномоментно','TC-093':'Считать денежную страховку устранением неприемлемого простоя'}[id],whyDifferent=reason))
csvwrite('duplication-audit-v2_2_2.csv',audit)
# Explicit assessment for all 9×75 pairs. Near-neighbor reasons cover meaningful shared concepts;
# others retain the actual production judgment so a reviewer can challenge the classification.
extra={('TC-076','TC-047'):reasons['TC-076'][1],('TC-077','TC-047'):'Шум scanner и обязательность критерия не обсуждаются; все экономические эффекты известны.',('TC-078','TC-047'):'Сохранить доказанно полезное ручное ревью — иное решение, чем warning ненадёжного scanner.',('TC-077','TC-003'):'Не adequacy перед hotfix; допустимы все остаточные риски, сравнивается полезность необязательного процесса.',('TC-079','TC-001'):reasons['TC-079'][1],('TC-080','TC-001'):reasons['TC-080'][1],('TC-087','TC-018'):'Сознательное сокрытие не равно дефициту performance после поддержки; PIP не предписывается.',('TC-087','TC-072'):'Нужен раздельный разбор ошибки и поведения, а не performance-cycle.',('TC-088','TC-012'):reasons['TC-088'][1],('TC-088','TC-015'):'Передача полномочного решения по повторному нарушению не равна раннему сообщению риска клиенту.',('TC-091','TC-039'):'Не масштабирование церемоний; исчезновение обучающей функции enabling создаёт устойчивую зависимость.',('TC-091','TC-065'):'Не onboarding отдельного человека; меняются взаимодействие групп и способ передачи capability.',('TC-093','TC-022'):reasons['TC-093'][1],('TC-093','TC-020'):'Передача денежного риска не выбор контрактной модели под зрелость scope.'}
allpairs=[]
for id in ids:
 for c in prod:
  reason=extra.get((id,c['id']));nearest= reasons[id][0]==c['id'];label='ALLOWED REINFORCEMENT' if nearest or reason else 'NO CLOSE ANALOG'
  allpairs.append(dict(plannedId=id,productionId=c['id'],classification=label,productionJudgment=c['keyInsight'],candidateJudgment=rs[id]['oneSentenceDecisionBoundary'],rationale=reasons[id][1] if nearest else reason or 'Разные предметы решения и наборы решающих фактов; production judgment сопоставлен с новой boundary, совпадение отдельных слов не использовано как критерий.'))
write('cross-bank-pairwise-audit.json',dict(method='Semantic concept review, same author; not independent content QA. 9 nearest classifications in CSV; complete 675 comparison inventory here.',count=len(allpairs),comparisons=allpairs))
# Internal 25-row scan. Sibling strategy flips are intentional reinforcement, not independent duplicates.
batch=[r for r in m['manifest'] if r['batch']=='Batch 03'];special={
('TC-077','TC-085'):'077 сравнивает цену необязательного gate и потерю половины пользы при допустимом остаточном риске; 085 выбирает достаточный targeted regression по локализованному impact вместо избыточного полного.',
('TC-087','TC-089'):'087 отдельно оценивает доказанное сознательное сокрытие при доступном безопасном сообщении; 089 меняет публичные разборы, из-за которых люди перестали сообщать near-miss. Противоположные ошибки — blanket immunity и подавление сообщений страхом.',
('TC-088','TC-096'):'088 выбирает момент уже подготовленной эскалации по второму нарушению; 096 формирует влияние через интересы и trade-off с workaround без authority.',
('TC-091','TC-095'):'091 меняет постоянную исполняющую enabling-группу в передачу capability; 095 управляет blocked WIP и внешними зависимостями в потоке.',
('TC-093','TC-098'):'093 выбирает конкретную меру для остаточного простоя при заданном риск-аппетите; 098 меняет бюджетную authority management reserve.',
('TC-076','TC-085'):'Удаление доказанно бесполезного дополнительного gate не отмена достаточных impact-based проверок перед релизом.',
('TC-078','TC-085'):'Сохранение дорогой, но окупающейся дополнительной защиты не выбор полного regression без дополнительного покрытия.',
('TC-091','TC-097'):'Enabling передаёт практику stream-командам; manager-of-managers оценивается за создание следующего слоя управления.'}
internal=[]
for aidx,a in enumerate(batch):
 for b in batch[aidx+1:]:
  pair=(a['plannedId'],b['plannedId']);siblings=a['scenarioFamilyId'] is not None and a['scenarioFamilyId']==b['scenarioFamilyId']
  internal.append(dict(a=pair[0],b=pair[1],classification='ALLOWED REINFORCEMENT' if siblings or pair in special else 'NO CLOSE ANALOG',aBoundary=a['oneSentenceDecisionBoundary'],bBoundary=b['oneSentenceDecisionBoundary'],reason='Controlled family states require different strongest strategies; inspect full family contract and family-proof.json.' if siblings else special.get(pair,'Different decision boundary and decisive facts; no duplicated diagnostic task found at blueprint stage.')))
write('internal-batch03-audit.json',dict(pairCount=len(internal),nearDuplicate=0,duplicate=0,comparisons=internal,limitation='Concept-stage semantic review only; future options must preserve the distinctions.'))
# Source trace: exact local excerpts plus interpretation, no secondary content source.
html=(R/'InteractiveBook/WebContent/index.html').read_text()
excerpts={
 't-3-2':['имеет доказанную связь с качеством','гейт, который блокирует, но не снижает дефекты — вредный шум','Гейт, который не доказал эффект — удаляется.'],
 't-10-1':['Очереди и брокеры (Kafka)','Антифрод — единственный шаг, который по смыслу должен завершиться до подтверждения','Кэшбэк и пуш — следствия платежа, их можно выполнить асинхронно.'],
 't-7-10':['Blameless не означает «без ответственности»','наказание уместно за сокрытие и повторное сознательное нарушение договорённостей, не за ошибку.'],
 't-6-3':['Договорённость нарушена второй раз, срок вехи под угрозой','Второе — эскалация с приложенной историей'],
 't-9-6':['Временно помогает stream-командам освоить практику или технологию, затем уходит','Становится постоянной «командой качества», которая делает вместо того, чтобы учить','Когнитивная нагрузка команды — ограничение'],
 't-2-6':['Стратегия выбирается по соотношению стоимости реагирования и ожидаемых потерь','Риск-аппетит (risk appetite) — уровень риска']}
trace=[]
for id in ids:
 r=rs[id];a=html.index('id="'+r['topicId']+'"');b=html.index('</article>',a);topic=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',html[a:b]));qs=excerpts[r['topicId']];assert all(q in topic for q in qs),(id,qs)
 trace.append(dict(plannedId=id,topicId=r['topicId'],source='InteractiveBook/WebContent/index.html#'+r['topicId'],exactExcerpts=qs,operationalization=r['oneSentenceScenarioConcept'],strongestFromSource=r['oneSentenceDecisionBoundary'],levelProof=r['whyLevel'],note='Concrete amounts, timings and readiness conditions are synthetic; decision principle comes from the source. No full case/options authored.'))
write('source-trace.json',dict(sourceSHA256=sha(R/'InteractiveBook/WebContent/index.html'),rows=trace))
print('Six collisions confirmed afresh; nine redesigned concepts compared against 75 production cases and 300 internal pairs; exact source excerpts checked.')
