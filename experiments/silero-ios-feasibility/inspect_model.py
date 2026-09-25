import torch, inspect, json, platform, zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/'reports'; out.mkdir(exist_ok=True)
torch.set_num_threads(4)
model=torch.package.PackageImporter(str(root/'artifacts/v5_5_ru.pt')).load_pickle('tts_models','model')
model.to(torch.device('cpu'))
def info(x):
 d={'type':str(type(x)), 'attributes':{k:str(type(v)) for k,v in vars(x).items()},'methods':{k:str(inspect.signature(getattr(x,k))) for k in dir(x) if not k.startswith('_') and callable(getattr(x,k))}}
 return d
report={'python':platform.python_version(),'torch':torch.__version__,'platform':platform.platform(),'object':info(model),'speakers':model.speakers,'parts':[]}
for i,p in enumerate(model.packages):
 r=info(p);r['config']={k:getattr(p,k,None) for k in ['speakers','speaker_to_ids','phons','symbols','alphabet','symbol_to_id','emb_dim','wrapped_jit_v']};r['cores']=[]
 for j,m in enumerate(p.models):
  r['cores'].append({'type':str(type(m)),'schema':str(m.forward.schema),'parameter_count':sum(x.numel() for x in m.parameters()),'parameters':[(k,list(v.shape),str(v.dtype)) for k,v in m.named_parameters()],'buffers':[(k,list(v.shape),str(v.dtype)) for k,v in m.named_buffers()],'modules':[(k,str(type(v)),getattr(v,'original_name','')) for k,v in m.named_modules()]})
  (out/f'core-{i}-{j}.txt').write_text(m.code)
 if p.accentor:
  r['accentor']=info(p.accentor)
 report['parts'].append(r)
(out/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str))
print(json.dumps({'type':str(type(model)),'speakers':model.speakers,'parts':len(model.packages),'torch':torch.__version__},ensure_ascii=False))
p=model.packages[0]; a=p.accentor
r={'ngram_count':len(a.accentor.model.embedding.ngram_dict),
   'homograph_vocab':len(a.homosolver.tokenizer.vocab),
   'stress_exceptions':len(a.accentor.exceptions),
   'homographs':len(a.homosolver.homodict),'yo_homographs':len(a.homosolver.yohomodict),
   'speaker_parameters':[(n,list(v.shape)) for n,v in p.models[0].named_parameters() if 'speaker' in n or 'spk' in n],
   'istft':{k:getattr(p.models[0].vocoder.head.istft,k) for k in ['n_fft','hop_length','win_length','padding']},
   'ssml_example':p.process_ssml('<speak>Привет.<break time="300ms"/><prosody rate="slow" pitch="high">Когда будет релиз?</prosody></speak>',None)}
(out/'preprocessing-data.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
