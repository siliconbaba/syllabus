import json,csv,re,html,hashlib,collections,statistics,pathlib,subprocess,difflib
from surface import scan,features
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[2];OLD=P.parent/'batch-01';QA=ROOT/'agent-artifacts/qa/batch-01';MP=ROOT/'agent-artifacts/manifests/v2.2'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def csvwrite(n,rows):
 with (P/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
old=read(OLD/'cases_TC026_TC050.json');new=read(P/'cases_TC026_TC050_r2.json');by={c['id']:c for c in new['cases']};ob={c['id']:c for c in old['cases']};verdict=read(QA/'QA-verdict.json');manifest=read(MP/'production_manifest_masterplan_v2_2.json');bp={r['plannedId']:r for r in manifest['manifest']}
for rel,h in verdict['inputHashes'].items():assert sha(ROOT/rel)==h,rel
# Confirm all known originals, not only the candidate, retain the prior recorded hashes.
for name,h in read(OLD/'artifact-hashes.json').items():assert sha(OLD/name)==h,name
for name,h in read(MP/'artifact-hashes.json').items():assert sha(MP/name)==h,name
issues=list(csv.DictReader((QA/'case-fixes.csv').open(encoding='utf-8-sig')));fissues=list(csv.DictReader((QA/'family-fixes.csv').open(encoding='utf-8-sig')))
assert len(issues)==10 and len(fissues)==1
scope=set(verdict['casesRequiringFixes']);frozen=set(ob)-scope
meta=['id','type','partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','decisiveMutation','trainingEligible','assessmentEligible']
def flatten(x,p=''):
 if isinstance(x,dict):return {kk:vv for k,v in x.items() for kk,vv in flatten(v,p+'.'+k if p else k).items()}
 if isinstance(x,list):return {kk:vv for i,v in enumerate(x) for kk,vv in flatten(v,p+f'[{i}]').items()}
 return {p:x}
def rawcases(path):
 s=path.read_text();idx=s.index('[',s.index('"cases"'));dec=json.JSONDecoder();out={};idx+=1
 while True:
  while s[idx].isspace() or s[idx]==',':idx+=1
  if s[idx]==']':break
  obj,end=dec.raw_decode(s,idx);out[obj['id']]=s[idx:end].encode();idx=end
 return out
oraw=rawcases(OLD/'cases_TC026_TC050.json');nraw=rawcases(P/'cases_TC026_TC050_r2.json')
changes=[];quality=[];keychanges=[];metachanges=[]
for id,c in by.items():
 a=ob[id];fa=flatten(a);fb=flatten(c);fields=[k for k in dict.fromkeys(list(fa)+list(fb)) if fa.get(k)!=fb.get(k)]
 assert all(c[k]==a[k] for k in meta)
 for k in ['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']:assert c[k]==bp[id][k]
 assert c['decisiveMutation']==bp[id]['decisiveMutationConcept']
 if fields:
  assert id in scope and c['revision']==2
  qs=[(i+1,q) for i,q in enumerate(issues) if id in q['caseIds']]
  changes.append({'TC-ID':id,'QA severity':' | '.join(dict.fromkeys(q['severity'] for _,q in qs)),'QA issue':' | '.join(f'QA-{i:02}: '+q['problem'] for i,q in qs),'fields changed':fields,'before summary':{k:fa.get(k) for k in fields},'after summary':{k:fb.get(k) for k in fields},'why fixed':c['authorRationale'] if id in ['TC-029','TC-030','TC-036','TC-038','TC-043','TC-045'] else ('Исправлены отмеченные quality/when-поля и/или синтаксис без смены стратегии; specific issue evidence в self-qa-r2.json.')} )
 else:assert oraw[id]==nraw[id]
 for ao,bo in zip(a['options'],c['options']):
  if ao['decisionQuality']!=bo['decisionQuality']:quality.append(dict(id=id,option=bo['id'],before=ao['decisionQuality'],after=bo['decisionQuality'],explanation=bo['explanation']))
  if ao['isBest']!=bo['isBest']:keychanges.append(dict(id=id,option=bo['id']))
 if id in frozen:assert oraw[id]==nraw[id]
assert {c['TC-ID'] for c in changes}==scope and len(changes)==17 and len(frozen)==8
assert len(by)==25 and set(by)=={f'TC-{n:03}' for n in range(26,51)} and not keychanges
assert new['schemaVersion']=='2.0'
for c in by.values():
 assert len(c['options'])==4 and [o['id'] for o in c['options']]==list('ABCD')
 assert sum(o['isBest'] for o in c['options'])==sum(o['decisionQuality']==1 for o in c['options'])==1
 for o in c['options']:assert o['isBest']==(o['decisionQuality']==1) and 0<=o['decisionQuality']<=1
 assert c['assessmentEligible']==(not c['scenarioFamilyId']) and c['trainingEligible']
res=subprocess.run([str(P/'validate-batch'),str(P/'cases_TC026_TC050_r2.json')],capture_output=True,text=True,check=True);(P/'schema-validation.log').write_text(res.stdout)
# Literal family checks include exact before/after context and ordered option differences.
fam=[]
for f in manifest['familyManifest']:
 if not any(id in by for id in f['memberIds']):continue
 ids=f['memberIds'];rs=[by[id] for id in ids];base=rs[0];fid=f['scenarioFamilyId']
 qdiff=[list(difflib.ndiff(base['question'].splitlines(),r['question'].splitlines())) for r in rs[1:]]
 sameq=all(r['question']==base['question'] for r in rs)
 sameopts=all([(o['id'],o['text']) for o in r['options']]==[(o['id'],o['text']) for o in base['options']] for r in rs)
 assert sameq and sameopts
 assert all(r['context']==ob[r['id']]['context'] and r['question']==ob[r['id']]['question'] for r in rs)
 key=[next(o['id'] for o in r['options'] if o['isBest']) for r in rs];assert len(set(key))==len(rs)
 for r in rs:
  assert [o['id'] for o in r['options']]==[o['id'] for o in ob[r['id']]['options']]
 diffs=[]
 for r in rs[1:]:
  sm=difflib.SequenceMatcher(None,base['context'],r['context']);diffs.append(dict(a=base['id'],b=r['id'],changes=[dict(before=base['context'][a:b],after=r['context'][c:d]) for tag,a,b,c,d in sm.get_opcodes() if tag!='equal']))
 optionchanges={id:[l for l in 'ABCD' if by[id]['options'][ord(l)-65]['text']!=ob[id]['options'][ord(l)-65]['text']] for id in ids}
 if fid=='F-BV-P01':assert all(v==['B'] for v in optionchanges.values())
 else:assert all(oraw[id]==nraw[id] for id in ids)
 fam.append(dict(familyId=fid,memberIDs=ids,status='PASS',singleVariable=f['singleLogicalVariable'],contextUnchangedFromR1=True,contextDiffsBetweenSiblings=diffs,questionDiff=[],optionTextDiffBetweenSiblings=[],optionOrderDiff=[],changedOptionTextsFromR1=optionchanges,constantsPreserved=True,strongestPositions=key))
changes.append({'TC-ID':'F-BV-P01','QA severity':'BLOCKER (same as QA-01; not additional issue)','QA issue':fissues[0]['problem'],'fields changed':['TC-029.options.B','TC-030.options.B'],'before summary':'Условное «только устойчивые пакеты» позволяло ноль фиксированных пакетов и вырождалось в D.','after summary':'Один одинаковый B требует фиксировать две трети результата на старте. Context, question, order и family metadata неизменны.','why fixed':'В 029 две трети формализованы без премии; в 030 их зафиксировать нельзя без принятия риска нестабильного scope. Поэтому B → D следует только из mutation.'})
csvwrite('change-log.csv',changes)
# Reader selections existed before loading production keys in this verification step.
reader=read(P/'reader-check.json');preds=reader['cases'];assert {r['id'] for r in preds}==scope
for r in preds:
 r['productionStrongest']=next(o['id'] for o in by[r['id']]['options'] if o['isBest']);r['matches']=r['productionStrongest']==r['predictedStrongest'];assert r['matches'] and r['confidence']=='high'
 assert set(r['decisiveFactVsEachAlternative'])==set('ABCD')-{r['predictedStrongest']}
# Reproduce exact QA punctuation and tokenizer features across all 100 original options.
surf={k:scan(v['cases']) for k,v in [('before',old),('after',new)]};priorStats=read(QA/'batch-statistics-independent.json')
for id,features in surf['before']['perCase'].items():
 for got,expected in zip(features,priorStats['optionFeatures'][id]):
  for k in ['punctuation','words','chars']:assert got[k]==expected[k]
repro=next(r for r in surf['before']['rules'] if r['rule']=='lex_+1punctuation_+1words');assert repro['firstTieHits']==17 and repro['correctIDs']==priorStats['additionalExploratoryRules'][1]['correctCaseIds']
assert max(r['firstTieHits'] for r in surf['after']['rules'])<=10
assert max(r['randomTieExpectedHits'] for r in surf['after']['rules'])<=10
positions=dict(sorted(collections.Counter(next(o['id'] for o in c['options'] if o['isBest']) for c in new['cases']).items()));assert positions==dict(A=6,B=6,C=6,D=7)
def lengths(cs):
 out={}
 for group,cond in [('strongest',True),('distractors',False)]:
  ts=[o['text'] for c in cs for o in c['options'] if o['isBest']==cond];chars=[len(t) for t in ts];words=[len(re.findall(r"[^\W_]+(?:[-’'][^\W_]+)*",t)) for t in ts]
  out[group]=dict(charsMean=statistics.mean(chars),charsMedian=statistics.median(chars),wordsMean=statistics.mean(words),wordsMedian=statistics.median(words))
 return out
stat=dict(before=surf['before'],after=surf['after'],originalHeuristicReproduced=dict(rule='maximize comma/semicolon/colon count, then Unicode words, then first A/B/C/D',hits=17),methods=dict(tokenizer="Unicode alphanumeric; internal hyphen/apostrophe retained; matches all 100 original QA word counts",tieHandling='first A/B/C/D reported as deterministic hits; also uniform-random expected hits among tied extrema',clauseAndActionCounts='explicit regex proxies in surface.py; not a syntactic parser',technicalTerms='Latin fragments plus separate Russian/Latin domain dictionary; not a semantic classifier',specificity='numeric/lexical anchor proxy plus author content review',limitations='Exploratory within-batch audit; no guarantee against all classifiers. Family dependence means siblings are not independent observations. No statistical p-value or out-of-sample claim.'),lengthsBefore=lengths(old['cases']),lengthsAfter=lengths(new['cases']),positions=positions,composition=dict(total=25,standalone=16,linked=9),levels=dict(collections.Counter(c['requiredLevel'] for c in new['cases'])),qualityChanges=quality)
write('batch-statistics-r2.json',stat)
# Explicit closure for every QA issue record, with no implicit acceptance of author PASS.
evidence=[
'Одинаковый B в 029/030 требует фиксировать две трети на старте; D в 030 сравнивается с реальной альтернативой. Reader check D > A/B/C, confidence high.',
'Исходная эвристика воспроизведена 17/25; тот же rule после 7/25. Лучший deterministic из расширенного набора 9/25; максимум expected random tie 9.5833/25. Frozen восемь не менялись.',
'036: неизвестности спроса и исполнения разделены; учитывается смещение льготного канала и этапность обязательств после неполного evidence. Senior rationale и сравнения A/C/D записаны.',
'038: синтаксическая двухверсионность отделена от поведения потребителя; спроектированы проверка семантики и выход при редких обращениях. Senior rationale записан.',
'043: расхождение локального HTTP и общего SLI требует изменить go/no-go нескольких pipeline с сохранением независимой поставки, без нового исключения.',
'045: техническая независимость не равна ресурсной; промежуточная приёмка переносит bottleneck на миграцию. Изменён механизм взаимодействия ветвей, итог 15 вместо 16 или 18, а не просто вычитание трёх дней.',
'037 D: 0.70 → 0.40, ниже A=0.55. Значение соответствует неверному типу evidence; strongest C сохранён.',
'048 B: 0.78 → 0.35 за нарушение обязательного сосуществования. Strongest C сохранён.',
'036 C больше не предписывает аренду после интервью. Аренда отложена до поведенческих данных; весь when соответствует действию, quality=0.60.',
'042 A when теперь требует решающего ограничения ликвидности, постоянных подтверждённых потоков и равенства остальных факторов. Оно покрывает окончательный выбор, не только shortlist.'
]
issueStatus=[dict(issueId=f'QA-{i+1:02}',caseIDs=q['caseIds'],severity=q['severity'],field=q['field'],originalProblem=q['problem'],status='FIXED',evidence=evidence[i],reviewAuthority='author self-assessment; pending focused independent QA') for i,q in enumerate(issues)]
assert collections.Counter(x['severity'] for x in issueStatus)=={'BLOCKER':1,'MAJOR':8,'MINOR':1}
regression=dict(casesChanged=17,casesByteIdentical=8,byteIdenticalCaseIDs=sorted(frozen),frozenMetadataChanges=[],revisionChanges=[dict(id=id,before=1,after=2) for id in sorted(scope)],strongestChanges=[],decisionQualityChanges=quality,familiesWithImplementationChanges=['F-BV-P01'],manifestFamilyChanges=[],otherFamiliesByteIdentical=True,sourceBankAndBlueprintUnchanged=True)
selfqa=dict(verdict='READY FOR FOCUSED QA',readyForImport=False,remainingUnresolvedIDs=[],issueStatuses=issueStatus,familyIssueStatus=dict(family='F-BV-P01',status='FIXED',duplicateOf='QA-01'),seniorRealization={id:dict(status='PASS — author assessment',whyThisNowRequiresSeniorReasoning=by[id]['authorRationale'],frozenBoundary=bp[id]['oneSentenceDecisionBoundary']) for id in ['TC-036','TC-038','TC-043','TC-045']},readerCheck=dict(method=reader['method'],cases=preds,allMatch=True),surfaceGate=dict(status='PASS',bestDeterministicHits=9,bestRandomTieExpectedHits=9.5833,originalRuleAfterHits=7,scope='60+ declared simple rules; conditional on implemented proxies'),families=fam,regression=regression,strictProductionLoader='PASS',sourceGrounding='Local textbook topic excerpts and new author rationale in source-trace-r2.csv; no external frameworks',protectedInputHashes={rel:sha(ROOT/rel) for rel in verdict['inputHashes']},qaInputHashes={n:sha(QA/n) for n in ['QA-report.md','case-fixes.csv','family-fixes.csv','batch-statistics-independent.json','QA-verdict.json']},candidateSHA256=sha(P/'cases_TC026_TC050_r2.json'))
selfqa['surfaceGate']['testedRuleCount']=len(surf['after']['rules']);selfqa['surfaceGate']['scope']='Declared rules in batch-statistics-r2.json; conditional on implemented proxies'
write('self-qa-r2.json',selfqa)
# Rechecked source grounding, scoped to all changed cases.
s=(ROOT/'InteractiveBook/WebContent/index.html').read_text();source=[]
terms={'t-5-6':'Рабочая модель','t-10-1':'Управленческий вывод','t-10-5':'SLI это','t-2-4':'Критический путь может меняться','t-8-4':'Гибридные варианты','t-3-3':'rollback','t-4-3':'Масштабирование','t-6-1':'Власть','t-7-7':'Делегирование результата','t-8-1':'Всегда указывайте горизонт','t-10-4':'trace ID','t-3-5':'совместимость','t-10-6':'Ключевое правило'}
for id in sorted(scope):
 c=by[id];start=s.index('id="'+c['topicId']+'"');end=s.find('<article',start+10);txt=html.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',s[start:end])));term=terms[c['topicId']];idx=txt.lower().find(term.lower());assert idx>=0,(id,term)
 source.append(dict(id=id,sourcePath='InteractiveBook/WebContent/index.html',anchor=c['topicId'],topicLine=s[:start].count('\n')+1,sourceExcerpt=txt[idx:idx+1000],sourceTopicExplanation=c['sourceTopicExplanation'],groundingNote='Синтетические факты конкретизируют утверждённую задачу; источник даёт механизм рассуждения, а не универсальные числовые thresholds.',whySenior=by[id]['authorRationale'] if id in selfqa['seniorRealization'] else 'Metadata и diagnostic boundary сохранены; смысловая правка только согласно QA issue.'))
csvwrite('source-trace-r2.csv',source)
report=['# Batch 01 r2 — targeted revision','','**READY FOR FOCUSED QA** — авторский self-verdict, не READY FOR IMPORT. Blocker: 1/1 FIXED; major: 8/8 FIXED; minor: 1/1 FIXED. Неразрешённых ID нет. Независимый focused QA ещё требуется.','','## Изменения и регрессия','','Изменены ровно 17 разрешённых cases. Восемь frozen cases побайтово идентичны как JSON-фрагменты: '+', '.join(sorted(frozen))+'. Исходный batch-01 не изменён, все его сохранённые hashes подтверждены.','','Frozen metadata changes: 0. Редакционные revision: 17 переходов 1→2; неизменённые cases остаются revision=1. Strongest changes: 0. DecisionQuality changes: '+str(len(quality))+'. Все значения и причины — self-qa-r2.json и change-log.csv. Family implementation changes: только F-BV-P01; три другие семьи побайтово прежние. Manifest, source, gold, schema и scoring не менялись.','','25 cases: 16 standalone / 9 linked, J4/M9/S8/H4. Позиции A6/B6/C6/D7. TC-051+ не создавались.','','## TC-030 и F-BV-P01','','B больше не условный hybrid: он требует на старте закрепить две трети результата. В 029 это ровно формализованная доля без премии; в 030 значимый стабильный пакет отсутствует. D в 030 сильнее B из-за непригодности фиксировать две трети; сильнее A из-за риска фиксации всего объёма; сильнее C из-за продолжающегося изменения требований при доступном контролируемом старте T&M. Сравнение strongest с самим D не имеет смысла: D — сохранённый ключ, проверены все остальные A/B/C.','','Contexts и questions обоих siblings неизменны от r1. Между siblings различается прежняя разрешённая variable; option texts/order идентичны. В r2 синхронно изменён только B, вместе с объяснениями и качеством B в 030. Буквальные diffs сохранены в self-qa-r2.json.','','## Why this now requires Senior reasoning','']
for id in selfqa['seniorRealization']:report+=['- '+id+': '+by[id]['authorRationale']]
report+=['','Эти изменения реализуют прежнее направление decision boundary: дешёвое знание до build; поведенчески совместимая миграция; действующее reliability governance вместо бизнес-исключения; безопасная параллельность с пересчётом всей цепочки. Уровни и codes не менялись. Усиление сделано по прямому текущему заданию, несмотря на предпочтение QA переклассифицировать строки. Проверка этой реализации — предмет focused QA.','','## Surface leakage','','Воспроизведены исходные punctuation/words/chars для всех 100 options. Rule `max ,;: → max Unicode words → first A/B/C/D` даёт прежние 17/25 и тот же список попаданий. После правок — **7/25**. Лучшее deterministic правило расширенного набора — **9/25**; максимальное ожидание при случайном выборе среди равных — **9.5833/25**. Ни одна проверенная одиночная heuristic не превышает 10/25.','','| Rule | Before, first-tie hits | After, first-tie hits | After, random-tie expected |','|---|---:|---:|---:|']
for name in ['max_chars','min_chars','max_words','min_words','max_punctuation','min_punctuation','max_clauses','max_actions','max_numbers','max_technicalTerms','max_domainTechnicalTerms','max_conditions','min_conditions','lex_+1punctuation_+1words','lex_+1punctuation_+1chars']:
 a=next(x for x in surf['before']['rules'] if x['rule']==name);b=next(x for x in surf['after']['rules'] if x['rule']==name);report.append(f"| {name} | {a['firstTieHits']} | {b['firstTieHits']} | {b['randomTieExpectedHits']} |")
report+=['','Проверены оба направления признаков, comma/semicolon/dash отдельно, слова и символы, proxies clauses/actions/conditions, числа, латиница и русские технические термины, скобки, specificity anchors. Лексикографические комбинации и суммы length+punctuation также включены. Специфичность и число смысловых действий дополнительно оценены при reader pass. Длины не делались одинаковыми до символа.','','Нормализация касается названного QA набора. Frozen cases не тронуты. Исправления не сводятся к сокращению strongest: выровнены перечни и синтаксическая структура полных наборов, сохранены профессиональные альтернативы. Эти результаты — внутрипартийный exploratory audit, не доказательство отсутствия всех возможных утечек; siblings не считаются независимыми наблюдениями.','','## Reader check и validation','','Для 17 изменённых cases выполнен отдельный проход по key-hidden-review.json без scoring/explanation-полей; predictedStrongest и решающие факты по каждой альтернативе записаны в reader-check.json перед программным сравнением. Все 17 совпали, confidence high. Автор уже знает предыдущий контекст, поэтому этот проход **не выдаётся за независимый blinded review другого агента**.','','Свежескомпилирован текущий production TrainerBank.load(url:) с mapping: строгая schema 2.0, known vocabulary и единственный isBest/quality=1 — PASS. Проверены ID, metadata, eligibility, literal family diffs и hashes исходных артефактов. Приложение, persistence, engine и production bank не изменены; полный app suite не требовался для отдельного content candidate.','','## Артефакты','','- cases_TC026_TC050_r2.json','- revision-report.md','- change-log.csv','- self-qa-r2.json','- batch-statistics-r2.json','','Дополнительно: key-hidden-review.json, reader-check.json, source-trace-r2.csv, strict-loader log/harness и скрипты воспроизведения. Все файлы находятся в batch-01-r2. Импорт и Batch 02 не выполнялись.']
(P/'revision-report.md').write_text('\n'.join(report)+'\n')
write('artifact-hashes.json',{p.name:sha(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps(dict(verdict=selfqa['verdict'],changed=17,unchanged=8,issues=dict(collections.Counter(i['severity'] for i in issueStatus)),qualityChanges=len(quality),strongestChanges=0,positions=positions,bestHeuristicBefore=17,bestHeuristicAfter=9,originalRuleAfter=7,unresolved=[]),ensure_ascii=False,indent=2))
