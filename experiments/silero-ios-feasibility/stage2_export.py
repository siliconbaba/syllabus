import torch,json,traceback,time
from pathlib import Path
from eager_components import Predictor,Encoder,Decoder,Spectral
R=Path(__file__).resolve().parent;A=R/'artifacts';D=A/'onnx-dsp';O=R/'reports/onnx-dsp'
torch.set_num_threads(4)
dsp=json.loads((O/'dsp-parity.json').read_text())
assert len(dsp)==8 and all(x['length_equal'] and x['relative_l2']<2e-7 for x in dsp), 'DSP parity must pass before ONNX export'
c=torch.jit.load(str(A/'neural-core.jit.pt')).eval()
f=torch.load(A/'question-fixture.pt',weights_only=True)['inputs'];s=torch.load(D/'question-spectral.pt',weights_only=True)
mask=f['sequence']==0
models={
'duration':(Predictor(c.dur_predictor.dur_pred),('sequence','speaker_ids','mask','type_ids'),(f['sequence'],f['speaker_ids'],mask,f['type_ids'])),
'pitch':(Predictor(c.pitch_predictor.pitch_pred,True),('sequence','speaker_ids','mask','type_ids'),(f['sequence'],f['speaker_ids'],mask,f['type_ids'])),
'encoder':(Encoder(c.tacotron),('sequence','speaker_ids','mask','pitch'),(f['sequence'],f['speaker_ids'],mask,s['pitch'])),
'spectral':(Spectral(c),('mel',),(s['mel'],))}
with torch.no_grad():
 enc=models['encoder'][0](*models['encoder'][2]); expanded=torch.repeat_interleave(enc[0],(s['durations'][0]+.5).long(),0).unsqueeze(0)
models['decoder']=(Decoder(c.tacotron),('expanded',),(expanded,))
results=[]
for name,(m,keys,args) in models.items():
 try:
  m.eval()
  if name=='spectral':m=torch.jit.freeze(torch.jit.script(m))
  axes={k:{1:'tokens'} for k in keys if k not in ['speaker_ids','pitch','mel']}
  if name=='pitch':axes['output']={2:'tokens'}
  elif name in ['spectral','decoder']:axes['output']={2:'frames'}
  else:axes['output']={1:'tokens'}
  if 'pitch' in keys:axes['pitch']={2:'tokens'}
  if 'mel' in keys:axes['mel']={2:'frames'}
  with torch.no_grad():torch.onnx.export(m,args,str(D/(name+'.onnx')),dynamo=False,opset_version=18,input_names=list(keys),output_names=['output'],dynamic_axes=axes)
  results.append({'name':name,'success':True});print(name,'SUCCESS',flush=True)
 except Exception as e:
  (O/(name+'-adapter-error.txt')).write_text(traceback.format_exc());results.append({'name':name,'success':False,'error':str(e)});print(name,str(e)[:300],flush=True)
(O/'adapter-export.json').write_text(json.dumps(results,indent=2))
