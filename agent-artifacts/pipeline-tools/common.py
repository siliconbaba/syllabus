"""Shared deterministic helpers; no production mutations or network dependencies."""
import hashlib, json, re, subprocess, tempfile, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT/'InteractiveBook/TrainerContent/topics.json'
BOOK = ROOT/'InteractiveBook/WebContent/index.html'
PRODUCTION = ROOT/'InteractiveBook/TrainerContent/cases.json'

def read(p):
    def unique(pairs):
        d = {}
        for k,v in pairs:
            if k in d: raise ValueError('duplicate JSON key: '+k)
            d[k]=v
        return d
    return json.loads(Path(p).read_text(), object_pairs_hook=unique)
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(c):return hashlib.sha256(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def raw_cases(p):
    s=Path(p).read_text();match=re.search(r'"cases"\s*:\s*\[',s)
    if not match: raise ValueError('missing cases array')
    i=match.end();out={};decoder=json.JSONDecoder()
    while True:
        while s[i].isspace() or s[i]==',':i+=1
        if s[i]==']':break
        c,end=decoder.raw_decode(s,i)
        if c['id'] in out:raise ValueError('duplicate ID '+c['id'])
        out[c['id']]=s[i:end].encode();i=end
    return out

def runtime(bank=None):
    sources=[ROOT/'InteractiveBook/Trainer/TrainerModels.swift',ROOT/'InteractiveBook/Trainer/TrainerScoringMapping.swift',Path(__file__).with_name('RuntimeProbe.swift')]
    # No persistent executable cache: compile current authoritative sources each invocation.
    with tempfile.TemporaryDirectory(prefix='trainer-pipeline-') as tmp:
        exe=Path(tmp)/'probe'
        result=subprocess.run(['/bin/bash','-c','source "$1"; prepare_xcode >/dev/null; shift; /usr/bin/xcrun swiftc "$@"','pipeline',str(ROOT/'scripts/common.sh'),*[str(p) for p in sources],'-module-cache-path',str(Path(tmp)/'module-cache'),'-o',str(exe)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError('Swift probe compile failed: '+result.stderr[-2000:])
        args=[str(exe)]
        if bank:
            shutil.copyfile(bank,Path(tmp)/'cases.json');shutil.copyfile(CATALOG,Path(tmp)/'topics.json');args.append(str(Path(tmp)/'cases.json'))
        result=subprocess.run(args,capture_output=True,text=True,check=True)
        return json.loads(result.stdout)

def batch_rows(manifest,batch):
    rows=[r for r in manifest['manifest'] if r['batch']==f'Batch {batch:02}']
    expected=[f'TC-{i:03}' for i in range(batch*25+1,batch*25+26)]
    if [r['plannedId'] for r in rows]!=expected:raise ValueError('Manifest batch range/count mismatch')
    return rows

def summary(output,issues=(),**values):
    result={'status':'FAIL' if issues else 'PASS','structural':'FAIL' if issues else 'PASS','schema':'NOT_APPLICABLE','runtime':'NOT_APPLICABLE','families':'NOT_APPLICABLE','unexpectedChanges':0,'surface':{'status':'NOT_RUN'},'issues':list(issues),**values}
    write(Path(output)/'validation-summary.json',result);return result

def entry(fn):
    import sys
    try:fn()
    except Exception as e:
        if '--output' in sys.argv:
            summary(sys.argv[sys.argv.index('--output')+1],[str(e)])
        print(str(e),file=sys.stderr);sys.exit(1)
