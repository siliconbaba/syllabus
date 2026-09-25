import torch, traceback, json
from pathlib import Path
R=Path(__file__).resolve().parent; A=R/'artifacts'; O=R/'reports'
torch.set_num_threads(4)
core=torch.jit.load(str(A/'neural-core.jit.pt')).eval()
f=torch.load(A/'question-fixture.pt',weights_only=True);kw=f['inputs']
keys=['sequence','speaker_ids','durs_rate','pitch_coefs','type_ids']
args=tuple(kw[k] for k in keys)
class Wrapper(torch.nn.Module):
 def __init__(self):super().__init__();self.core=core
 def forward(self,sequence,speaker_ids,durs_rate,pitch_coefs,type_ids):
  return self.core(sequence,speaker_ids,48000,None,durs_rate,pitch_coefs,None,None,'cpu',-1,False,type_ids,None)[0]
m=Wrapper().eval();results=[]
def attempt(name,fn):
 try:
  result=fn();results.append({'name':name,'success':True});print(name,'SUCCESS',flush=True);return result
 except Exception as e:
  trace=traceback.format_exc();(O/(name+'-error.txt')).write_text(trace);results.append({'name':name,'success':False,'type':type(e).__name__,'error':str(e)});print(name,type(e).__name__,str(e)[:500],flush=True)
attempt('torch-export-direct',lambda:torch.export.export(core,(),kw))
def convert_ts():
 from torch._export.converter import TS2EPConverter
 return TS2EPConverter(torch.jit.script(m),args,{}).convert()
attempt('torch-export-ts2ep',convert_ts)
ep=attempt('torch-export-wrapper',lambda:torch.export.export(m,args))
if ep is not None:
 torch.export.save(ep,A/'core-export.pt2')
 def pte():
  from executorch.exir import to_edge
  (A/'core.pte').write_bytes(to_edge(ep).to_executorch().buffer)
 attempt('executorch',pte)
def onnx_export():
 scripted=torch.jit.script(m)
 torch.onnx.export(scripted,args,str(A/'core.onnx'),dynamo=False,opset_version=18,input_names=keys,output_names=['waveform'],dynamic_axes={'sequence':{1:'tokens'},'durs_rate':{1:'tokens'},'pitch_coefs':{1:'tokens'},'type_ids':{1:'tokens'},'waveform':{1:'samples'}})
attempt('onnx-legacy',onnx_export)
(O/'export-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
