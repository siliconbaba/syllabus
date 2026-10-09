import re,json,pathlib,itertools,statistics
P=pathlib.Path(__file__).resolve().parent
TOKEN=re.compile(r"[^\W_]+(?:[-’'][^\W_]+)*",re.UNICODE)
def features(t):
 tok=TOKEN.findall(t.lower()); verbs=[w for w in tok if re.search(r'(ть|ться|ти|чь)$',w) and w not in {'стоимость','скорость','готовность','ответственность','область','часть','мощность','возможность','неопределённость','устойчивость','надёжность','совместимость','самостоятельность','приемлемость','полностью','эффективность','очередь','связь'}]
 domainTerms=len(re.findall(r'\b(?:[a-z]+|\w*(?:миграц|контракт|интеграц|верси|корреляц|диагност|приорит|бюджет|метрик|приёмк|согласован|полномоч|релиз|автомат|гипотез|эксперимент|протокол)\w*)\b',t.lower()))
 return dict(domainTechnicalTerms=domainTerms,words=len(tok),chars=len(t),punctuation=len(re.findall('[,;:]',t)),allPunctuation=len(re.findall(r'[^\w\s]',t)),commas=t.count(','),semicolons=t.count(';'),dashes=len(re.findall('[—–]',t)),clauses=1+len(re.findall(r'[;:]|\b(?:если|когда|чтобы|поскольку|хотя)\b',t.lower())),actions=len(verbs),numbers=len(re.findall(r'\d+(?:[.,]\d+)?',t)),technicalTerms=len(re.findall(r'[A-Za-z]+',t)),conditions=len(re.findall(r'\b(?:если|когда|при|после|до|пока|только|чтобы)\b',t.lower())),parentheticals=len(re.findall(r'\([^)]*\)',t)),conjunctionAnd=tok.count('и'),negative=tok.count('не')+tok.count('без'),specificityAnchors=len(re.findall(r'\d+(?:[.,]\d+)?|[A-Za-z]+|\b(?:кажд\w*|всех|обоих|двух|трёх|четырёх|семи|восьми|дня|дней|неделю|недель|часа|суток)\b',t.lower())),sentences=len(re.findall(r'[.!?](?:\s|$)',t)))
def scan(cases):
 fs=[[features(o['text']) for o in c['options']] for c in cases];keys=[next(i for i,o in enumerate(c['options']) if o['isBest']) for c in cases];out=[]
 def rule(name,vals):
  hit=0;exp=0;ids=[]; ties=[]
  for c,vs,k in zip(cases,vals,keys):
   mx=max(vs);idxs=[i for i,v in enumerate(vs) if v==mx]
   hit+=idxs[0]==k;exp+=(1/len(idxs) if k in idxs else 0)
   if idxs[0]==k:ids.append(c['id'])
   ties.append(len(idxs))
  out.append(dict(rule=name,firstTieHits=hit,randomTieExpectedHits=round(exp,4),correctIDs=ids,tieCounts=ties))
 for f in fs[0][0]:
  for d in [1,-1]:rule(('max_' if d==1 else 'min_')+f,[[d*x[f] for x in ss] for ss in fs])
 for f,g in [('punctuation','words'),('punctuation','chars'),('punctuation','technicalTerms'),('words','punctuation'),('chars','punctuation')]:
  for d,e in itertools.product([1,-1],repeat=2):rule(f'lex_{d:+}{f}_{e:+}{g}',[[(d*x[f],e*x[g]) for x in ss] for ss in fs])
 for w in [1,5,10]:rule(f'words_plus_{w}_punctuation',[[x['words']+w*x['punctuation'] for x in ss] for ss in fs])
 for w in [5,10,20]:rule(f'chars_plus_{w}_punctuation',[[x['chars']+w*x['punctuation'] for x in ss] for ss in fs])
 return dict(perCase={c['id']:f for c,f in zip(cases,fs)},rules=out,bestFirstTie=max(out,key=lambda r:r['firstTieHits']),bestExpectedTie=max(out,key=lambda r:r['randomTieExpectedHits']))
if __name__=='__main__':
 result={v:scan(json.loads(path.read_text())['cases']) for v,path in [('before',P.parent/'batch-01/cases_TC026_TC050.json'),('after',P/'cases_TC026_TC050_r2.json')]}
 assert next(r for r in result['before']['rules'] if r['rule']=='lex_+1punctuation_+1words')['firstTieHits']==17
 (P/'surface-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 for v,x in result.items():
  print(v,[(r['rule'],r['firstTieHits'],r['randomTieExpectedHits']) for r in sorted(x['rules'],key=lambda r:(r['firstTieHits'],r['randomTieExpectedHits']),reverse=True)[:12]])
