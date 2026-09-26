#!/usr/bin/env python3
"""Audit union of speakable topics, including openable details. Never edits lexicons."""
import argparse, collections, hashlib, json, re
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = set('script style nav button input select textarea pre code svg img summary'.split())
CONTAINERS = set('article section div header footer p h1 h2 h3 h4 h5 h6 ul ol li dl dt dd blockquote details table thead tbody tfoot tr td th label'.split())
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
class Node:
    def __init__(self, tag='', attrs=()): self.tag, self.attrs, self.children = tag, dict(attrs), []
    def excluded(self):
        return self.tag in EXCLUDED or 'hidden' in self.attrs or self.attrs.get('aria-hidden') == 'true' or bool(set(self.attrs.get('class','').split()) & {'studied','speech-listen','table-hint'}) or bool(re.search(r'(display\s*:\s*none|visibility\s*:\s*hidden)', self.attrs.get('style','')))
class Parser(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.root=Node(); self.stack=[self.root]
    def handle_starttag(self, tag, attrs):
        node=Node(tag,attrs); self.stack[-1].children.append(node)
        if tag not in VOID: self.stack.append(node)
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag,attrs); self.handle_endtag(tag)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag: del self.stack[i:]; break
    def handle_data(self, data): self.stack[-1].children.append(data)
def inline(node):
    if isinstance(node,str): return node
    if node.excluded(): return ''
    value=' '.join(map(inline,node.children))
    if node.tag=='a' and re.match(r'\s*(https?://|www\.|[\w.-]+\.[a-z]{2,}(?:/|$))',value,re.I): return ''
    return value
def blocks(node):
    if node.excluded(): return
    if node.tag=='tr': yield '; '.join(inline(c) for c in node.children if isinstance(c,Node) and not c.excluded()); return
    buf=[]
    for c in node.children:
        if isinstance(c,Node) and c.tag in CONTAINERS:
            yield ' '.join(buf); buf=[]; yield from blocks(c)
        else: buf.append(inline(c))
    yield ' '.join(buf)
def topics(node):
    if 'topic' in node.attrs.get('class','').split(): yield node; return
    for c in node.children:
        if isinstance(c,Node): yield from topics(c)
def split_token(word):
    return re.sub(r'([a-z])([A-Z])',r'\1 \2',re.sub(r'([A-Z])([A-Z][a-z])',r'\1 \2',word)).split()
def lexicon():
    texts=[(ROOT/'InteractiveBook/Audio/SpeechTextProcessor.swift').read_text().split('private static let termRegex')[0],(ROOT/'InteractiveBook/Audio/Silero/TechnicalLexicon.swift').read_text().split('static let letters')[0]]
    return {k.lower():v for text in texts for k,v in re.findall(r'"([^"\n]+)"\s*:\s*"([^"\n]+)"',text)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,default=ROOT/'build/english-pronunciation'); ap.add_argument('--cmudict',type=Path); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    p=Parser(); html=ROOT/'InteractiveBook/WebContent/index.html'; p.feed(html.read_text()); rows=[]
    for t in topics(p.root):
        for b in blocks(t):
            b=re.sub(r'\s+',' ',b).strip()
            if re.search('[A-Za-z]',b): rows.append({'topic':t.attrs['id'],'text':b})
    count=collections.Counter(w.lower() for row in rows for w in re.findall('[A-Za-z]+',row['text']))
    known=lexicon(); approved={}
    source=ROOT/'InteractiveBook/Audio/Silero/EnglishPronunciation.swift'
    if source.exists(): approved=dict(re.findall(r'"([a-z]+)"\s*:\s*"([A-Z0-9 ]+)"',source.read_text()))
    frequencies=[{'token':w,'frequency':n,'coverage':'explicit' if w in known else 'cmudict' if w in approved else 'fallback'} for w,n in count.most_common()]
    report={'html_sha256':hashlib.sha256(html.read_bytes()).hexdigest(),'scope':'Union of topic content including openable details; excludes audio-reader.js excluded tags/classes, URL labels, inline-hidden content; no CSS execution.', 'unique':len(count),'occurrences':sum(count.values()),'explicit':sum(w in known for w in count),'dictionary':sum(w not in known and w in approved for w in count),'uncovered':[r for r in frequencies if r['coverage']=='fallback'],'frequencies':frequencies}
    for name,data in [('coverage.json',report),('blocks.json',rows)]: (a.out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    if a.cmudict:
        manifest=json.loads((ROOT/'tools/pronunciation/SOURCE.json').read_text())
        if hashlib.sha256(a.cmudict.read_bytes()).hexdigest()!=manifest['sha256']:
            raise SystemExit('Wrong CMUdict SHA256: pin/review the new source before proposing changes')
        wanted=set(count)
        for row in rows:
            for token in re.findall('[A-Za-z]+',row['text']): wanted.update(w.lower() for w in split_token(token))
        wanted.update((ROOT/'tools/pronunciation/fallback-words.txt').read_text().split())
        cmu={}
        for line in a.cmudict.read_text().splitlines():
            bits=line.split(); word=bits[0]
            if word in wanted and word not in known and len(word)>1: cmu.setdefault(word,' '.join(bits[1:]).split(' #')[0])
        (a.out/'proposed-phonemes.json').write_text(json.dumps(cmu,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('unique','occurrences','explicit','dictionary')})); print('Uncovered:', ', '.join(r['token']+':'+str(r['frequency']) for r in report['uncovered'][:100]))
if __name__=='__main__': main()
