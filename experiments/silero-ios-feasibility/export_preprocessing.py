"""Tensor-only auxiliary exports, leaving original package and golden data untouched."""
from pathlib import Path
import torch,json,traceback,hashlib
import onnx,onnxruntime as ort
import numpy as np
R=Path(__file__).resolve().parent;D=R/'artifacts/preprocessing';O=R/'reports/preprocessing';D.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
torch.set_num_threads(4)
class AccentNumeric(torch.nn.Module):
 def __init__(self,a):
  super().__init__();self.weight=torch.nn.Parameter(a.embedding.weight.detach().clone());self.stress=a.stress_clf;self.yo=a.yo_clf
 def forward(self,indices:torch.Tensor,offsets:torch.Tensor):
  x=torch.nn.functional.embedding_bag(indices,self.weight,offsets,mode='mean')
  return torch.cat((self.stress(x),self.yo(x)),dim=1)
def metric(a,b):
 d=a.astype(np.float64)-b;return dict(max_abs=float(abs(d).max()),rmse=float(np.sqrt(np.mean(d*d))),relative_l2=float(np.linalg.norm(d)/max(np.linalg.norm(a.astype(np.float64)),1e-30)))
if __name__=='__main__':
 a=torch.jit.load(str(D/'accent.jit')).eval();h=torch.jit.load(str(D/'homograph.jit')).eval()
 results={}
 for name,model,args,names,dynamic in [
  ('accent',torch.jit.script(AccentNumeric(a).eval()),(torch.tensor([0,1,2,3,5,8]),torch.tensor([0,3])),['indices','offsets'],{'indices':{0:'ngrams'},'offsets':{0:'words'},'output':{0:'words'}}),
  ('homograph',h,(torch.tensor([[2,83828,100,83829,3]]),torch.tensor([1]),torch.tensor([3])),['input_ids','homo_start_ids','homo_end_ids'],{'input_ids':{0:'batch',1:'tokens'},'homo_start_ids':{0:'batch'},'homo_end_ids':{0:'batch'},'output':{0:'batch'}})]:
  try:
   dest=D/(name+'.onnx')
   torch.onnx.export(model,args,str(dest),dynamo=False,opset_version=18,input_names=names,output_names=['output'],dynamic_axes=dynamic)
   onnx.checker.check_model(str(dest));opts=ort.SessionOptions();opts.intra_op_num_threads=4;ses=ort.InferenceSession(str(dest),sess_options=opts,providers=['CPUExecutionProvider'])
   with torch.no_grad():ref=model(*args).numpy()
   actual=ses.run(None,{k:v.numpy() for k,v in zip(names,args)})[0]
   results[name]={'success':True,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'smoke_parity':metric(ref,actual),'inputs':[(x.name,x.shape,x.type) for x in ses.get_inputs()],'outputs':[(x.name,x.shape,x.type) for x in ses.get_outputs()]}
  except Exception as e:
   (O/(name+'-export-error.txt')).write_text(traceback.format_exc());results[name]={'success':False,'error':str(e)[:2000]}
  print(name,results[name],flush=True)
 (O/'auxiliary-export.json').write_text(json.dumps(results,indent=2))
