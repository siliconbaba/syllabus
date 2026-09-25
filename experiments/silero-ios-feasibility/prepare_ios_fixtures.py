from pathlib import Path
import numpy as np,json,shutil,hashlib
from onnx_dsp import reconstruct
R=Path(__file__).resolve().parent;A=R/'artifacts/onnx-dsp';D=R/'ios/SileroIOSPoC/Fixtures';D.mkdir(parents=True,exist_ok=True)
manifest={'format':'contiguous little-endian row-major arrays; JSON shapes/dtypes; no headers','sample_rate':48000,'models':{},'cases':[]}
def write(name,x):
 x=np.ascontiguousarray(x);x=x.astype(x.dtype.newbyteorder('<'),copy=False);file=name+'.bin';(D/file).write_bytes(x.tobytes())
 # Prove serialized values identical, no numeric conversion besides byte order.
 assert np.array_equal(np.frombuffer((D/file).read_bytes(),dtype=x.dtype).reshape(x.shape),x)
 return {'file':file,'shape':list(x.shape),'dtype':str(x.dtype),'sha256':hashlib.sha256(x.tobytes()).hexdigest()}
for name in ['duration','pitch','encoder','decoder','spectral']:
 source=A/(name+'.onnx');shutil.copyfile(source,D/source.name)
 digest=hashlib.file_digest(source.open('rb'),'sha256').hexdigest();assert digest==hashlib.file_digest((D/source.name).open('rb'),'sha256').hexdigest()
 manifest['models'][name]={'sha256':digest,'bytes':source.stat().st_size}
w=np.load(A/'window.npy');manifest['window']=write('window',w)
for case in json.loads((R/'corpus.json').read_text()):
 n=case['id'];inputs=np.load(A/(n+'-prepared-inputs.npz'));inter=np.load(A/(n+'-onnx-intermediates.npz'))
 ref=np.load(A/(n+'-reference-float.npy'));mac=reconstruct(inter['spectral'],w).flatten()
 row={'id':n,'inputs':{k:write(n+'-'+k,inputs[k]) for k in inputs.files},'reference':write(n+'-reference',ref),'mac':write(n+'-mac',mac),'durations':write(n+'-durations',inter['durations']),'mac_spectral':write(n+'-mac-spectral',inter['spectral']),'intermediate':{k:write(n+'-mac-'+k,inter[k]) for k in ['duration_log','pitch','mel']}}
 manifest['cases'].append(row)
(D/'manifest.json').write_text(json.dumps(manifest,indent=2));(R/'reports/ios').mkdir(exist_ok=True);(R/'reports/ios/resources-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Prepared',len(manifest['cases']),'fixtures; model bytes and all tensor values unchanged')
