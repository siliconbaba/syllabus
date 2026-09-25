import torch,json,wave
from pathlib import Path
from onnx_dsp import reconstruct,metrics
R=Path(__file__).resolve().parent;A=R/'artifacts';O=A/'onnx-dsp';O.mkdir(exist_ok=True)
torch.set_num_threads(4)
c=torch.jit.load(str(A/'neural-core.jit.pt')).eval()
g=c.forward.graph.copy();torch._C._jit_pass_inline(g)
spectral=[n for n in g.nodes() if n.kind()=='aten::chunk'][-1].inputsAt(0)
original=list(g.outputs())[0]
values={v.debugName():v for n in g.nodes() for v in n.outputs()}
extra=[values[k] for k in ['pitch_hat','mel_outputs0']]
node=g.create('prim::TupleConstruct',[original,spectral]+extra);node.output().setType(torch._C.TupleType([v.type() for v in [original,spectral]+extra]));g.appendNode(node);g.eraseOutput(0);g.registerOutput(node.output());g.lint()
fn=torch._C._create_function_from_graph('capture_spectral',g)
window=c.vocoder.head.istft.window.detach().numpy();__import__('numpy').save(O/'window.npy',window)
def wav(path,x):
 import numpy as np
 pcm=(np.clip(np.asarray(x).flatten(),-1,1)*32767).astype('<i2')
 with wave.open(str(path),'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(pcm.tobytes())
rows=[]
with torch.no_grad():
 for case in json.loads((R/'corpus.json').read_text()):
  f=torch.load(A/(case['id']+'-fixture.pt'),weights_only=True);torch.set_rng_state(f['rng'])
  (out,durations),s,pitch,mel=fn(c,**dict(gt_durs=None,gt_pitch=None,accent_word=-1,question=False,**f['inputs']))
  assert torch.equal(out[0],f['waveform']), 'Capture changed original waveform'
  import numpy as np
  np.savez(O/(case['id']+'-prepared-inputs.npz'),**{k:v.numpy() for k,v in f['inputs'].items() if isinstance(v,torch.Tensor)})
  np.save(O/(case['id']+'-reference-float.npy'),f['waveform'].numpy())
  torch.save({'spectral':s,'durations':durations,'pitch':pitch,'mel':mel,'waveform':out[0]},O/(case['id']+'-spectral.pt'))
  external=reconstruct(s.numpy(),window)
  row={'id':case['id'],'spectral_shape':list(s.shape),'dtype':str(s.dtype),**metrics(out[0].numpy(),external)}
  rows.append(row);wav(O/(case['id']+'-external-dsp.wav'),external);wav(O/(case['id']+'-original.wav'),out[0].numpy());print(row,flush=True)
(R/'reports/onnx-dsp/dsp-parity.json').write_text(json.dumps(rows,indent=2))
