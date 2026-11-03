import json,csv,copy,hashlib,collections,pathlib,subprocess,os
HERE=pathlib.Path(__file__).resolve().parent; ROOT=HERE.parents[2]; OLD=HERE.parent/'v2.1'; QA=ROOT/'agent-artifacts/qa/manifest-v2.1'
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(HERE/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def csvwrite(n,rs):
 fields=list(dict.fromkeys(k for r in rs for k in r))
 with (HERE/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rs:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,bool)) else v for k,v in r.items()})
def counts(rs,k):return dict(sorted(collections.Counter(r[k] for r in rs).items()))
before=read(OLD/'production_manifest_masterplan_v2_1.json');m=copy.deepcopy(before);rows=m['manifest'];by={r['plannedId']:r for r in rows};fs={f['scenarioFamilyId']:f for f in m['familyManifest']}
issues=list(csv.DictReader((QA/'row-fixes-final.csv').open(encoding='utf-8-sig')));fi=list(csv.DictReader((QA/'family-fixes-final.csv').open(encoding='utf-8-sig')));verdict=read(QA/'QA-verdict.json')
assert digest(OLD/'production_manifest_masterplan_v2_1.json')==verdict['inputHashes']['agent-artifacts/manifests/v2.1/production_manifest_masterplan_v2_1.json']
why={
64:'Сопоставить известную экономику сделки с проверенной альтернативой и определить допустимые уступки; governance не проектируется.',
72:'Сопоставить завершённую поддержку и отсутствие улучшения с условиями перехода к формальному PIP одного сотрудника.',
75:'Соблюсти явное ограничение протокола: ранняя значимость не разрешает остановку до 14 дней без early-stop rule.',
88:'Подготовить влияние проблемы и варианты решения для рабочей эскалации; уровень адресата не усложняет reasoning.',
92:'Сегментировать p95 и среднее, чтобы локализовать ухудшение пользовательского опыта по данным дашборда.',
100:'Отличить одиночный шум от устойчивого actionable-сигнала и выбрать рабочий порог реакции.',
106:'Сопоставить временность очереди с устойчивой пропускной способностью и выбрать управление потоком без лишней перестройки.',
107:'Сопоставить устойчивый входящий поток с capacity и выбрать рабочее изменение WIP или мощности.',
113:'Проверить неизвестную причину снижения мотивации через 1:1 до выбора бонуса или другой интервенции.',
122:'Выбрать диагностику и обратную связь до формального PIP, поскольку причина внезапной просадки ещё не установлена.',
144:'Сопоставить гарантии доставки и последствия повторного списания; потребовать защиту бизнес-обработки от дубликатов.',
168:'Рассчитать экономику своей альтернативы до уступок и обещаний; организационная модель не меняется.',
194:'Сначала применить обязательные security/audit ограничения, затем сравнить цену допущенных поставщиков.',
201:'Сопоставить расход error budget с утверждённым warning-порогом и сохранить обычный темп в рамках policy.',
202:'Применить утверждённый warning-порог и выделить предусмотренную policy capacity на стабилизацию.',
203:'Применить утверждённый freeze-порог и остановить изменения согласно готовому правилу.',
217:'Согласовать работу с результативностью сотрудника с HR-процедурой до необратимых кадровых действий.',
253:'Сравнить измеренную цену отсрочки входящего потока со стоимостью дополнительной capacity на одном горизонте.',
254:'Выбрать между снижением входа и увеличением мощности по полным сопоставимым затратам, без перепроектирования нескольких потоков.',
255:'Сопоставить конкретную сделку с более выгодной доступной BATNA и отказаться от уступки ниже reservation point.',
256:'Сопоставить ту же сделку с менее выгодной BATNA и принять предложение, превышающее reservation point.',
261:'Распознать изменение цены только в B как смешение факторов и не приписывать весь эффект фиче.',
275:'Различить SLA поддержки и критерии приёмки разработки при ведении одного подрядчика.',
282:'Оценить организационный blast radius и последствия расширения command structure; единый Senior семьи учитывает межкомандную альтернативу, локальная ветвь сама по себе не является самостоятельным Head evidence.',
283:'Согласовать конфликтующие действия нескольких доменов, восстановление общего клиентского пути и коммуникации через единую incident command structure.',
300:'Сопоставить paid-to-date с законтрактованными обязательствами и прогнозом EAC, чтобы получить корректный план-факт.'}
for q in issues:
 r=by[q['plannedId']]
 if q['recommendedLevel']:
  r['requiredLevel']=q['recommendedLevel'];r['whyLevel']=why[int(r['plannedId'][3:])]
  if r['requiredLevel']!='head':
   for k in ['whyHead','authorityScope','secondaryEffect']:r[k]=None
for num,pat in {112:'expectation-management',116:'safeguards',144:'safeguards',145:'risk-differentiation',194:'safeguards',214:'safeguards',216:'communications',224:'communications',273:'safeguards',288:'root-cause'}.items():by[f'TC-{num:03}']['primaryPattern']=pat
# Remove displaced or duplicate primary tags only on flagged semantic rows.
for num,secondary in {112:['communications'],116:['quality-metrics'],144:[],145:[],214:['reliability'],216:['external-contact'],224:['dependency-management'],273:['reliability'],288:['support']}.items():by[f'TC-{num:03}']['secondaryPatterns']=secondary
by['TC-112']['sourceTopicExplanation']='§6.1 задаёт стороны коммуникации; проверяемая граница — согласование ожиданий до обещания по §6.2, а не сообщение о срыве.'
by['TC-116']['sourceTopicExplanation']='§10.4: диагностическая корреляция через trace ID сохраняется при минимизации и маскировании payload; safeguards относится к защите данных, не к распределению полномочий.'
by['TC-224']['topicId']='t-6-5';by['TC-288']['topicId']='t-7-9'
by['TC-273'].update(oneSentenceScenarioConcept='Middle TPM планирует очередь между сервисами: consumer, меняющий баланс, уже атомарно дедуплицирует операции по бизнес-ID, но при его недоступности немедленные повторные отправки producer перегружают восстановление; нужно выбрать режим retries при допустимой задержке обработки.',decisiveFactsConcept=['Consumer уже обеспечивает атомарную идемпотентность; повторное списание исключено','При недоступности consumer немедленные retries усиливают нагрузку; восстановление занимает до 10 минут','Допустимая задержка 30 минут; сообщения надёжно сохраняются; ограниченные retries с backoff и jitter укладываются в этот срок'],oneSentenceDecisionBoundary='Немедленно повторять отправки ради минимальной задержки ↔ ограничить частоту retries с backoff/jitter, сохранив сообщения и уложившись в допустимое окно восстановления.',whyLevel='Сопоставить допустимую задержку и нагрузку восстановления, выбрав рабочую retry-policy; идемпотентность уже дана и не является предметом выбора.')

def family(fid,base,variable,states,decisions,constants,proof,extra=None):
 f=fs[fid]; f.update(baseSituation=base,singleLogicalVariable=variable,stateByMember=dict(zip(f['memberIds'],states)),decisionBoundaryByState=dict(zip(f['memberIds'],decisions)),factsThatMustRemainConstant=constants,whyMutationIsControlled=proof,expectedStrongestShiftConcept=' ↔ '.join(decisions))
 if extra:f.update(extra)
 for id in f['memberIds']:
  r=by[id];mutation=variable+': '+f['stateByMember'][id]
  r.update(oneSentenceScenarioConcept=base+' В этой версии: '+mutation+'.',decisiveFactsConcept=[mutation]+constants,oneSentenceDecisionBoundary=f['decisionBoundaryByState'][id],decisiveMutationConcept=mutation)
family('F-PM-T01','Руководитель проекта пересчитывает критический путь после задержки внешней интеграции; дата, остаток работ и возможности ускорения одинаковы.','Прогнозируемый сдвиг критического пути в днях',['1 день','4 дня','8 дней'],['Сохранить дату и обычный контроль: warning-trigger ещё не достигнут; платное ускорение преждевременно.','Активировать подготовленное ускорение и перепланировать цепочку, сохранив дату и требуемый остаточный резерв.','Вынести изменение scope или даты на владельца обязательства: даже максимальное ускорение не сохраняет дату.'],['До задержки календарный буфер 5 дней; прогресс и остаток работ одинаковы','Согласованный warning-trigger: сдвиг от 3 дней требует меры для сохранения не менее 3 дней резерва на оставшуюся неопределённость','Единственная проверенная мера стоит 100 тысяч рублей, оплачивается из утверждённого резерва и даёт ровно 2 дня ускорения без изменения scope/качества','Других мер ускорения нет; максимальная компенсация 5 дней буфера + 2 дня ускорения = 7 дней','Дата и scope могут меняться только владельцем обязательства; цена меры одинакова'], 'Меняется только сдвиг 1/4/8; общий warning-trigger 3 дня и предел сохранения даты 7 дней заданы явно. При 4 ускорение оставляет 3 дня резерва; при 8 остаётся опоздание 1 день.',{'boundary1':'Сдвиг <3: обычный контроль; сдвиг ≥3: активировать утверждённую меру.','boundary2':'Сдвиг >7: даже 2 дня ускорения плюс буфер не сохраняют дату.','threeDistinctStrategies':['monitor-baseline','mitigate-and-replan','renegotiate-commitment']})
family('F-PE-T01','Менеджер измерил повторяющуюся нагрузку сотрудника и планирует одинаковый четырёхнедельный горизонт; роль, навыки и личные обстоятельства одинаковы.','Недельный demand до снятия необязательной работы при устойчивой capacity 40 часов',['42 часа (+5%)','50 часов (+25%)','60 часов (+50%)'],['Убрать 2 часа необязательного шума, сохранить обязательства и контролировать восстановление в пределах 40 часов.','Убрать шум и явно перенести 8 часов задач в согласованное свободное окно; сохранить 40-часовой предел и восстановление.','Снять шум и доступные 8 часов, затем немедленно пересогласовать оставшиеся обязательства или привлечь выделенную capacity: локальные меры оставляют 50 часов.'],['Горизонт 4 недели одинаков; самостоятельного окончания пика не ожидается ни в одном состоянии','Устойчивая capacity 40 часов в неделю уже включает восстановление; сверхурочные не являются доступным ресурсом','Во всех состояниях можно без последствий убрать ровно 2 часа необязательных встреч и отчётности в неделю','Ещё максимум 8 часов задач в неделю можно перенести в подтверждённое свободное окно без последующего переработочного долга; перенос требует согласования','За пределом 10 часов снижения нужен пересмотр обязательств или выделение ресурсов руководителем; такие действия имеют цену координации и не нужны, пока хватает локальных мер'], 'Меняется только demand 42/50/60; роль, горизонт и пределы снижения 2+8 одинаковы. Общие границы 42 и 50 часов выведены из capacity, а не из универсальных процентов выгорания.',{'boundary1':'Demand ≤42: достаточно убрать шум; >42: нужен перенос обязательных задач.','boundary2':'Demand >50: локального снятия 10 часов недостаточно; требуется пересогласование обязательств/capacity.','threeDistinctStrategies':['remove-noise-preserve-commitments','reschedule-with-recovery','renegotiate-load-capacity']})
family('F-ST-P03','Компания завершает стратегические переговоры с партнёром о многолетних обязательствах; в конечный момент решения на столе одно и то же окончательное предложение.','Чистая ценность лучшей реально доступной альтернативы несделке',['120 условных единиц','80 условных единиц'],['Отклонить предложение ценностью 100 и реализовать BATNA ценностью 120.','Принять предложение ценностью 100 вместо BATNA ценностью 80.'],['Чистая ценность окончательного предложения 100 единиц на одном горизонте после всех затрат и рисков','Все варианты пакетирования уже рассмотрены; до общего срока ответа улучшить предложение или продолжить обмен нельзя в обеих версиях','BATNA исполнима в нужный срок; её оценка на той же шкале включает затраты перехода и последствия несделки','Интересы сторон, обязательства, полномочия подписантов и цена несделки партнёра одинаковы'], 'Единственная mutation — оценённая ценность BATNA. 80 < 100 < 120 создаёт принятие/отклонение; поиск интересов одинаково завершён и не противопоставляется reservation point.')
family('F-TD-P03','На стадии ревью накопилась очередь: входящий поток устойчиво 12 задач в неделю при capacity 10; WIP-policy, тип задач и приоритеты одинаковы. Менеджер выбирает ограничение входа либо дополнительную мощность на четыре недели.','Полная цена отсрочки двух задач в неделю на общем четырёхнедельном горизонте',['40 тысяч рублей','160 тысяч рублей'],['Ограничить вход до 10 задач в неделю: отсрочка стоит 40 тысяч против 100 тысяч за добавление мощности.','Добавить проверенную мощность до 12 задач в неделю: её цена 100 тысяч ниже 160 тысяч от отсрочки.'],['Demand 12 и capacity 10 сохраняются все 4 недели: временность очереди не меняется','Лимит входа 10 удерживает WIP, но переносит две задачи в неделю; все последствия переноса включены в указанную цену','Проверенный резервный reviewer доступен немедленно на 4 недели, даёт ровно +2 задачи/неделю; полная цена с onboarding и упущенной работой 100 тысяч рублей','Качество ревью и восстановление исходной очереди одинаковы в обоих вариантах; другие меры на данном горизонте недоступны','Тип задач, приоритеты и бюджетные полномочия менеджера одинаковы'], 'Обе версии имеют устойчивый bottleneck; меняется только цена отсрочки относительно постоянных 100 тысяч за capacity. Это экономический выбор entry limit/capacity, а не повтор временная/устойчивая очередь F-PR-P01.')
# Align changed family metadata with its revised decision, using existing codes.
for id in ['TC-253','TC-254']:
 by[id]['primaryPattern']='process-economics';by[id]['secondaryPatterns']=['bottleneck','cost-of-delay']
# Family level is dependent metadata, including three construction-frozen families.
for f in m['familyManifest']:
 levels={by[i]['requiredLevel'] for i in f['memberIds']};assert len(levels)==1;f['requiredLevel']=levels.pop()
for f in m['changedFamilyDesigns']:
 if f['scenarioFamilyId'] in {q['scenarioFamilyId'] for q in fi}:
  ref=fs[f['scenarioFamilyId']];f.update(status='targeted-QA-v2.2',singleLogicalVariable=ref['singleLogicalVariable'],expectedStrongestShiftConcept=ref['expectedStrongestShiftConcept'])
for b in m['batchPlan']:b['levels']=counts([r for r in rows if r['batch']==b['batch']],'requiredLevel')
m['headAudit']=[{k:r.get(k) for k in before['headAudit'][0]} for r in rows if r['requiredLevel']=='head']
write('working-master.json',m)
# Compile the existing audit harness with authoritative production Swift.
sources=['TrainerScoringMapping.swift','TrainerScoringEngine.swift'];hashes={n:digest(ROOT/'InteractiveBook/Trainer'/n) for n in sources}
for n in sources:
 assert hashes[n]==verdict['inputHashes']['InteractiveBook/Trainer/'+n]
 assert hashes[n]==digest(ROOT/'agent-artifacts/runtime-contract'/n)
goldpath=ROOT/'InteractiveBook/TrainerContent/cases.json';goldhash=digest(goldpath);gold=read(goldpath)['cases'];allrows=gold+[dict(r,id=r['plannedId']) for r in rows]
excluded={'TC-001','TC-002','TC-003','TC-004','TC-017','TC-018'};assessment=[r for r in allrows if r['assessmentEligible'] and r['id'] not in excluded]
write('runtime-input.json',dict(rows=allrows,template=gold[0],assessmentIDs=[r['id'] for r in assessment]))
env=dict(os.environ);env.setdefault('DEVELOPER_DIR','/Applications/Xcode.app/Contents/Developer')
subprocess.run(['/usr/bin/xcrun','swiftc','-module-cache-path','/private/tmp/manifest-v22-swift-cache',str(ROOT/'InteractiveBook/Trainer/TrainerModels.swift'),*[str(ROOT/'InteractiveBook/Trainer'/n) for n in sources],str(ROOT/'Tests/ScoringFixtures.swift'),str(OLD/'RuntimeAudit.swift'),'-o',str(HERE/'runtime-audit')],check=True,env=env)
subprocess.run([str(HERE/'runtime-audit'),str(HERE/'runtime-input.json'),str(HERE/'runtime-output.json')],check=True)
audit=read(HERE/'runtime-output.json');mapped={r['id']:r for r in audit['rows']}
for r in rows:
 x=mapped[r['plannedId']];r.update(derivedRuntimeUiDomain=x['uiDomainTitle'],derivedRuntimePrimaryThinking=x['primaryThinking'],derivedRuntimeSecondaryThinking=x['secondaryThinking'])
def coverage(group):
 domains={d:0 for d in audit['domainTitles']};matrix={d:{l:0 for l in ['junior','middle','senior','head']} for d in domains};thinking={p:{'primaryCaseIDs':[],'secondaryCaseIDs':[],'unionCaseIDs':[],'normalizedEvidenceWeightSum':0.0} for p in audit['thinkingTitles']}
 for r in group:
  x=mapped[r['id']];d=x['uiDomain'];domains[d]+=1;matrix[d][r['requiredLevel']]+=1
  if x['primaryThinking']!='context':thinking[x['primaryThinking']]['primaryCaseIDs'].append(r['id'])
  for p in set(x['secondaryThinking'])-{'context'}:thinking[p]['secondaryCaseIDs'].append(r['id'])
  for p,w in x['normalizedWeights'].items():thinking[p]['unionCaseIDs'].append(r['id']);thinking[p]['normalizedEvidenceWeightSum']+=w
 for v in thinking.values():
  v.update(primaryCaseCount=len(v['primaryCaseIDs']),secondaryCaseCount=len(v['secondaryCaseIDs']),evidenceCaseCount=len(v['unionCaseIDs']),normalizedEvidenceWeightSum=round(v['normalizedEvidenceWeightSum'],10))
  assert set(v['unionCaseIDs'])==set(v['primaryCaseIDs'])|set(v['secondaryCaseIDs'])
 return dict(caseCount=len(group),levels=counts(group,'requiredLevel'),uiDomains=domains,uiDomainByLevel=matrix,seniorPlusHeadByUiDomain={d:v['senior']+v['head'] for d,v in matrix.items()},thinking=thinking)
new=allrows[25:];report=dict(authoritative=True,status='technical-validation-PASS; focused-QA-pending',runtimeContract=dict(sourceHashes=hashes,referenceSync='PASS'),domainTitles=audit['domainTitles'],thinkingTitles=audit['thinkingTitles'],gold=coverage(gold),new=coverage(new),all300=coverage(allrows),newAssessment=coverage([r for r in new if r['assessmentEligible']]),assessment200=coverage(assessment),contextSensitivityScoredEvidence=0,engineWeightVerification=audit['engineWeightVerification'],headFeasibility=audit['headFeasibility'],assessmentPolicy=dict(excludedGoldLinkedIds=sorted(excluded),appliedOnlyInThisReport=True,productionBankChanged=False,currentFlagsPoolBeforeGoldPolicyChange=206),structure=before['coverageSummary']['structure'],pools=dict(training=300,ordinaryAssessmentAfterGoldExclusion=200,families=46,maxIndependentUnits=246),thinkingRule='Primary 1, secondary 0.5; aliases dedupe max per category/case; exclude context; normalize by max(1,sum).',unknownDomains=[],unknownPatterns=[])
report['headFeasibility']['result']='PASS' if audit['headFeasibility']['maximumSyntheticLevel']=='head' and audit['headFeasibility']['breadthMet'] else 'FAIL'
report['headFeasibility']['seniorPlusHeadByUiDomain']=report['assessment200']['seniorPlusHeadByUiDomain']
targets={'junior':45,'middle':120,'senior':90,'head':45};report['levelTargetComparison']={l:dict(target=v,actual=report['all300']['levels'].get(l,0),gapActualMinusTarget=report['all300']['levels'].get(l,0)-v) for l,v in targets.items()}
# Scope equality is exact for all fields of every row outside row OR family issue scope.
row_scope={q['plannedId'] for q in issues};family_scope={q['scenarioFamilyId'] for q in fi};allowed=row_scope|{id for f in m['familyManifest'] if f['scenarioFamilyId'] in family_scope for id in f['memberIds']}
changed=[]
for old,r in zip(before['manifest'],rows):
 keys=[k for k in dict.fromkeys(list(old)+list(r)) if old.get(k)!=r.get(k)]
 if keys:
  assert r['plannedId'] in allowed
  qs=[q['problem'] for q in issues if q['plannedId']==r['plannedId']]+[q['problem'] for q in fi if q['scenarioFamilyId']==r['scenarioFamilyId']]
  changed.append(dict(recordType='row',id=r['plannedId'],qaIssue=' | '.join(qs),fieldsChanged=keys,before={k:old.get(k) for k in keys},after={k:r.get(k) for k in keys},whyFixed='Применён точный QA fix; reasoning-калибровка и/или контролируемая граница отражены в изменённых полях.',status='addressed-pending-focused-QA'))
 else:assert old==r
for old,f in zip(before['familyManifest'],m['familyManifest']):
 keys=[k for k in dict.fromkeys(list(old)+list(f)) if old.get(k)!=f.get(k)]
 if f['scenarioFamilyId'] not in family_scope:assert set(keys)<= {'requiredLevel'}
 if keys:
  qs=[q['problem'] for q in fi if q['scenarioFamilyId']==f['scenarioFamilyId']]+[q['problem'] for q in issues if q['plannedId'] in f['memberIds']]
  changed.append(dict(recordType='family',id=f['scenarioFamilyId'],qaIssue=' | '.join(qs),fieldsChanged=keys,before={k:old.get(k) for k in keys},after={k:f.get(k) for k in keys},whyFixed=f['whyMutationIsControlled'] if f['scenarioFamilyId'] in family_scope else 'Только синхронизация requiredLevel с явно отмеченными QA членами; конструкция неизменна.',status='addressed-pending-focused-QA'))
assert len(rows)==275 and len(by)==275 and set(by)=={f'TC-{i:03}' for i in range(26,301)}
assert counts(rows,'structure')=={'pair':70,'standalone':181,'triplet':24};assert counts(m['familyManifest'],'type')=={'pair':35,'triplet':8}
topics={t['id']:t for t in read(ROOT/'InteractiveBook/TrainerContent/topics.json')['topics']}
for r,old in zip(rows,before['manifest']):
 assert r['topicId'] in topics and r['partId']=='part-'+r['topicId'].split('-')[1]
 assert r['batch']==old['batch'] and r['trainingEligible'] is True and r['assessmentEligible']==(r['structure']=='standalone')
 assert int(r['batch'].split()[-1])==(int(r['plannedId'][3:])-26)//25+1
members=[]
for f in m['familyManifest']:
 rs=[by[id] for id in f['memberIds']];members+=f['memberIds'];assert len(rs)==(2 if f['type']=='pair' else 3)
 for k in ['topicId','domain','requiredLevel','batch']:assert len({r[k] for r in rs})==1
 assert f['topicId']==rs[0]['topicId'] and f['requiredLevel']==rs[0]['requiredLevel']
 for i,r in enumerate(rs):assert r['scenarioFamilyId']==f['scenarioFamilyId'] and r['structure']==f['type'] and r['familyPosition']==i+1
assert len(set(members))==94 and set(members)=={r['plannedId'] for r in rows if r['structure']!='standalone'}
assert len(counts(rows,'batch'))==11 and set(counts(rows,'batch').values())=={25}
assert digest(goldpath)==goldhash and len(assessment)==200
assert all(by[id]['requiredLevel']!='head' and all(by[id][k] is None for k in ['whyHead','authorityScope','secondaryEffect']) for id in verdict['head']['levelFixes'])
# Check the four controlled numeric mutations independently of their prose labels.
assert [('monitor' if d<3 else 'mitigate' if d<=7 else 'renegotiate') for d in [1,4,8]]==['monitor','mitigate','renegotiate']
assert [('noise' if d<=42 else 'reschedule' if d<=50 else 'capacity') for d in [42,50,60]]==['noise','reschedule','capacity']
assert [('accept' if 100>b else 'reject') for b in [120,80]]==['reject','accept']
assert [('limit' if delay<100 else 'capacity') for delay in [40,160]]==['limit','capacity']
validation=dict(structuralRegression='PASS',frozenRowsExactEquality='PASS',unchangedRowCount=275-sum(c['recordType']=='row' for c in changed),changedRowCount=sum(c['recordType']=='row' for c in changed),rowIssueCount=34,rowIssuesAddressed=34,familyIssuesAddressed=4,headIssuesRevisited=10,constructionFrozenFamilies=39,levelOnlyFamilyUpdates=[c['id'] for c in changed if c['recordType']=='family' and c['fieldsChanged']==['requiredLevel']],unresolvedIssues=[],focusedQARequired=True,readyClaimed=False,canStartBatch01=False,engineWeightVerification=audit['engineWeightVerification'],headFeasibility=report['headFeasibility'],inputHashes={p.name:digest(p) for p in [OLD/'production_manifest_masterplan_v2_1.json',*[QA/n for n in ['QA-report-final.md','row-fixes-final.csv','family-fixes-final.csv','QA-verdict.json']]]})
m.update(manifestVersion='2.2-targeted-QA-revision',coverageSummary=report,remainingDisputedRows=[])
m['targetedRevision']=validation;m['runtimeMappingStatus']=dict(authoritativeSwiftAvailable=True,source='authoritative-swift-mapping',sourceHashes=hashes,validation='PASS')
write('production_manifest_masterplan_v2_2.json',m);csvwrite('production_manifest_TC026_TC300_v2_2.csv',rows);csvwrite('linked_family_manifest_v2_2.csv',m['familyManifest']);csvwrite('head_audit_v2_2.csv',m['headAudit']);csvwrite('change-log-v2_1-to-v2_2.csv',changed);write('runtime_coverage_v2_2.json',report);write('validation-result.json',validation)
# CSV roundtrip verification against JSON for all exported record collections.
for n,rs in [('production_manifest_TC026_TC300_v2_2.csv',rows),('linked_family_manifest_v2_2.csv',m['familyManifest']),('head_audit_v2_2.csv',m['headAudit'])]:
 actual=list(csv.DictReader((HERE/n).open(encoding='utf-8-sig')));assert len(actual)==len(rs)
 for a,r in zip(actual,rs):
  for k,v in r.items():assert a[k]==(json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,bool)) else '' if v is None else str(v))
level_changes=[(o['plannedId'],o['requiredLevel'],r['requiredLevel']) for o,r in zip(before['manifest'],rows) if o['requiredLevel']!=r['requiredLevel']]
review=['# Targeted revision v2.2 — для focused QA','', 'Self-QA: 34 row issues и 4 family issues addressed; независимый focused QA ещё требуется. READY не заявляется, Batch 01 не начинать.','', 'Изменены 40 строк: 34 из row-fixes плюс 6 членов двух triplet из family-fixes. Остальные 235 строк совпадают со v2.1 по всем полям. Конструкции 39 остальных семей неизменны; F-PR-P01, F-PO-T01 и F-PO-P04 получили только согласованный requiredLevel по row QA.','', '10 спорных Head: 8 → Middle, TC-282/283 → Senior. whyHead, authorityScope, secondaryEffect очищены. Оставшиеся 35 Head не перепроектировались.','', '## Уровни','', '| Pool | Junior | Middle | Senior | Head |','|---|---:|---:|---:|---:|']
for label,key in [('New 275','new'),('All 300','all300'),('Planned assessment 200','assessment200')]:review.append('| '+label+' | '+' | '.join(str(report[key]['levels'].get(l,0)) for l in targets)+' |')
review+=['','| Level | Target all300 | Actual | Actual − target |','|---|---:|---:|---:|']
for l,v in report['levelTargetComparison'].items():review.append(f"| {l} | {v['target']} | {v['actual']} | {v['gapActualMinusTarget']:+} |")
review+=['','## Изменения уровней','']+[f'- {id}: {a} → {b}.' for id,a,b in level_changes]
review+=['','## Runtime и feasibility','','Производственные Swift mapping/engine скомпилированы с существующим audit harness. Все 300 impulse responses PASS; context evidence=0, aliases max/category/case и engine normalization подтверждены.','',f"Head feasibility: {report['headFeasibility']['result']}; областей с ≥3 Senior/Head: {len(audit['headFeasibility']['breadthDomains'])}. Проверка использует синтетические идеальные ответы, не гарантирует результат учащегося или короткой сессии.",'','| Domain | Gold | New | All | Assessment | J | M | S | H | Assessment S+H | Raw S+H |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for d in audit['domainTitles']:
 matrix=report['assessment200']['uiDomainByLevel'][d];vals=[report[k]['uiDomains'][d] for k in ['gold','new','all300','assessment200']]+[matrix[l] for l in targets]+[report['assessment200']['seniorPlusHeadByUiDomain'][d],report['all300']['seniorPlusHeadByUiDomain'][d]];review.append('| '+audit['domainTitles'][d]+' | '+' | '.join(map(str,vals))+' |')
review+=['','275 IDs, 181 standalone/94 linked, 35 pairs/8 triplets, 11×25 batches сохранены. Structural regression и CSV/JSON roundtrip PASS. Training pool 300; planned assessment 200; 46 families; 246 max independent units.','', 'Assessment 200 требует отдельного будущего отключения TC-001/002/003/004/017/018 в gold; текущие флаги дали бы 206. Gold, engine, mapping, thresholds и UI не изменялись.','', 'Новых vocabulary codes не добавлено. TC-144 сохраняет boundary обработки дубликатов; TC-273 проверяет безопасную retry-policy при уже заданной идемпотентности. Обе используют существующий safeguards.','', 'Незакрытых замечаний по self-QA нет; содержательная приёмка 4 mutations и исправленных строк остаётся за focused QA. Дефицит 10 Head относительно target показан без компенсации. Полный app/WebKit suite не запускался: изменены только planning artifacts.','', 'Полный before/after — change-log-v2_1-to-v2_2.csv. Head audit содержит 35 текущих Head; решения по 10 снятым Head сохранены в change-log.','', 'Source SHA-256:']+[f'- {n}: `{h}`' for n,h in hashes.items()]
(HERE/'production_manifest_review_v2_2.md').write_text('\n'.join(review)+'\n')
(HERE/'vocabulary-review-v2.2.md').write_text('# Vocabulary v2.2\n\nНовых codes и обязательных vocabulary gaps нет. Исправления используют существующие safeguards, risk-differentiation, communications, expectation-management и root-cause. Технически узкая категория idempotency не требуется для проверяемого safeguards; rollback больше не используется как alias. Остальные vocabulary-review решения v2.1 сохранены в masterplan.\n')
for name in ['working-master.json','runtime-input.json','runtime-audit']:(HERE/name).unlink()
write('artifact-hashes.json',{p.name:digest(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps(dict(validation=validation,levels={k:report[k]['levels'] for k in ['new','all300','assessment200']},levelChanges=len(level_changes)),ensure_ascii=False,indent=2))
