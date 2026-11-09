"""Descriptive editorial measurements; not a validated Russian readability grade."""
import json,re,hashlib,statistics,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def text(s):return html.unescape(re.sub('<[^>]+>',' ',s))
def words(s):return re.findall(r'[\w]+(?:[-/][\w]+)*',text(s))
chapters=sum([json.loads(p.read_text()) for p in sorted(ROOT.glob('chapters-*.json'))],[])
cues=json.loads((ROOT/'reading-cues.json').read_text())
rows=[];long=[]
for c in chapters:
 paragraphs=[]
 for field,parts in [('sections',c['sections']),('workedExample',[c['workedExample']]),('expedition',[c['expedition']])]:
  for i,s in enumerate(parts):
   for p in re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>',s['html'],re.S):
    p=re.sub(r'<(?:table|pre)\b[^>]*>.*?</(?:table|pre)>',' ',p,flags=re.S)
    paragraphs.append(len(words(p)))
    # Approximate segmentation: decimal points/abbreviations may split; manual review required.
    for sentence in re.split(r'(?<=[.!?])\s+',text(p)):
     if len(words(sentence))>=35:long.append({'chapter':c['id'],'field':field,'section':s['title'],'words':len(words(sentence)),'text':sentence})
 rows.append({'id':c['id'],'paragraphs':len(paragraphs),'median_paragraph_words':statistics.median(paragraphs),'max_paragraph_words':max(paragraphs),'goals_duplicate_section_titles':c['goals']==[s['title'] for s in c['sections']],'cues':[{k:x[k] for k in ['section','kind']}|{'words':len(words(x['html']))} for x in cues[c['id']]]})
result={'scope':'32 chapters; sections, workedExample, expedition; descriptive metrics, no readability grade','chapters':rows,'long_sentence_candidates':sorted(long,key=lambda x:x['words'],reverse=True),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('chapters-*.json'))}|{'reading-cues.json':hashlib.sha256((ROOT/'reading-cues.json').read_bytes()).hexdigest()}}
(OUT/'measurements.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Chapters:',len(rows),'goals duplicate titles:',sum(x['goals_duplicate_section_titles'] for x in rows),'sentences >=35 words:',len(long))
for x in result['long_sentence_candidates'][:7]:print(x)
