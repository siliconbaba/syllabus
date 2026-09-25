import torch,json
from pathlib import Path
R=Path(__file__).resolve().parent;A=R/'artifacts';D=A/'preprocessing';D.mkdir(exist_ok=True)
torch.set_num_threads(4)
m=torch.package.PackageImporter(str(A/'v5_5_ru.pt')).load_pickle('tts_models','model');p=m.packages[m.speaker_to_package['xenia']]
m.unpack_q_model();p.q_model_unpacked=True
a=p.accentor.accentor.model;h=p.accentor.homosolver.model
for name,mod in [('accent',a),('homograph',h)]:
 s=[]
 for key,sub in mod.named_modules():
  s.append('\n### '+key+'\n'+str(sub.code if hasattr(sub,'code') else sub))
 (D/(name+'-modules.txt')).write_text('\n'.join(s))
 torch.jit.save(mod,str(D/(name+'.jit')))
print('Saved initialized auxiliary models and method sources')
