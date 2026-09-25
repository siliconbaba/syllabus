import torch, onnx, onnxruntime as ort, json, traceback
from pathlib import Path
R=Path(__file__).resolve().parent;A=R/'artifacts';O=R/'reports/onnx-dsp';torch.set_num_threads(4)
from export_utils import dense_fp32_graph
from torch.onnx import register_custom_op_symbolic
def dense_is_nested(g,x): return g.op('Constant',value_t=torch.tensor(False))
register_custom_op_symbolic('prim::is_nested',dense_is_nested,18)
register_custom_op_symbolic('aten::is_autocast_enabled',lambda g: g.op('Constant',value_t=torch.tensor(False)),18)
c=torch.jit.load(str(A/'neural-core.jit.pt')).eval(); f=torch.load(A/'question-fixture.pt',weights_only=True)['inputs']
class Duration(torch.nn.Module):
 def __init__(self):super().__init__();self.m=c.dur_predictor
 def forward(self,seq,sp,mask):return self.m(seq,sp,mask,1.,None)
class Pitch(torch.nn.Module):
 def __init__(self):super().__init__();self.m=c.pitch_predictor
 def forward(self,seq,sp,mask,types):return self.m(seq,sp,mask,types,None)
results=[]
for name,m,keys in [('duration',Duration(),['sequence','speaker_ids','mask']),('pitch',Pitch(),['sequence','speaker_ids','mask','type_ids'])]:
 try:
  f['mask']=torch.zeros_like(f['sequence'],dtype=torch.bool);args=tuple(f[k] for k in keys)
  dest=A/'onnx-dsp'/(name+'.onnx')
  torch.onnx.export(dense_fp32_graph(m),args,str(dest),dynamo=False,opset_version=18,input_names=keys,output_names=['output'],dynamic_axes={k:{1:'tokens'} for k in keys if k!='speaker_ids'})
  onnx.checker.check_model(str(dest));sess=ort.InferenceSession(str(dest),providers=['CPUExecutionProvider'])
  metrics=[]
  for case in json.loads((R/'corpus.json').read_text()):
   inp=torch.load(A/(case['id']+'-fixture.pt'),weights_only=True)['inputs'];inp['mask']=torch.zeros_like(inp['sequence'],dtype=torch.bool)
   args=tuple(inp[k] for k in keys)
   with torch.no_grad(): ref=m(*args).numpy()
   out=sess.run(None,{v.name:inp[v.name].numpy() for v in sess.get_inputs()})[0]
   d=ref.astype('float64')-out;metrics.append({'case':case['id'],'shape':list(out.shape),'max_abs':float(abs(d).max()),'rmse':float((d*d).mean()**0.5)})
  results.append({'name':name,'success':True,'metrics':metrics})
 except Exception as e:
  (O/(name+'-onnx-error.txt')).write_text(traceback.format_exc());results.append({'name':name,'success':False,'error':str(e)[:2500]})
 print(name,results[-1],flush=True)
(O/'component-export-results.json').write_text(json.dumps(results,indent=2))
