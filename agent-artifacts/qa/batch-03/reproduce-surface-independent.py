import json,re,pathlib,collections,statistics,random,itertools,hashlib,difflib,csv,html
root=pathlib.Path(__file__).resolve().parents[3];out=root/'agent-artifacts/qa/batch-03';base=root/'agent-artifacts/test-bank/batch-03';new=json.load((base/'cases_TC076_TC100.json').open())['cases'];old=json.load((root/'InteractiveBook/TrainerContent/cases.json').open())['cases'];stats=json.load((out/'batch-statistics-independent.json').open())
def tokens(s):return re.findall(r"[^\W_]+(?:[-’'][^\W_]+)*",s,re.UNICODE)
nonverbs={'часть','стоимость','мощность','готовность','зависимость','обратимость','надёжность','надежность','возможность','неопределённость','эффективность','длительность','устойчивость','ответственность','скорость','ценность','детальность','совместимость','конкретность','автономность','прозрачность','область','очередность','полноценность','доступность','нагрузочность','плотность','вероятность','совокупность','сложность','принадлежность','достаточность','личность','регулярность','достоверность','полезность','целостность','приоритетность','деятельность','результативность','согласованность','необходимость'}
def feat(s):
 ts=[x.lower() for x in tokens(s)];return {'words':len(ts),'chars':len(s),'sentences':len(re.findall(r'[.!?]+(?=\s|$)',s)),'latinFragments':len(re.findall('[A-Za-z]+',s)),'numberFragments':len(re.findall(r'\d+(?:[,.]\d+)?',s)),'and':ts.count('и'),'punctuation':len(re.findall('[,;:]',s)),'conditions':sum(t in {'если','когда','пока','при','после','до'} for t in ts),'orderMarkers':sum(t in {'сначала','затем','после','до','перед','сразу'} for t in ts),'actions':sum((t.endswith(('ть','ться','ти','чь')) and t not in nonverbs) for t in ts),'clauses':1+len(re.findall('[;:]',s)),'managementNounSuffix':sum(t.endswith(('ние','ния','цию','ция','ции','ость')) for t in ts),'negativeMarkers':sum(t in {'не','без','только'} for t in ts)}

basic=feat

def feat(t):
 f=basic(t);ts=re.findall(r'[^\W_]+',t.lower());f.update(commas=t.count(','),semicolons=t.count(';'),dashes=len(re.findall('[—–]|(?<=\\s)-(?=\\s)',t)),parentheses=t.count('('),clauseProxy=1+len(re.findall('[,;:]',t)),specificityProxy=len(re.findall('[A-Za-z]+|\\d+',t))+sum(x.startswith(('провер','соглас','фикс','измер','переключ','подтверд','владел','срок','приём','прием','контракт','верси','схем','данн','очеред','клиент')) for x in ts));return f
rules=[[(k,d)] for k in feat('') for d in [1,-1]]
for a,b in [('words','punctuation'),('chars','punctuation'),('words','clauseProxy'),('chars','clauseProxy'),('specificityProxy','punctuation')]:
 for x,y in [(a,b),(b,a)]:
  for da,db in itertools.product([1,-1],repeat=2):rules.append([(x,da),(y,db)])
def scan(rows):
 fs=[[feat(o['text']) for o in r['options']] for r in rows];keys=[next(i for i,o in enumerate(r['options']) if o['isBest']) for r in rows];result=[]
 for rule in rules:
  weights=[];hit=[];unique=ties=0
  for i,rr in enumerate(fs):
   v=[tuple(d*r[k] for k,d in rule) for r in rr];ix=[j for j,x in enumerate(v) if x==max(v)];weights.append([1/len(ix) if j in ix else 0 for j in range(4)]);hit.append(ix[0]==keys[i]);unique+=ix==[keys[i]];ties+=keys[i] in ix
  result.append({'rule':rule,'firstTieHits':sum(hit),'randomTieExpectedHits':sum(w[k] for w,k in zip(weights,keys)),'uniqueHits':unique,'hitsIncludingTies':ties,'correctIdsFirstTie':[r['id'] for r,h in zip(rows,hit) if h],'weights':weights})
 groups=collections.defaultdict(list)
 for i,r in enumerate(rows):groups[r.get('scenarioFamilyId') or r['id']].append(i)
 rng=random.Random(20261008);ge=0;draws=2000;obs=max(z['randomTieExpectedHits'] for z in result)
 for _ in range(draws):
  labels=keys.copy()
  for ix in groups.values():
   perm=list(range(4));rng.shuffle(perm)
   for i in ix:labels[i]=perm[keys[i]]
  ge+=max(sum(z['weights'][i][labels[i]] for i in range(len(rows))) for z in result)>=obs-1e-10
 for z in result:z.pop('weights')
 summary={k:{'correctMean':statistics.mean(feat(o['text'])[k] for r in rows for o in r['options'] if o['isBest']),'distractorMean':statistics.mean(feat(o['text'])[k] for r in rows for o in r['options'] if not o['isBest'])} for k in feat('')}
 return {'count':len(rows),'rules':result,'bestFirstTieHits':max(z['firstTieHits'] for z in result),'bestRandomTieExpectedHits':obs,'positions':dict(collections.Counter('ABCD'[k] for k in keys)),'keySequence':' '.join('ABCD'[k] for k in keys),'featureMeans':summary,'optionFeatures':{r['id']:f for r,f in zip(rows,fs)},'familyPreservingPermutation':{'maxStatisticAdjustedP':(ge+1)/(draws+1),'seed':20261008,'draws':draws,'groups':len(groups),'rules':len(rules)}}
corpora={name:scan(rows) for name,rows in [('production75',old),('batch03',new),('combined100',old+new)]}
result={'method':{'rules':len(rules),'features':list(feat('')),'ties':'first A/B/C/D and uniform-random expectations','actions':'infinitive suffix heuristic minus explicit noun stoplist','clauses':'1+semicolon/colon; clauseProxy also includes commas','specificityProxy':'Latin/number fragments plus words with management prefixes'},'corpora':corpora}
(out/'surface-leakage-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for name,v in corpora.items():
 print(name,{k:v[k] for k in ['bestFirstTieHits','bestRandomTieExpectedHits','positions','familyPreservingPermutation']})
 print('best single',max(z['firstTieHits'] for z in v['rules'] if len(z['rule'])==1))
 print('best',[(z['rule'],z['firstTieHits'],z['randomTieExpectedHits']) for z in v['rules'] if z['firstTieHits']==v['bestFirstTieHits']])
