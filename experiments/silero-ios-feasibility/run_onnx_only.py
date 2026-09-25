"""Standalone prepared-input synthesis: deliberately no PyTorch import."""
import json,time,wave
from pathlib import Path
import numpy as np
import onnxruntime as ort
from onnx_dsp import reconstruct,metrics
R=Path(__file__).resolve().parent;D=R/'artifacts/onnx-dsp';O=R/'reports/onnx-dsp'

class PreparedSynthesizer:
    def __init__(self):
        opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
        self.sessions={n:ort.InferenceSession(str(D/(n+'.onnx')),sess_options=opts,providers=['CPUExecutionProvider']) for n in ['duration','pitch','encoder','decoder','spectral']}
        self.window=np.load(D/'window.npy')
    def run(self,name,**inputs):
        session=self.sessions[name]
        return session.run(None,{v.name:np.ascontiguousarray(inputs[v.name]) for v in session.get_inputs()})[0]
    def synthesize(self,x):
        assert x['sequence'].shape[0]==1
        assert np.all(x['pitch_coefs']==1)
        # Contract: baseline sr=48000, symb_durs={}, focus_mask=None.
        inp={k:x[k] for k in ['sequence','speaker_ids','type_ids']};inp['mask']=x['sequence']==0
        log=self.run('duration',**inp)
        dur=np.rint(np.maximum(np.exp(log)-np.float32(1),np.float32(0)))
        dur[0,0]=min(dur[0,0],5)
        dur=np.rint(dur/x['durs_rate'])
        dur[0,0]=min(dur[0,0],5);dur[0,-1]=min(dur[0,-1],7);dur[0,-2]=13;dur[0,-3]=min(dur[0,-3],13)
        pitch=self.run('pitch',**inp)
        pitch=np.where(abs(pitch)<.001,np.float32(0),pitch)
        encoded=self.run('encoder',**inp,pitch=pitch)
        expanded=np.repeat(encoded[0],(np.maximum(dur[0],0)+np.float32(.5)).astype(np.int64),axis=0)[None]
        mel=self.run('decoder',expanded=expanded)
        spectral=self.run('spectral',mel=mel)
        return reconstruct(spectral,self.window),dur

if __name__=='__main__':
    t=time.perf_counter();synth=PreparedSynthesizer();init=time.perf_counter()-t
    rows=[]
    for case in json.loads((R/'corpus.json').read_text()):
        name=case['id'];x=np.load(D/(name+'-prepared-inputs.npz'))
        audio,dur=synth.synthesize(x)
        ref=np.load(D/(name+'-reference-float.npy'))
        row={'id':name,**metrics(ref,audio)};rows.append(row)
        assert row['length_equal'] and row['relative_l2']<5e-4
        print(name,row['snr_db'],flush=True)
    import sys
    assert 'torch' not in sys.modules, 'Unexpected PyTorch runtime dependency'
    (O/'onnx-only-parity.json').write_text(json.dumps({'torch_loaded':False,'session_initialization_seconds':init,'cases':rows},indent=2))
