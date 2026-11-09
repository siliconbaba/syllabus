"""Static geometry/data checks, not a substitute for browser rendering."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
EXPECTED={'storage':('ch-03',4),'last-item':('ch-04',3),'cache-stampede':('ch-07',4),'replicas-vs-shards':('ch-08',0),'payment-unknown':('ch-09',0),'queue-vs-log':('ch-11',2),'road-distance':('ch-14',2),'replica-lag':('ch-17',3),'rag-boundaries':('ch-26',3),'migration-bridge':('ch-30',4)}
visuals=sum([json.loads((ROOT/name).read_text()) for name in ['visual-explainers-a.json','visual-explainers-b.json']],[])
assert {v['id'] for v in visuals}==set(EXPECTED)
frames=0
for visual in visuals:
 assert (visual['chapter'],visual['afterSection'])==EXPECTED[visual['id']]
 for frame in visual['frames']:
  frames+=1;node=ET.fromstring('<svg>'+frame['svg']+'</svg>');box=list(map(float,frame['viewBox'].split()))
  for text in node.iter('text'):
   assert 0<=float(text.get('x','0'))<=box[2] and 0<=float(text.get('y','0'))<=box[3],(visual['id'],frame['title'],'text anchor outside viewBox')
  assert frame['description'] and frame['title']
assert frames==29
result={'status':'PASS','explainers':len(visuals),'frames':frames,'placements':{v['id']:{'chapter':v['chapter'],'afterSection':v['afterSection'],'presentation':v['presentation'],'frames':len(v['frames'])} for v in visuals},'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['visual-explainers-a.json','visual-explainers-b.json','visual-explainers.js']},'scope':'JSON, XML, placement and text-anchor bounds; glyph overlap and browser layout NOT_RUN'}
(ROOT/'qa/visual-explainers-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS: 10 explainers / 29 frames, expected placement, XML and text-anchor bounds. Browser layout NOT_RUN.')
