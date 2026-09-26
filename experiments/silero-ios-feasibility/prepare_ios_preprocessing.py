"""Copy checked auxiliary artifacts only; does not export or mutate golden data."""
from pathlib import Path
import json,hashlib,shutil
import onnx
R=Path(__file__).resolve().parent;A=R/'artifacts/preprocessing';D=R/'ios/SileroIOSPoC/Preprocessing';D.mkdir(parents=True,exist_ok=True)
exports=json.loads((R/'reports/preprocessing/auxiliary-export.json').read_text());files={}
for name in ['accent.onnx','homograph.onnx','data.json','golden.json']:
 p=A/name;digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if name.endswith('.onnx'):
  assert exports[p.stem]['success'] and exports[p.stem]['sha256']==digest
  graph=onnx.load(p)
  def check(g):
   for node in g.node:
    assert node.domain in ('','ai.onnx'),(node.op_type,node.domain)
    for a in node.attribute:
     if a.type==onnx.AttributeProto.GRAPH:check(a.g)
  check(graph.graph)
 shutil.copyfile(p,D/name);assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest
 files[name]={'bytes':p.stat().st_size,'sha256':digest}
(R/'reports/preprocessing/resources-manifest.json').write_text(json.dumps(files,indent=2))
print('Copied verified auxiliary models, original dictionaries and additive golden captures')

# Optional product corpus; distinct from immutable Silero golden captures.
if (R/"technical-corpus.json").exists():shutil.copyfile(R/"technical-corpus.json",D/"technical-corpus.json")

shutil.copyfile(R.parent.parent/"Tests/pronunciation-audio-corpus.json",D/"pronunciation-audio-corpus.json")
