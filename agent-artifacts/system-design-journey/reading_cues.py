"""Apply reviewed, exact-match reading cues without rewriting course text."""
import json
from html.parser import HTMLParser
from pathlib import Path
LABELS={'definition':'Определение','boundary':'Важное ограничение'}
class Plain(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
def plain(s):
    p=Plain();p.feed(s);return ''.join(p.parts)
def apply_reading_cues(chapters):
    cues=json.loads((Path(__file__).parent/'reading-cues.json').read_text())
    if set(cues)!={c['id'] for c in chapters}:raise ValueError('Reading cues must cover all chapters')
    for chapter in chapters:
        before=[s['html'] for s in chapter['sections']]
        for cue in cues[chapter['id']]:
            section=chapter['sections'][cue['section']]; fragment=cue['html'];kind=cue['kind']
            if kind=='term':
                # Match text nodes only, never tags/attributes; keep existing emphasis intact.
                import re
                parts=re.split('(<[^>]+>)',section['html']);found=False;inside=0
                for i,part in enumerate(parts):
                    if part in ('<strong>','<b>'):inside+=1
                    elif part in ('</strong>','</b>'):inside-=1
                    elif not part.startswith('<') and fragment in part:
                        if not inside:parts[i]=part.replace(fragment,'<strong>'+fragment+'</strong>',1)
                        found=True;break
                if not found:raise ValueError('Term excerpt changed: '+chapter['id'])
                section['html']=''.join(parts);continue
            if section['html'].count(fragment)!=1:raise ValueError('Ambiguous/changed reading cue: '+chapter['id'])
            if kind=='key':replacement='<span class="reading-key">'+fragment+'</span>'
            elif kind in LABELS:
                # Keep explanations in place; an exact definition can occupy only
                # part of a paragraph without wrapping that whole paragraph.
                label='<span class="cue-label">'+LABELS[kind]+'</span>'
                if '<p>'+fragment+'</p>' in section['html']:
                    section['html']=section['html'].replace('<p>'+fragment+'</p>','<p class="reading-cue reading-'+kind+'">'+label+fragment+'</p>',1)
                else:
                    section['html']=section['html'].replace(fragment,'<span class="reading-cue reading-'+kind+'">'+label+fragment+'</span>',1)
                continue
            else:raise ValueError('Unknown reading cue')
            section['html']=section['html'].replace(fragment,replacement,1)
        for original,section in zip(before,chapter['sections']):
            stripped=section['html']
            for label in LABELS.values():stripped=stripped.replace('<span class="cue-label">'+label+'</span>','')
            if plain(original)!=plain(stripped):raise ValueError('Reading cue changed original text: '+chapter['id'])
