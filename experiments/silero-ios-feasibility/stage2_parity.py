import torch,numpy as np,json,time,wave,onnx,onnxruntime as ort
from pathlib import Path
from onnx_dsp import reconstruct,metrics
from eager_components import Predictor,Encoder,Decoder
R=Path(__file__).resolve().parent;A=R/'artifacts';D=A/'onnx-dsp';O=R/'reports/onnx-dsp'
torch.set_num_threads(4)
c=torch.jit.load(str(A/'neural-core.jit.pt')).eval()
window=np.load(D/'window.npy')
models={'duration':Predictor(c.dur_predictor.dur_pred).eval(),'pitch':Predictor(c.pitch_predictor.pitch_pred,True).eval(),'encoder':Encoder(c.tacotron).eval(),'decoder':Decoder(c.tacotron).eval()}
opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
sessions={};init={};contracts={}
for name in ['duration','pitch','encoder','decoder','spectral']:
 path=D/(name+'.onnx');onnx.checker.check_model(str(path))
 t=time.perf_counter();sessions[name]=ort.InferenceSession(str(path),sess_options=opts,providers=['CPUExecutionProvider']);init[name]=time.perf_counter()-t
 contracts[name]={'inputs':[(x.name,x.type,x.shape) for x in sessions[name].get_inputs()],'outputs':[(x.name,x.type,x.shape) for x in sessions[name].get_outputs()]}
def run(name,**inputs):return sessions[name].run(None,{x.name:np.ascontiguousarray(inputs[x.name]) for x in sessions[name].get_inputs()})[0]
def small(ref,test):
 ref=np.asarray(ref,dtype=np.float64);test=np.asarray(test,dtype=np.float64)
 if ref.shape!=test.shape:return {'ref_shape':list(ref.shape),'test_shape':list(test.shape),'shape_equal':False}
 d=test-ref
 return {'max_abs':float(abs(d).max()),'rmse':float(np.sqrt(np.mean(d*d))),'relative_l2':float(np.linalg.norm(d)/max(np.linalg.norm(ref),1e-30))}
def durations(log,rate):
 d=np.rint(np.maximum(np.exp(log)-np.float32(1),np.float32(0)))
 d[0,0]=min(d[0,0],5)
 d=np.rint(d/rate)
 d[0,0]=min(d[0,0],5);d[0,-1]=min(d[0,-1],7);d[0,-2]=13;d[0,-3]=min(d[0,-3],13)
 return d

def pipeline(inp):
 assert inp['sequence'].shape[0]==1, 'Only the baseline batch-one contract is validated'
 assert inp['symb_durs']=={} and inp['focus_mask'] is None and inp['sr']==48000
 assert np.all(inp['pitch_coefs'].numpy()==1),'Baseline host orchestration is for pitch coefficients 1'
 x={k:v.numpy() for k,v in inp.items() if isinstance(v,torch.Tensor)};x['mask']=x['sequence']==0
 timings={}
 def timed(name,**inputs):
  t=time.perf_counter();result=run(name,**inputs);timings[name]=time.perf_counter()-t;return result
 start=time.perf_counter();log=timed('duration',**x);pitch_raw=timed('pitch',**x)
 d=durations(log,x['durs_rate']);pitch=np.where(abs(pitch_raw)<.001,np.float32(0),pitch_raw)
 encoded=timed('encoder',**x,pitch=pitch)
 expanded=np.repeat(encoded[0],(np.maximum(d[0],0)+np.float32(.5)).astype(np.int64),axis=0)[None]
 mel=timed('decoder',expanded=expanded);spectral=timed('spectral',mel=mel)
 neural_host=time.perf_counter()-start
 t=time.perf_counter();audio=reconstruct(spectral,window);dsp_time=time.perf_counter()-t
 return locals()
def wav(path,a):
 with wave.open(str(path),'wb') as f:
  f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes((np.clip(a.flatten(),-1,1)*32767).astype('<i2').tobytes())
rows=[]
with torch.no_grad():
 for case in json.loads((R/'corpus.json').read_text()):
  name=case['id'];fixture=torch.load(A/(name+'-fixture.pt'),weights_only=True);saved=torch.load(D/(name+'-spectral.pt'),weights_only=True);inp=fixture['inputs']
  seq,sp=inp['sequence'],inp['speaker_ids'];mask=seq==0;types=inp['type_ids']
  ref_log=c.dur_predictor(seq,sp,mask,1.,None);ref_pitch=c.pitch_predictor(seq,sp,mask,types,None)
  refs={'duration_adapter':small(ref_log.numpy(),models['duration'](seq,sp,mask,types).numpy()),'pitch_adapter':small(ref_pitch.numpy(),models['pitch'](seq,sp,mask,types).numpy())}
  eager_enc=models['encoder'](seq,sp,mask,saved['pitch']);expanded=torch.repeat_interleave(eager_enc[0],(saved['durations'][0]+.5).long(),dim=0).unsqueeze(0)
  refs['acoustic_adapter']=small(saved['mel'].numpy(),models['decoder'](expanded).numpy())
  same_inputs={'sequence':seq.numpy(),'speaker_ids':sp.numpy(),'mask':mask.numpy(),'type_ids':types.numpy()}
  same_enc=run('encoder',**same_inputs,pitch=saved['pitch'].numpy())
  refs['encoder_onnx_same_inputs']=small(eager_enc.numpy(),same_enc)
  refs['decoder_onnx_same_inputs']=small(models['decoder'](expanded).numpy(),run('decoder',expanded=expanded.numpy()))
  refs['spectral_onnx_same_inputs']=small(saved['spectral'].numpy(),run('spectral',mel=saved['mel'].numpy()))
  p=pipeline(inp)
  intermediate={'duration_log':small(ref_log.numpy(),p['log']),'durations':small(saved['durations'].numpy(),p['d']), 'duration_exact':np.array_equal(saved['durations'].numpy(),p['d']),'pitch_raw':small(ref_pitch.numpy(),p['pitch_raw']),'pitch_conditioned':small(saved['pitch'].numpy(),p['pitch']),'mel':small(saved['mel'].numpy(),p['mel']),'spectral':small(saved['spectral'].numpy(),p['spectral'])}
  times=[]
  for _ in range(3):
   timing=pipeline(inp);times.append([timing['neural_host'],timing['dsp_time'],sum(timing['timings'].values())])
  med=np.median(times,axis=0);seconds=fixture['waveform'].numel()/48000
  row={'id':name,'tokens':seq.shape[1],'frames':p['spectral'].shape[2],'adapter_parity':refs,'intermediate':intermediate,'final':metrics(fixture['waveform'].numpy(),p['audio']),'performance':{'audio_seconds':seconds,'neural_and_orchestration_seconds':float(med[0]),'dsp_seconds':float(med[1]),'total_seconds':float(med[:2].sum()),'rtf':float(med[:2].sum()/seconds),'onnx_inference_seconds':float(med[2]),'host_orchestration_seconds':float(med[0]-med[2]),'repeats':3}}
  rows.append(row);wav(D/(name+'-onnx-dsp.wav'),p['audio']);np.savez(D/(name+'-onnx-intermediates.npz'),duration_log=p['log'],durations=p['d'],pitch=p['pitch'],mel=p['mel'],spectral=p['spectral'])
  print(json.dumps(row),flush=True)
(O/'onnx-parity.json').write_text(json.dumps({'session_init_seconds':init,'contracts':contracts,'cases':rows},indent=2))
