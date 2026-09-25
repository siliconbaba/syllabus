"""Independent product-corpus / whitelist / audio audit (not raw-Silero waveform parity)."""
from pathlib import Path
import json,hashlib,wave,shutil
import numpy as np
R=Path(__file__).resolve().parent;A=R/'artifacts/technical/ios-results';O=R/'reports/technical';O.mkdir(exist_ok=True)
r=json.loads((A/'report.json').read_text());corpus=json.loads((R/'technical-corpus.json').read_text())
assert r['text_pass'] and r['all_pass'] and len(r['cases'])==len(corpus)==60
for row,expected in zip(r['cases'],corpus,strict=True):
 assert row['id']==expected['id'] and row['source']==expected['source']
 assert row['actual']==expected['expected'] and row['pass'] and row['whitelist_survives']
 assert row['after_silero_whitelist']==row['actual'].lower()
 assert not any(c.isascii() and (c.isalpha() or c.isdigit()) for c in row['actual'])
assert len(r['audio'])==sum(x['audio'] for x in corpus)==20
rows=[]
for c in r['audio']:
 x=np.fromfile(A/(c['id']+'.f32'),dtype='<f4');assert x.size==c['samples']==600*c['frames'] and np.isfinite(x).all() and np.max(np.abs(x))>1e-5
 with wave.open(str(A/(c['id']+'.wav'))) as w:
  assert w.getnchannels()==1 and w.getframerate()==48000 and w.getsampwidth()==2 and w.getnframes()==x.size
  pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
 assert np.array_equal(pcm,(np.clip(x,-1,1)*np.float32(32767)).astype(np.int16))
 rows.append({'id':c['id'],'samples':x.size,'wav_sha256':hashlib.sha256((A/(c['id']+'.wav')).read_bytes()).hexdigest(),'clipped_samples':int(np.sum(np.abs(x)>1))})
# Existing synthesizer / auxiliary files must remain identical.
for manifest,base in [(R/'reports/ios/resources-manifest.json',R/'artifacts/onnx-dsp'),(R/'reports/preprocessing/resources-manifest.json',R/'artifacts/preprocessing')]:
 d=json.loads(manifest.read_text());d=d.get('models',d)
 for n,v in d.items():
  file=base/(n+'.onnx' if not Path(n).suffix else n)
  assert hashlib.sha256(file.read_bytes()).hexdigest()==v['sha256']
shutil.copyfile(A/'report.json',O/'simulator-report.json')
if (A/'playback.json').exists():shutil.copyfile(A/'playback.json',O/'playback.json')
(O/'independent-audit.json').write_text(json.dumps({'pass':True,'text_cases':60,'whitelist_cases':60,'audio_cases':20,'models_and_original_golden_unchanged':True,'audio':rows},indent=2))
print('PASS: 60 text expectations, 60 whitelist survivals, 20 finite/non-silent WAVs; model and original capture hashes unchanged.')
