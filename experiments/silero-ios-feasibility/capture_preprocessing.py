"""Additive original-Silero captures. Never write previous golden fixtures."""
import torch,numpy as np,json,hashlib,re
from pathlib import Path
import onnxruntime as ort
from export_preprocessing import AccentNumeric,metric
R=Path(__file__).resolve().parent;D=R/'artifacts/preprocessing';O=R/'reports/preprocessing'
torch.set_num_threads(4)
def save_new(path,value):
 data=json.dumps(value,ensure_ascii=False,indent=2).encode()
 if path.exists():assert path.read_bytes()==data,f'Immutable capture differs: {path}'
 else:path.write_bytes(data)
def indices_for(words,ng):
 inds=[];offsets=[]
 for word in words:
  offsets.append(len(inds));b=b'<'+word.encode()+b'>';sub=[]
  for n in range(1,len(word.encode())+4):
   for j in range(len(b)-n+1):
    try:g=b[j:j+n].decode()
    except UnicodeDecodeError:continue
    if g in ng:sub.append(ng[g])
  if not sub:sub=[ng['UNK']]
  inds.extend(sub)
 return torch.tensor(inds),torch.tensor(offsets)
if __name__=='__main__':
 assert hashlib.sha256((R/'artifacts/v5_5_ru.pt').read_bytes()).hexdigest()=='50081637b602126ee06cb3bc8a744d25651d2da149ee8864b9a379bfdd934437'
 imp=torch.package.PackageImporter(str(R/'artifacts/v5_5_ru.pt'));m=imp.load_pickle('tts_models','model');p=m.packages[m.speaker_to_package['xenia']];m.unpack_q_model();p.q_model_unpacked=True
 mod=imp.import_module('multi_acc_v3_package');a=p.accentor.accentor;h=p.accentor.homosolver;tok=h.tokenizer;ng=a.model.embedding.ngram_dict
 metadata={'symbols':p.symbols,'symbol_to_id':p.symbol_to_id,'sos':p.sos_token,'eos':p.eos_token,'exceptions':a.exceptions,'ngrams':ng,'homodict':h.homodict,'vocab':dict(tok.vocab),'never_split':sorted(tok.never_split),'WH_FORMS':sorted(mod.WH_FORMS),'LEADING_FILLERS':sorted(mod.LEADING_FILLERS),'TAG_PATTERNS':mod.TAG_PATTERNS,'speaker_ids':{'aidar':0,'baya':1,'kseniya':2,'eugene':3,'xenia':4},'stress_classes':int(a.model.stress_clf(torch.zeros(1,16)).shape[1]),'yo_classes':int(a.model.yo_clf(torch.zeros(1,16)).shape[1])}
 save_new(D/'data.json',metadata)
 extended=[('homo_context','На двери висит замок, а на горе стоит замок.'),('yo_restore','Все еще ждут, когда он принесет елку.'),('stress_words','Договор, звонит, торты, красивее и обеспечение.'),('wh_question','Скажите, пожалуйста, почему команда опоздала?'),('general_question','Команда уже готова?'),('alternative_question','Релиз будет сегодня или завтра?'),('tag_question','Мы всё проверили, не так ли?'),('exclamation','Какой прекрасный результат!'),('multi','Команда готова. Когда релиз? Мы успеем!'),('punctuation','Ну... правда?! Да?.. Нет; возможно: позже.'),('hyphens','Кто-то по-прежнему ждёт — а кто‑то ушёл.'),('quotes','«Когда будет релиз?» — спросил он.'),('technical_ru','Сервер возвращает ошибку, поэтому проверяем журнал событий.'),('user_stress','з+амок и зам+ок, вс+е и ёлка.'),('unicode','Е\u0308жик\u00a0ждёт\tеё.\nКогда\nрелиз?'),('known_latin','API вернул HTTP 500, а SLA нарушен.'),('known_digits','В 2026 году исправили 25 ошибок.')]
 corpus=json.loads((R/'corpus.json').read_text());extras=[{'id':'extra_'+i,'text':t} for i,t in extended];save_new(R/'preprocessing-corpus.json',extras)
 sessions={}
 for name in ['accent','homograph']:
  opts=ort.SessionOptions();opts.intra_op_num_threads=4;sessions[name]=ort.InferenceSession(str(D/(name+'.onnx')),sess_options=opts,providers=['CPUExecutionProvider'])
 numeric=AccentNumeric(a.model).eval();rows=[];parity=[]
 for item in corpus+extras:
  text=item['text'];sentences,_,breaks,rates,pitches,sp=p.prepare_tts_model_input(text,False,[4],None);normal=sentences[0]
  tags=h._find_and_tag_homos(normal);marks=[x[4] for x in tags if x[4] is not None];ids=[tok(s) for s in marks];starts=[v.index(tok.homo_start_id) for v in ids];ends=[v.index(tok.homo_end_id) for v in ids]
  batch=torch.nn.utils.rnn.pad_sequence([torch.tensor(x) for x in ids],batch_first=True,padding_value=0) if ids else torch.empty(0,0,dtype=torch.int64)
  logits=h.model(batch,torch.tensor(starts),torch.tensor(ends)) if ids else torch.empty(0,1)
  homo=h(normal);raw,clean,mask=a._tokenize(homo);inds,offsets=indices_for(clean,ng)
  emb=torch.nn.functional.embedding_bag(inds,a.model.embedding.weight,offsets,mode='mean');actualemb=a.model.embedding(clean)
  assert torch.equal(emb,actualemb),(item['id'],'ngram order mismatch',float((emb-actualemb).abs().max()))
  st,yo=a.model(clean);combined=torch.cat((st,yo),dim=1);assert torch.equal(numeric(inds,offsets),combined)
  accent=a(homo);seq,symb,dr,pc=p.merge_batch_model(sentences,breaks,rates,pitches);cls=mod.classify_text(text);types=p.build_type_ids_inference(text,cls,seq.shape[1])
  row={**item,'normalized':normal,'homograph_tags':[list(x) for x in tags],'wordpieces':[tok.tokenize(x) for x in marks],'homo_ids':batch.tolist(),'homo_starts':starts,'homo_ends':ends,'homo_logits':logits.tolist(),'homograph_resolved':homo,'stress_raw':raw,'stress_clean':clean,'stress_mask':mask,'ngram_indices':inds.tolist(),'ngram_offsets':offsets.tolist(),'accent_logits':combined.tolist(),'stressed':accent,'final_text':accent,'character_ids':[p.symbol_to_id[c] for c in accent],'classification':cls,'sequence':seq.tolist(),'type_ids':types.tolist(),'speaker_ids':sp.tolist(),'durs_rate':dr.tolist(),'pitch_coefs':pc.tolist()}
  if item in corpus:
   old=np.load(R/'artifacts/onnx-dsp'/(item['id']+'-prepared-inputs.npz'))
   for k in ['sequence','type_ids','speaker_ids','durs_rate','pitch_coefs']:assert np.array_equal(np.array(row[k]),old[k]),(item['id'],k)
  out=sessions['accent'].run(None,{'indices':inds.numpy(),'offsets':offsets.numpy()})[0]
  pr={'id':item['id'],'accent':metric(combined.numpy(),out),'stress_argmax_equal':bool(np.array_equal(st.argmax(1).numpy(),out[:,:metadata['stress_classes']].argmax(1))),'yo_argmax_equal':bool(np.array_equal(yo.argmax(1).numpy(),out[:,metadata['stress_classes']:].argmax(1)))}
  if ids:
   out=sessions['homograph'].run(None,{'input_ids':batch.numpy(),'homo_start_ids':np.array(starts,dtype=np.int64),'homo_end_ids':np.array(ends,dtype=np.int64)})[0];pr['homograph']=metric(logits.numpy(),out);pr['homograph_decisions_equal']=bool(np.array_equal((logits.numpy()>0),(out>0)))
  rows.append(row);parity.append(pr);print(item['id'],pr,flush=True)
 save_new(D/'golden.json',rows)
 (O/'auxiliary-corpus-parity.json').write_text(json.dumps(parity,indent=2))
 print('Captured',len(rows),'cases; original 8 prepared fixtures unchanged and exact')
