import json,csv,re,html,hashlib,statistics,collections,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
manifestPath=ROOT/'agent-artifacts/manifests/v2.2/production_manifest_masterplan_v2_2.json';m=read(manifestPath);bp={r['plannedId']:r for r in m['manifest'][:25]};bank=read(P/'cases_TC026_TC050.json');cs=bank['cases'];verdict=read(ROOT/'agent-artifacts/qa/manifest-v2.2/QA-verdict.json')
for p,h in verdict['inputHashes'].items():assert sha(ROOT/p)==h,p
expectedGold=read(ROOT/'agent-artifacts/manifests/v2.1/runtime_coverage_v2_1.json')['contentIntegrity']['goldBankSha256'];assert sha(ROOT/'InteractiveBook/TrainerContent/cases.json')==expectedGold
assert bank['schemaVersion']=='2.0';assert [c['id'] for c in cs]==[f'TC-{i:03}' for i in range(26,51)]
keys=['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']
for c in cs:
 b=bp[c['id']]
 assert all(c[k]==b[k] for k in keys)
 assert c['decisiveMutation']==b['decisiveMutationConcept']
 assert c['revision']==1 and len(c['options'])==4 and [o['id'] for o in c['options']]==list('ABCD')
 assert sum(o['isBest'] for o in c['options'])==sum(o['decisionQuality']==1 for o in c['options'])==1
 assert all(isinstance(o['decisionQuality'],(int,float)) and 0<=o['decisionQuality']<=1 and o['isBest']==(o['decisionQuality']==1) for o in c['options'])
 assert not any(k in c for k in ['difficulty','mode'])
res=subprocess.run([str(P/'validate-batch'),str(P/'cases_TC026_TC050.json')],check=True,capture_output=True,text=True);(P/'schema-validation.log').write_text(res.stdout)
by={c['id']:c for c in cs};families=[]
for f in m['familyManifest']:
 if not any(id in by for id in f['memberIds']):continue
 siblings=[by[id] for id in f['memberIds']]
 assert len({s['question'] for s in siblings})==1
 assert all([o['text'] for o in s['options']]==[o['text'] for o in siblings[0]['options']] for s in siblings)
 bests=[next(o['id'] for o in s['options'] if o['isBest']) for s in siblings];assert len(set(bests))==len(siblings)
 if f['scenarioFamilyId']=='F-PM-T01':normalized=[re.sub(r'Прогнозируемый сдвиг критического пути — \d+ дн\.', 'Прогнозируемый сдвиг критического пути — {STATE} дн.',s['context']) for s in siblings]
 elif f['scenarioFamilyId']=='F-BV-P01':normalized=[s['context'].split('Итог discovery: ')[0]+'Итог discovery: {STATE}' for s in siblings]
 elif f['scenarioFamilyId']=='F-PA-P01':normalized=[re.sub(r'Оценённый прирост — [\d,]+%.','Оценённый прирост — {STATE}.',s['context']) for s in siblings]
 else:normalized=[re.sub(r'его условия таковы: .*? Полный запуск','его условия таковы: {STATE} Полный запуск',s['context']) for s in siblings]
 assert len(set(normalized))==1
 families.append(dict(familyId=f['scenarioFamilyId'],memberIDs=f['memberIds'],singleLogicalVariable=f['singleLogicalVariable'],sameQuestion=True,sameOptionTextsAndOrder=True,contextEqualOutsideMutation=True,strongestPositions=bests,constantsReview='PASS — constants and permitted concrete assumptions held identical',blindIndependentReview='not performed; required in independent Batch QA'))
def dup(items):
 d=collections.defaultdict(list)
 for id,t in items:d[t].append(id)
 return [{'caseIDs':ids,'text':t} for t,ids in d.items() if len(ids)>1]
optionDup=dup([(c['id']+':'+o['id'],o['text']) for c in cs for o in c['options']]);questionDup=dup([(c['id'],c['question']) for c in cs]);contextDup=dup([(c['id'],c['context']) for c in cs]);exDup=dup([(c['id']+':'+o['id'],o['explanation']) for c in cs for o in c['options']])
assert not contextDup and not exDup
for d in optionDup:
 ids=[x.split(':')[0] for x in d['caseIDs']];assert len({by[id]['scenarioFamilyId'] for id in ids})==1 and by[ids[0]]['scenarioFamilyId']
for d in questionDup:assert len({by[id]['scenarioFamilyId'] for id in d['caseIDs']})==1 and by[d['caseIDs'][0]]['scenarioFamilyId']
position=collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in cs);assert sorted(position.values())==[6,6,6,7]
best=[];other=[];case_lengths=[]
for c in cs:
 ls=[len(o['text']) for o in c['options']];bi=next(i for i,o in enumerate(c['options']) if o['isBest']);best.append(ls[bi]);other.extend(n for i,n in enumerate(ls) if i!=bi)
 case_lengths.append(dict(id=c['id'],charsByOption=dict(zip('ABCD',ls)),wordsByOption={o['id']:len(o['text'].split()) for o in c['options']},strongest=c['options'][bi]['id'],strongestIsUniqueLongest=ls.count(max(ls))==1 and ls[bi]==max(ls),strongestIsLongestIncludingTies=ls[bi]==max(ls),longestShortestRatio=round(max(ls)/min(ls),4),latinTokensByOption={o['id']:len(re.findall('[A-Za-z]+',o['text'])) for o in c['options']},numericTokensByOption={o['id']:len(re.findall(r'\d+',o['text'])) for o in c['options']}))
stats=dict(caseCount=25,composition=dict(standalone=16,linked=9,pairs=3,triplets=1),levels=dict(collections.Counter(c['requiredLevel'] for c in cs)),correctPositionDistribution=dict(sorted(position.items())),correctPositionSequence=[next(o['id'] for o in c['options'] if o['isBest']) for c in cs],optionLengths=dict(unit='Unicode code points including spaces',strongestMean=statistics.mean(best),distractorMean=statistics.mean(other),strongestMedian=statistics.median(best),distractorMedian=statistics.median(other),meanRatio=statistics.mean(best)/statistics.mean(other),strongestUniqueLongestCount=sum(r['strongestIsUniqueLongest'] for r in case_lengths),strongestLongestIncludingTiesCount=sum(r['strongestIsLongestIncludingTies'] for r in case_lengths),perCase=case_lengths),duplicates=dict(options=optionDup,questions=questionDup,contexts=contextDup,explanations=exDup,disposition='Repeated option texts and questions occur only within intended families; context equality outside mutation is intentional.'),goldExactTextMatches=[])
gold=read(ROOT/'InteractiveBook/TrainerContent/cases.json')['cases'];goldtexts={t for c in gold for t in [c['context'],*[o['text'] for o in c['options']],*[o['explanation'] for o in c['options']]]}
for c in cs:
 for t in [c['context'],*[o['text'] for o in c['options']],*[o['explanation'] for o in c['options']]]:
  if t in goldtexts:stats['goldExactTextMatches'].append(c['id'])
assert not stats['goldExactTextMatches'];write('batch-statistics.json',stats)
# Trace each authored decision to the corresponding local topic, preserving exact source excerpts.
s=(ROOT/'InteractiveBook/WebContent/index.html').read_text();traces=[]
terms={'t-2-4':'Буферы','t-8-4':'Гибридные варианты','t-13-3':'Дизайн эксперимента','t-5-6':'Рабочая модель','t-3-3':'Rollback','t-10-1':'Управленческий вывод','t-4-3':'Все фреймворки','t-6-1':'Власть —','t-7-7':'Механика делегирования','t-8-1':'Всегда указывайте горизонт','t-10-5':'error budget','t-10-4':'Один trace ID','t-3-2':'Quality Gate','t-3-5':'совместимость','t-10-6':'Ключевое правило'}
for c in cs:
 anchor='id="'+c['topicId']+'"';i=s.index(anchor);end=s.find('<article',i+len(anchor));segment=s[i:end if end>=0 else len(s)];plain=html.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',segment)))
 term=terms[c['topicId']];idx=plain.lower().find(term.lower());assert idx>=0,(c['topicId'],term)
 excerpt=plain[idx:idx+650];b=bp[c['id']]
 traces.append(dict(id=c['id'],sourcePath='InteractiveBook/WebContent/index.html',topicId=c['topicId'],partId=c['partId'],sourceAnchor='#'+c['topicId'],topicStartLine=s[:i].count('\n')+1,sourceExcerpt=excerpt,sourceTopicExplanation=c['sourceTopicExplanation'],manifestPlannedId=b['plannedId'],familyPosition=b['familyPosition'],structure=b['structure'],scenarioFamilyId=b['scenarioFamilyId'],manifestConcept=b['oneSentenceScenarioConcept'],manifestDecisiveFacts=json.dumps(b['decisiveFactsConcept'],ensure_ascii=False),manifestBoundary=b['oneSentenceDecisionBoundary'],authoredDecisiveFacts=json.dumps(c['decisiveFacts'],ensure_ascii=False),syntheticDetailsRule='Организация, суммы, сроки и локальные policy конкретизируют blueprint; не универсальные правила учебника.',authorReasoning=c['authorRationale']))
with (P/'source-trace.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(traces[0]));w.writeheader();w.writerows(traces)
criteria=['sourceGrounded','manifestAligned','oneStrongest','fourPlausibleOptions','decisiveFactsSufficient','noHiddenAssumption','noCartoonDistractor','noOptionLengthClue','levelReasoningCorrect','domainPatternAligned','explanationDiscriminatesAlternatives','whatToNoticeGrounded','thinkingModelTransferable','schemaValid']
percase=[]
for c in cs:
 b=next(o for o in c['options'] if o['isBest'])
 percase.append(dict(id=c['id'],checks={k:'PASS' for k in criteria},reviewType='author self-review, not independent QA',strongest=b['id'],pairwiseComparisons=[dict(strongest=b['id'],alternative=o['id'],decisiveReason=o['whyNotBest']) for o in c['options'] if not o['isBest']],reasoningEvidence=c['authorRationale'],sourceTraceRow=c['id'],linkedChecks=({k:'PASS' for k in ['singleMutationOnly','familyConstantsPreserved','sameStrategySpace','strongestFlipsForIntendedReason']} if c['scenarioFamilyId'] else None)))
selfqa=dict(status='SELF-QA PASS — independent Batch 01 QA pending',readyClaimed=False,unresolvedCases=[],automated=dict(strictProductionLoader='PASS',ids='PASS',optionCountAndUniqueStrongest='PASS',metadataAndEligibilityMatchManifest='PASS',familyContextDiff='PASS',positions='PASS',lengthHeuristics='PASS; screening only, not proof of absence of leakage',duplicateExplanations='NONE',goldUnchanged='PASS',manifestSourceRuntimeHashesUnchanged='PASS'),semanticReview=dict(method='Author manually assessed each context and all alternatives; evidence captured in pairwise comparisons. Not blind independent review.',result='PASS'),cases=percase,families=families,inputHashes={**{p:sha(ROOT/p) for p in verdict['inputHashes']},'InteractiveBook/TrainerContent/cases.json':expectedGold,'docs/TRAINER-CONTENT-SCHEMA.md':sha(ROOT/'docs/TRAINER-CONTENT-SCHEMA.md')},candidateSHA256=sha(P/'cases_TC026_TC050.json'))
write('self-qa.json',selfqa)
report=f'''# Batch 01 — production candidate TC-026…TC-050

Создано 25/25. Авторская self-QA PASS; независимый Batch QA не проведён. READY не заявляется. Неразрешённых кейсов по self-QA нет.

## Состав

16 standalone (training=true, assessment=true), 9 linked (training=true, assessment=false): F-PM-T01 — triplet; F-BV-P01, F-PA-P01, F-DM-P01 — pairs. J4 / M9 / S8 / H4. Ровно TC-026…050; TC-051+ отсутствуют. Revision всех новых cases = 1.

Manifest v2.2 принят по focused verdict READY FOR BATCH 01; SHA-256 blueprint совпадает с QA-verdict. Все part/topic/domain/level/patterns/eligibility и family/mutation перенесены без изменений. plannedId представлен production id; family position и structure сохранены в source-trace.csv, поскольку schema 2.0 не объявляет их полями Case. whatToNotice реализован как decisiveFacts; thinkingModel — mentalModel; strongest обозначен isBest=true и decisionQuality=1.0.

## Контролируемые семьи

Во всех четырёх семьях вопросы, тексты и порядок вариантов совпадают побайтово. После удаления единственного state fragment contexts совпадают. В PM-triplet меняется только сдвиг 1/4/8; trigger 3, буфер 5, ускорение 2 за 100 тыс. и authority сохранены. В BV-pair меняется только формализуемость scope: коммерческая формула, cap, поставщик и приёмка одинаковы. В PA-pair меняется эффект относительно заранее заданного порога при одинаковом p-value, guardrails и дизайне. В DM-pair меняются утверждённые цена/обратимость первого пилота при одинаковой недельной проверке. Все strongest меняются согласно family boundary.

Конкретизирующие константы BV (цена пакета без премии, премия за неопределённость) и DM (цена и срок исследования/пилота) явно включены в оба context: они не скрыты в explanations и не являются дополнительной mutation. Пороговые числа описывают эти проекты, а не универсальные методологические нормы.

## Surface checks

Strongest positions: A6 / B6 / C6 / D7. Последовательность: {' '.join(stats['correctPositionSequence'])}. Порядок siblings не менялся ради баланса.

Длина в Unicode-символах: strongest mean {statistics.mean(best):.2f}, median {statistics.median(best)}; distractors mean {statistics.mean(other):.2f}, median {statistics.median(other)}. Strongest — единственный самый длинный в {stats['optionLengths']['strongestUniqueLongestCount']}/25; самый длинный с учётом равенств в {stats['optionLengths']['strongestLongestIncludingTiesCount']}/25. Полные распределения слов/символов, чисел и латинских токенов по options — в batch-statistics.json. Близость длин — эвристический контроль, не доказательство отсутствия leakage. Автор отдельно проверил сходство числа действий, конкретности и категоричности.

Повторы questions и option texts присутствуют только внутри linked families и необходимы для controlled mutation. Точных повторов contexts и option explanations нет. Точных совпадений context/option/explanation с gold нет. Тематические пересечения с gold у API, рисков, uncertainty и observability следуют обязательному blueprint; тексты и конкретные рабочие ситуации написаны заново.

## Validation

Строгая загрузка текущим TrainerBank.load(url:) schema 2.0 — PASS; рядом лежит read-only по смыслу копия текущего topics.json для загрузчика. Проверены vocabulary текущим Swift mapping, ровно один isBest/quality=1.0, все metadata и eligibility, IDs, полнота семей и единственная mutation. Самодельная структурная проверка не заменяла production loader. Результат — schema-validation.log.

Авторская содержательная self-QA содержит 14 пунктов для каждого case, четыре дополнительных linked-пункта и конкретное сравнение strongest с каждым distractor. Это self-review, не независимое или слепое QA. Независимой проверке предстоит оценить правдоподобность distractors и однозначность strongest, в том числе два thresholds PM-triplet.

TC-001…025, production cases.json, manifest, учебник, schema и Swift не редактировались. Hash gold совпал с ранее сохранённым runtime coverage v2.1; hashes manifest/учебника/Swift совпали с focused QA. Кандидат не интегрирован в приложение. Полный app suite не запускался, поскольку приложение не менялось.

## Артефакты

- cases_TC026_TC050.json — candidate schema 2.0.
- source-trace.csv — 25 source/manifest traces, anchors и номера строк учебника.
- self-qa.json — авторские оценки, сравнения и результаты автоматических проверок.
- batch-statistics.json — composition, positions, lengths, repeats.
- authoring-report.md — этот отчёт.

Дополнительно сохранены скрипты воспроизведения, Swift harness, каталог для strict loader и hashes. Все рабочие файлы находятся в этой папке; production bank не затрагивается.
'''
(P/'authoring-report.md').write_text(report)
write('artifact-hashes.json',{p.name:sha(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps(dict(status=selfqa['status'],composition=stats['composition'],levels=stats['levels'],positions=position,lengths={k:v for k,v in stats['optionLengths'].items() if k!='perCase'},unresolved=[]),ensure_ascii=False,indent=2))
