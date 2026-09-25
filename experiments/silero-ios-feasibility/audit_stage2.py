import json,numpy as np,torch,onnx,platform,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;D=R/'artifacts/onnx-dsp';O=R/'reports/onnx-dsp'
models={}
for n in ['duration','pitch','encoder','decoder','spectral']:
 m=onnx.load(D/(n+'.onnx'))
 models[n]={'bytes':(D/(n+'.onnx')).stat().st_size,'opset':[(x.domain,x.version) for x in m.opset_import], 'operators':sorted(set(x.domain+'::'+x.op_type for x in m.graph.node)), 'initializer_types':sorted(set(x.data_type for x in m.graph.initializer))}
 assert all(x.domain in ('','ai.onnx') for x in m.graph.node),'Custom operator found'
 assert all(x.data_type not in (10,14,15,16) for x in m.graph.initializer),'Unexpected half/complex weights'
w=np.load(D/'window.npy');h=torch.hann_window(2400,periodic=True).numpy()
r={'models':models,'window_periodic_hann_max_abs':float(abs(w-h).max()),'platform':platform.platform(),'torch':torch.__version__}
(O/'graph-audit.json').write_text(json.dumps(r,indent=2))
parity=json.loads((O/'onnx-parity.json').read_text());dsp=json.loads((O/'dsp-parity.json').read_text())
assert len(parity['cases'])==len(dsp)==8
assert len({c['tokens'] for c in parity['cases']})==8
for c in parity['cases']:
 assert c['final']['length_equal'] and c['intermediate']['duration_exact']
 assert c['final']['snr_db']>65 and c['final']['relative_l2']<5e-4
for c in dsp:assert c['length_equal'] and c['relative_l2']<2e-7
hashes={}
for p in sorted((R/'artifacts').glob('*-fixture.pt')):
 hashes[p.name]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
(O/'golden-fixture-hashes.json').write_text(json.dumps(hashes,indent=2))
print('PASS: 8/8 lengths, predicted durations, DSP and ONNX numerical parity; 8 token lengths; standard ONNX operators; float32 weights')
