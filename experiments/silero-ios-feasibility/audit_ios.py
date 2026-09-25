"""Independent verification of saved iOS output; no torch / re-export."""
from pathlib import Path
import hashlib,json
import numpy as np
from onnx_dsp import metrics
R=Path(__file__).resolve().parent
A=R/'artifacts/onnx-dsp'; I=R/'artifacts/ios-results'
m=json.loads((R/'reports/ios/resources-manifest.json').read_text())
r=json.loads((I/'report.json').read_text())
assert r['all_pass'] and len(r['cases'])==8 and r['ort_version']=='1.24.2'
for n,v in m['models'].items():
 for p in [A/(n+'.onnx'), R/'ios/SileroIOSPoC/Fixtures'/(n+'.onnx')]:
  assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
for c in m['cases']:
 for d in list(c['inputs'].values())+[c['reference'],c['mac'],c['durations'],c['mac_spectral']]+list(c['intermediate'].values()):
  assert hashlib.sha256((R/'ios/SileroIOSPoC/Fixtures'/d['file']).read_bytes()).hexdigest()==d['sha256']
w=np.load(A/'window.npy')
assert w.tobytes()==(R/'ios/SileroIOSPoC/Fixtures/window.bin').read_bytes()
rows=[]
for c,meta in zip(r['cases'],m['cases'],strict=True):
 n=c['id'];assert n==meta['id'];t=c['tokens'];f=c['frames']
 assert c['shapes']=={'duration':[1,t],'pitch':[1,1,t],'encoder':[1,t,128],'decoder':[1,192,f],'spectral':[1,2402,f]}
 inter=np.load(A/(n+'-onnx-intermediates.npz'))
 assert np.array_equal(np.array(c['durations']),inter['durations'].flatten())
 assert int(np.sum(c['durations']))==f and c['samples']==600*f
 audio=np.fromfile(I/(n+'.f32'),dtype='<f4')
 row={'id':n}
 for key,descriptor in [('vs_mac',meta['mac']),('vs_golden',meta['reference'])]:
  reference=np.fromfile(R/'ios/SileroIOSPoC/Fixtures'/descriptor['file'],dtype='<f4')
  v=metrics(reference,audio);assert v['length_equal'] and v['relative_l2']<.001
  for k in ['max_abs','rmse','relative_l2','snr_db']:
   assert np.isclose(v[k],c[key][k],rtol=1e-8,atol=1e-12),(n,k)
  row[key]=v
 assert c['dsp_only_vs_mac']['relative_l2']<1e-5
 rows.append(row)
out={'passed':True,'cases':rows,'models_sha256_unchanged':True,'window_bytes_unchanged':True,'all_shapes_and_durations_exact':True}
(R/'reports/ios/independent-audit.json').write_text(json.dumps(out,indent=2))
print('PASS: 8/8, all five model SHA256 unchanged, window unchanged, durations/shapes exact, Swift metrics independently verified.')
