"""Independently audit Swift-generated stages/tensors/audio against immutable references."""
from pathlib import Path
import hashlib,json,numpy as np,shutil
from onnx_dsp import metrics
R=Path(__file__).resolve().parent;A=R/'artifacts/preprocessing';I=A/'ios-results';O=R/'reports/preprocessing'
r=json.loads((I/'preprocessing.json').read_text());gold=json.loads((A/'golden.json').read_text());assert r['all_pass'] and len(r['cases'])==25
manifest=json.loads((O/'resources-manifest.json').read_text())
for n,v in manifest.items():
 assert hashlib.sha256((A/n).read_bytes()).hexdigest()==v['sha256']
 assert hashlib.sha256((R/'ios/SileroIOSPoC/Preprocessing'/n).read_bytes()).hexdigest()==v['sha256']
for actual,ref in zip(r['cases'],gold,strict=True):
 assert actual['id']==ref['id'] and actual['pass'] and all(actual['checks'].values())
 for k,v in actual['actual_stages'].items():assert v==ref[k],(actual['id'],k)
 for v in actual['auxiliary_metrics'].values():assert v['relative_l2']<1e-5
 if not ref['id'].startswith('extra_'):
  with np.load(R/'artifacts/onnx-dsp'/(ref['id']+'-prepared-inputs.npz')) as f:
   for k in f.files:assert np.array_equal(np.array(actual['actual_stages'][k]),f[k]),(ref['id'],k)
summary=[]
for c in r['waveforms']:
 n=c['id'];assert c['pass'] and c['durations_equal'] and c['shapes_equal']
 inter=np.load(R/'artifacts/onnx-dsp'/(n+'-onnx-intermediates.npz'))
 assert np.array_equal(c['durations'],inter['durations'].flatten())
 audio=np.fromfile(I/(n+'.f32'),dtype='<f4');reference=np.load(R/'artifacts/onnx-dsp'/(n+'-reference-float.npy'));v=metrics(reference,audio)
 assert v['length_equal'] and v['relative_l2']<.001
 for k in ['max_abs','rmse','relative_l2','snr_db']:assert np.isclose(v[k],c['vs_golden'][k],rtol=1e-8,atol=1e-12)
 old=np.fromfile(R/'artifacts/ios-results'/(n+'.f32'),dtype='<f4');equal=np.array_equal(audio,old)
 summary.append({'id':n,'waveform':v,'bit_equal_previous_ios_fixture':equal})
 # Separate A/B directory; preserve prior WAV references.
 ab=I/'ab';ab.mkdir(exist_ok=True);shutil.copyfile(R/'artifacts'/(n+'-reference.wav'),ab/(n+'-python.wav'));shutil.copyfile(I/(n+'.wav'),ab/(n+'-ios.wav'))
small={k:v for k,v in r.items() if k!='cases'};small['cases']=[{k:v for k,v in c.items() if k!='actual_stages'} for c in r['cases']]
(O/'simulator-preprocessing.json').write_text(json.dumps(small,indent=2,ensure_ascii=False))
(O/'independent-audit.json').write_text(json.dumps({'passed':True,'stage_cases':25,'all_original_tensors_exact':True,'waveforms':summary},indent=2))
if (I/'playback.json').exists():shutil.copyfile(I/'playback.json',O/'playback.json')
print('PASS: 25 stage cases exact; 8 original tensor sets exact; 8 end-to-end waveform metrics independently verified.')
