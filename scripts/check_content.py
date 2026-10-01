#!/usr/bin/env python3
"""Offline content integrity checks, standard library only; no runtime dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from collections import Counter
import re,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return re.sub(r'\s+',' ',s).strip()
def digest(s):return hashlib.sha256(norm(s).encode()).hexdigest()
class Node:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
 def all(self):
  yield self
  for c in self.children:
   if isinstance(c,Node):yield from c.all()
 def has(self,cls):return cls in self.attrs.get('class','').split()
 def text(self,skip_tabs=False):
  if skip_tabs and self.has('answer-tabs'):return ''
  return ' '.join(c.strip() if isinstance(c,str) else c.text(skip_tabs) for c in self.children if not isinstance(c,str) or c.strip())
class Parser(HTMLParser):
 void=set('area base br col embed hr img input link meta param source track wbr'.split())
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.errors=[]
 def handle_starttag(self,t,a):
  n=Node(t,a,self.stack[-1]);self.stack[-1].children.append(n)
  if t not in self.void:self.stack.append(n)
 def handle_startendtag(self,t,a):
  n=Node(t,a,self.stack[-1]);self.stack[-1].children.append(n)
 def handle_endtag(self,t):
  if t in self.void:return
  if len(self.stack)<2 or self.stack[-1].tag!=t:self.errors.append('Unbalanced closing '+t)
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:del self.stack[i:];return
 def handle_data(self,d):self.stack[-1].children.append(d)
def check():
 p=Parser();p.feed((ROOT/'InteractiveBook/WebContent/index.html').read_text());nodes=list(p.root.all())
 m=json.loads((ROOT/'Tests/content-manifest.json').read_text())
 ids=Counter(n.attrs['id'] for n in nodes if 'id' in n.attrs);byid={n.attrs['id']:n for n in nodes if 'id' in n.attrs}
 errors=[]
 def verify(ok,message):
  if not ok:errors.append(message)
 verify(not p.errors and len(p.stack)==1,'HTML tag balance: '+str(p.errors[:8]))
 verify(not [k for k,v in ids.items() if v>1],'Duplicate IDs')
 for n in nodes:
  href=n.attrs.get('href','')
  if href.startswith('#'):verify(href[1:] in byid,'Broken anchor '+href)
  if n.tag in ['script','link','img','iframe']:
   url=n.attrs.get('src',n.attrs.get('href',''))
   if n.tag=='link' and n.attrs.get('rel')!='stylesheet':continue
   verify(not re.match(r'(https?:)?//',url),'External render dependency '+url)
   if url and not url.startswith(('data:','#','http:','https:','//')):verify((ROOT/'InteractiveBook/WebContent'/url).is_file(),'Missing local asset '+url)
 questions=[n for n in nodes if n.has('bank-question')]
 verify([int(n.attrs['data-question']) for n in questions]==list(range(1,101)),'Question order/count')
 verify(len([n for n in nodes if n.has('bank-group')])==10,'Ten source blocks')
 for row,n in zip(m['questions'],questions):
  verify(n.attrs['id']=='bank-q-'+str(row['number']),'Question identity')
  verify(digest(n.text(True))==row['content_sha256'],'Question content changed: '+str(row['number']))
  for v in row['variants']:
   variant=byid.get(n.attrs['id']+'-'+v['mode'])
   verify(variant is not None and digest(variant.text())==v['sha256'],'Variant changed '+n.attrs['id']+v['mode'])
  verify(not any('data-level' in x.attrs for x in n.all()),'Invented grade in '+n.attrs['id'])
  ancestor=n.parent
  while ancestor:
   verify('data-level' not in ancestor.attrs,'Bank inside a grade filter');ancestor=ancestor.parent
 for rec in m['system_design']:
  dest=byid.get(rec['destination'])
  actual=norm(dest.text()) if dest else ''
  for text in rec['chunks']:verify(norm(text) in actual,'Missing System Design content at '+rec['destination']+': '+text[:75])
 verify([n.attrs['id'] for n in nodes if n.has('sd-case')]==m['case_ids'],'Exactly seven case identities')
 for cid in m['case_ids']:
  c=byid.get(cid)
  verify(c is not None and len([n for n in c.all() if n.has('case-section')])==16,'Case template '+cid)
  verify(any(n.has('system-diagram') for n in c.all()),'Case lacks diagram '+cid)
 for anchor in ['part-10','part-11','t-11-6','t-11-7','sd-building-blocks','sd-payment-states']:verify(anchor in byid,'Missing '+anchor)
 verify(len([n for n in nodes if n.has('topic')])==129,'Topic count')
 for n in nodes:
  if n.has('topic'):
   verify(any(x.tag=='a' and x.attrs.get('href')=='#'+n.attrs['id'] for x in nodes),'Topic missing from TOC '+n.attrs['id'])
 title='Управление процессами и проектами'
 verify(all(norm(n.text())==title for n in nodes if n.tag in ['title','h1']),'Book title')
 verify(next(n for n in nodes if n.has('brand')).text().strip().startswith(title),'Topbar title')
 bank=byid['t-a-3']
 verify('более 200 вопросов' not in bank.text(),'Old bank still present')
 verify(len([n for n in nodes if n.tag=='svg' and 'viewbox' in n.attrs])>=13,'Responsive diagrams missing')
 if errors:
  print('\n'.join('FAIL: '+s for s in errors[:45]));print('Total failures:',len(errors));return 1
 print('PASS: 100 questions / 300 source variants / 10 groups; 108 System Design source units; seven 16-section cases; 129 topics; unique IDs, links, title, offline assets and balanced HTML')
 return 0
if __name__=='__main__':sys.exit(check())
