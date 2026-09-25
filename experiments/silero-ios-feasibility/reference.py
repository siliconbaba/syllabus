import torch, json, wave, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
A=ROOT/'artifacts'; R=ROOT/'reports'
torch.set_num_threads(4)
imp=torch.package.PackageImporter(str(A/'v5_5_ru.pt'))
model=imp.load_pickle('tts_models','model'); model.to(torch.device('cpu')); torch.set_num_threads(4)
p=model.packages[model.speaker_to_package['xenia']]
# Official lazy unpacking happens before the intercepted call.
model.unpack_q_model(); p.q_model_unpacked=True
core=p.models[p.speaker_to_model['xenia']]
def clone(x):
 if isinstance(x,torch.Tensor): return x.detach().clone()
 if isinstance(x,dict): return {k:clone(v) for k,v in x.items()}
 return x
def describe(x):
 if isinstance(x,torch.Tensor): return {'shape':list(x.shape),'dtype':str(x.dtype),'values':x.tolist()}
 return x
def wav(path,x):
 x=x.detach().cpu().flatten(); pcm=(x.clamp(-1,1)*32767).to(torch.int16).numpy().tobytes()
 with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(pcm)
class Capture:
 def __call__(self,**kw):
  self.inputs=clone(kw); self.rng=torch.get_rng_state(); self.output=core(**kw);return self.output
 def __getattr__(self,n):return getattr(core,n)
capture=Capture();p.models[p.speaker_to_model['xenia']]=capture
rows=[]
for sample in json.loads((ROOT/'corpus.json').read_text()):
 row=dict(sample)
 try:
  normalized=p.prepare_text_input(sample['text'],None)[0]
  row['normalized']=normalized;row['accented']=p.accentor(normalized)
  torch.manual_seed(20260924)
  start=time.perf_counter();ref=model.apply_tts(text=sample['text'],speaker='xenia',sample_rate=48000);row['seconds']=time.perf_counter()-start
  torch.set_rng_state(capture.rng)
  direct=core(**clone(capture.inputs))[0][0]
  delta=(ref-direct).double();row.update(samples=ref.numel(),duration=ref.numel()/48000,max_abs=float(delta.abs().max()),rmse=float(delta.square().mean().sqrt()),bit_equal=torch.equal(ref,direct))
  wav(A/(sample['id']+'-reference.wav'),ref);wav(A/(sample['id']+'-direct.wav'),direct)
  torch.save({'inputs':capture.inputs,'rng':capture.rng,'waveform':ref},A/(sample['id']+'-fixture.pt'))
  (R/(sample['id']+'-inputs.json')).write_text(json.dumps({k:describe(v) for k,v in capture.inputs.items()},ensure_ascii=False,indent=2))
 except Exception:row['error']=traceback.format_exc()
 rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
(R/'reference-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
torch.jit.save(core,str(A/'neural-core.jit.pt'))
(R/'core-operators.json').write_text(json.dumps(torch.jit.export_opnames(core),indent=2))
for name,obj in [('stress',p.accentor.accentor),('homographs',p.accentor.homosolver)]:
 m=obj.model
 info={'type':str(type(m)),'schema':str(m.forward.schema),'attributes':{k:{'type':str(type(v)),'length':len(v) if isinstance(v,(dict,list,tuple,str,set)) else None} for k,v in vars(obj).items()},'parameters':[(k,list(v.shape),str(v.dtype)) for k,v in m.named_parameters()],'buffers':[(k,list(v.shape),str(v.dtype)) for k,v in m.named_buffers()]}
 (R/(name+'-inventory.json')).write_text(json.dumps(info,ensure_ascii=False,indent=2))
 (A/(name+'-code.txt')).write_text(m.code)
