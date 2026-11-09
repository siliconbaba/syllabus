#!/usr/bin/env python3
"""Validate source packs and produce a self-contained offline reader (stdlib only)."""
import json,re,sys,html,base64,struct
from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from reading_cues import apply_reading_cues
ROOT=Path(__file__).resolve().parent
WORLDS={'money','inventory','search','geo','collaboration','media','telemetry','saas'}
class SafeHTML(HTMLParser):
    allowed={'p','strong','em','b','i','ul','ol','li','code','pre','blockquote','table','thead','tbody','tr','th','td','br','a','h3','h4','dl','dt','dd','sup','sub','span'}
    def __init__(self):
        super().__init__();self.stack=[]
    def handle_starttag(self,tag,attrs):
        if tag not in self.allowed: raise ValueError('Forbidden HTML tag: '+tag)
        if tag in {'p','table','pre','ul','ol','dl','blockquote','h3','h4'} and 'p' in self.stack:
            raise ValueError('Block element inside paragraph: '+tag)
        for k,v in attrs:
            if k=='class' and tag in {'p','span'} and v in {'reading-cue reading-definition','reading-cue reading-boundary','reading-key','cue-label'}:continue
            if k not in {'href','title','colspan','rowspan'}:raise ValueError('Forbidden HTML attribute: '+k)
            if k=='href' and not re.match(r'^(https://|#)',v or ''):raise ValueError('Unsafe HTML link')
        if tag!='br':self.stack.append(tag)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag!='br':self.handle_endtag(tag)
    def handle_endtag(self,tag):
        if not self.stack or self.stack[-1]!=tag:raise ValueError('Unbalanced HTML closing tag: '+tag)
        self.stack.pop()

def require(ok,msg):
    if not ok:raise ValueError(msg)
def rich(s,label):
    require(isinstance(s,str) and bool(s.strip()),label+' must be nonempty HTML')
    parser=SafeHTML();parser.feed(s);parser.close();require(not parser.stack,label+' unclosed HTML tags: '+str(parser.stack))
def source(s):
    require(isinstance(s,dict) and s.get('title') and re.match(r'^https://[^\s]+$',s.get('url','')),'Invalid source')
def diagram(d,cid):
    require(re.fullmatch(r'[-\d.]+(?:\s+[-\d.]+){3}',d.get('viewBox','')) is not None,cid+' invalid viewBox')
    box=list(map(float,d['viewBox'].split()));require(box[2]>0 and box[3]>0,cid+' empty viewBox')
    require(d.get('title') and d.get('caption'),cid+' missing diagram title/caption')
    node=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg">'+d['svg']+'</svg>')
    allowed={'svg','g','rect','circle','ellipse','line','polyline','polygon','path','text','tspan','defs','marker','title','desc','clipPath'}
    ids=set();refs=[]
    for el in node.iter():
        tag=el.tag.split('}')[-1];require(tag in allowed,cid+' forbidden SVG tag '+tag)
        require(tag!='svg' or el is node,cid+' nested SVG')
        for k,v in el.attrib.items():
            k=k.split('}')[-1]
            require(not k.lower().startswith('on') and k not in {'href','src','style'},cid+' forbidden SVG attribute '+k)
            require(not re.search(r'(javascript:|https?:|data:|@import)',v,re.I),cid+' external SVG resource')
            if k=='id':require(v not in ids,cid+' duplicate SVG id');ids.add(v)
            for ref in re.findall(r'url\((.*?)\)',v):
                require(ref.startswith('#'),cid+' external SVG reference');refs.append(ref[1:])
    require(all(ref in ids for ref in refs),cid+' missing SVG reference target')

def load(name):
    p=ROOT/name
    require(p.is_file(),'Required content pack missing: '+name+'; no placeholder output generated')
    return json.loads(p.read_text(encoding='utf-8'))
def build():
    chapters=[]
    for name in ['chapters-01-08.json','chapters-09-16.json','chapters-17-24.json','chapters-25-32.json']:
        pack=load(name);require(isinstance(pack,list) and len(pack)==8,name+' must contain exactly 8 chapters');chapters+=pack
    require([c.get('id') for c in chapters]==[f'ch-{i:02}' for i in range(1,33)],'Chapter ids/order must be ch-01 through ch-32')
    for i,c in enumerate(chapters,1):
        cid=c['id'];require(c.get('arc')==(i-1)//4+1,cid+' wrong arc')
        for k in ['title','briefing']:require(isinstance(c.get(k),str) and c[k].strip(),cid+' missing '+k)
        require(len(c.get('sections',[]))>=5,cid+' needs at least five sections')
        require(c.get('goals') and all(isinstance(x,str) for x in c['goals']),cid+' missing goals')
        for s in c['sections']:require(s.get('title'),cid+' section title missing');rich(s.get('html'),cid+' section')
        for k in ['workedExample','expedition']:require(c.get(k,{}).get('title'),cid+' missing '+k);rich(c[k].get('html'),cid+' '+k)
        require(c['expedition'].get('world') in WORLDS,cid+' invalid expedition world')
        for k in ['transfer','distinct']:require(c['expedition'].get(k) and all(isinstance(x,str) for x in c['expedition'][k]),cid+' expedition '+k)
        require(1<=len(c.get('diagrams',[]))<=2,cid+' needs 1–2 diagrams')
        for di,d in enumerate(c['diagrams']):
            diagram(d,cid)
            # SVG definitions have document-wide scope: isolate author ids per figure.
            prefix=f'journey-{cid}-{di}-'
            ids=re.findall(r'\bid=[\"\']([^\"\']+)[\"\']',d['svg'])
            for ident in sorted(ids,key=len,reverse=True):
                d['svg']=re.sub(r'(\bid=[\"\'])'+re.escape(ident)+r'([\"\'])',lambda m:m[1]+prefix+ident+m[2],d['svg'])
                d['svg']=d['svg'].replace('url(#'+ident+')','url(#'+prefix+ident+')')
        dec=c.get('decision',{});require(dec.get('prompt') and dec.get('explanation') and len(dec.get('options',[]))>=2,cid+' invalid decision')
        require(type(dec.get('recommended')) is int and 0<=dec['recommended']<len(dec['options']),cid+' invalid recommended')
        for o in dec['options']:require(all(o.get(k) for k in ['title','consequence','tradeoff']),cid+' incomplete option')
        ex=c.get('exercise',{});require(ex.get('prompt') and ex.get('rubric'),cid+' invalid exercise');rich(ex.get('model'),cid+' exercise')
        require(len(c.get('checkpoint',[]))==2,cid+' requires two checkpoints')
        for q in c['checkpoint']:require(q.get('question') and q.get('explanation') and len(q.get('options',[]))>=3 and type(q.get('answer')) is int and 0<=q['answer']<len(q['options']),cid+' invalid checkpoint')
        require(c.get('sources'),cid+' sources missing')
        for s in c['sources']:source(s)
        texts=[c['briefing']]+[s['html'] for s in c['sections']]+[c['workedExample']['html'],c['expedition']['html'],ex['model']]
        c['wordCount']=len(re.findall(r'\S+',html.unescape(re.sub('<[^>]+>',' ',' '.join(texts)))))
    for start in range(0,32,8):require(sum(len(c['diagrams']) for c in chapters[start:start+8])>=12,'Each author pack requires at least 12 diagrams')
    worlds=load('atlas.json');require(isinstance(worlds,list) and {w.get('id') for w in worlds}==WORLDS and len(worlds)==8,'Atlas requires exactly eight unique worlds')
    for w in worlds:
        require(w.get('title') and w.get('briefing') and w.get('sections'),'Incomplete world '+w.get('id','?'))
        for s in w['sections']:require(s.get('title'),'Missing world section title');rich(s.get('html'),'world section')
        for x in w.get('compare',[]):require(x.get('world') in WORLDS,'Invalid compare world');rich(x.get('html'),'world comparison')
        for s in w.get('sources',[]):source(s)
    market=load('market.json') if (ROOT/'market.json').is_file() else []
    require(isinstance(market,list),'Market must be an array')
    market_ids=set()
    for m in market:
        require(isinstance(m,dict) and isinstance(m.get('id'),str) and m['id'] not in market_ids,'Market requires unique string ids')
        market_ids.add(m['id'])
        require(all(isinstance(m.get(k),str) and m[k].strip() for k in ['title','kernel']),'Market title/kernel missing')
        require(isinstance(m.get('worlds'),list) and bool(m['worlds']) and all(w in WORLDS for w in m['worlds']),'Invalid market world links')
    stages=load('story-stages.json')
    require(isinstance(stages,list) and [s.get('id') for s in stages]==list(range(1,9)),'Eight ordered story stages required')
    for stage in stages:
        require(all(isinstance(stage.get(k),str) and stage[k].strip() for k in ['title','period','regions','scale','change']),'Incomplete story stage')
    visuals=load('visual-explainers-a.json')+load('visual-explainers-b.json')
    require(len(visuals)==10,'Ten visual explainers required')
    visual_ids=set()
    for visual in visuals:
        ident=visual.get('id','')
        require(isinstance(ident,str) and re.fullmatch(r'[a-z][a-z0-9-]*',ident) is not None and ident not in visual_ids,'Invalid/duplicate visual explainer id')
        visual_ids.add(ident)
        require(visual.get('presentation') in {'comparison','sequence'},'Invalid visual presentation')
        chapter=next((c for c in chapters if c['id']==visual.get('chapter')),None)
        require(chapter is not None,'Unknown visual explainer chapter')
        require(type(visual.get('afterSection')) is int and 0<=visual['afterSection']<len(chapter['sections']),'Invalid visual explainer placement')
        require(all(isinstance(visual.get(k),str) and visual[k].strip() for k in ['title','intro','takeaway','caveat']),'Incomplete visual explanation')
        require(isinstance(visual.get('frames'),list) and 2<=len(visual['frames'])<=4,'Visual explanation requires two to four frames')
        for i,frame in enumerate(visual['frames']):
            require(isinstance(frame.get('description'),str) and frame['description'].strip(),'Missing visual frame description')
            diagram(dict(frame,caption=frame['description']),ident)
            prefix=f'visual-{ident}-{i}-'
            for svg_id in sorted(re.findall(r'\bid=[\"\']([^\"\']+)[\"\']',frame['svg']),key=len,reverse=True):
                frame['svg']=re.sub(r'(\bid=[\"\'])'+re.escape(svg_id)+r'([\"\'])',lambda m:m[1]+prefix+svg_id+m[2],frame['svg'])
                frame['svg']=frame['svg'].replace('url(#'+svg_id+')','url(#'+prefix+svg_id+')')
    art=load('illustrations.json')
    for sheet in art['sheets'].values():
        require(re.fullmatch(r'[a-z-]+\.png',sheet.get('file','')) is not None,'Invalid illustration filename')
        require(all(type(sheet.get(k)) is int and 1<=sheet[k]<=8 for k in ['columns','rows']),'Invalid illustration grid')
        raw=(ROOT/'illustrations'/sheet['file']).read_bytes()
        require(len(raw)>=24 and raw[:8]==b'\x89PNG\r\n\x1a\n' and raw[12:16]==b'IHDR','Invalid PNG illustration')
        sheet['width'],sheet['height']=struct.unpack('>II',raw[16:24])
        # CSS percentage windows also support fractional cell boundaries.
        require(sheet['width']>=sheet['columns'] and sheet['height']>=sheet['rows'],'Empty illustration cell')
        sheet['src']='data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
    ids=set();openings=[]
    for scene in art['scenes']:
        require(re.fullmatch(r'[a-z][a-z0-9-]*',scene.get('id','')) is not None,'Invalid illustration id')
        require(scene.get('kind') in {'arc','moment','spot'},'Invalid illustration kind')
        require(scene.get('id') not in ids,'Duplicate illustration id');ids.add(scene['id'])
        require(scene.get('chapter') in {c['id'] for c in chapters},'Unknown illustration chapter')
        require(scene.get('sheet') in art['sheets'],'Unknown illustration sheet')
        sheet=art['sheets'][scene['sheet']]
        require(type(scene.get('cell')) is int and 0<=scene['cell']<sheet['columns']*sheet['rows'],'Invalid illustration cell')
        require(all(isinstance(scene.get(k),str) and scene[k].strip() for k in ['caption','alt']),'Illustration caption/alt missing')
        if scene.get('placement')=='opening':openings.append(scene['chapter'])
        elif scene.get('placement')=='inline':
            c=next(c for c in chapters if c['id']==scene['chapter'])
            section=scene.get('section');paragraph=scene.get('afterParagraph')
            require(scene['kind']=='spot' and type(section) is int and 0<=section<len(c['sections']),'Invalid inline illustration section')
            require(type(paragraph) is int and 1<=paragraph<c['sections'][section]['html'].count('</p>'),'Inline illustration must sit between paragraphs')
        else:
            require(scene.get('placement')=='afterSection' and type(scene.get('afterSection')) is int and 0<=scene['afterSection']<len(next(c for c in chapters if c['id']==scene['chapter'])['sections']),'Invalid illustration placement')
    require(sorted(openings)==[f'ch-{n:02}' for n in range(1,33,4)],'Each arc needs one opening illustration')
    apply_reading_cues(chapters)
    for c in chapters:
        for section in c['sections']:rich(section['html'],c['id']+' annotated section')
    template=(ROOT/'template.html').read_text(encoding='utf-8');require(template.count('__COURSE_DATA__')==1,'Template data marker missing or duplicated')
    require(template.count('__VISUAL_EXPLAINERS_JS__')==1,'Visual explainer script marker missing or duplicated')
    template=template.replace('__VISUAL_EXPLAINERS_JS__',(ROOT/'visual-explainers.js').read_text(encoding='utf-8'))
    data=json.dumps({'chapters':chapters,'worlds':worlds,'market':market,'storyStages':stages,'storyArt':art,'visualExplainers':visuals},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    output=template.replace('__COURSE_DATA__',data);(ROOT/'system-design.html').write_text(output,encoding='utf-8')
    print(f'Built system-design.html: {len(chapters)} chapters, {len(worlds)} worlds, {sum(c["wordCount"] for c in chapters):,} words, {len(output):,} characters')
if __name__=='__main__':
    try:build()
    except (ValueError,KeyError,TypeError,ET.ParseError,json.JSONDecodeError) as exc:print('BUILD ERROR: '+str(exc),file=sys.stderr);sys.exit(1)
