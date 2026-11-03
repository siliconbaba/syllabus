#!/usr/bin/env python3
"""Local, standard-library task router. Never runs LLMs or edits content."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

PHASES = {'AUTHORING_READY':'TEST_BANK','FIX_READY':'TEST_BANK',
          'ARCHITECTURE_READY':'TEST_BANK','AWAITING_QA':'TEST_QA',
          'CASE_AUTHORING':'TEST_BANK','CASE_QA':'TEST_QA',
          'IMPLEMENTATION_READY':'CODE','CODE':'CODE',
          'IMPLEMENTATION_QA':'IMPLEMENTATION_QA'}
TERMINAL = {'HUMAN_DECISION','MANIFEST_FREEZE_READY','RELEASE_READY'}
GATES = ['sourceGrounding','levelRealization','semanticUniqueness',
         'runtimeSemantics','familyContracts','regression']
HUMAN = ['exact 300 target','standalone/linked totals','assessment eligibility',
         'level policy/distribution','topic coverage','family model','schema',
         'scoring model','runtime vocabulary','production import policy',
         'systemic methodology defect confirmed by independent QA']

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def read(p):
    return json.loads(Path(p).read_text())

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def atomic(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix='.write-')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        d = os.open(p.parent, os.O_RDONLY)
        try: os.fsync(d)
        finally: os.close(d)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

class Supervisor:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.project = self.root.parent.parent

    def load(self): return read(self.root/'STATE.json')
    def save(self, s):
        s['updatedAt'] = now()
        atomic(self.root/'STATE.json', s)

    def path(self, name):
        p = (self.project/name).resolve()
        if not p.is_relative_to(self.project): raise ValueError('Path escapes project')
        return p

    @contextlib.contextmanager
    def lock(self):
        # Never replace/unlink this inode. Kernel releases flock on process exit.
        with (self.root/'LOCK.json').open('a+') as f:
            try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: raise ValueError('Supervisor is locked')
            try:
                f.seek(0); f.truncate()
                json.dump({'pid':os.getpid(),'acquiredAt':now()}, f); f.flush(); os.fsync(f.fileno())
                yield
            finally:
                f.seek(0); f.truncate(); json.dump({'locked':False,'releasedAt':now()}, f); f.flush()
                fcntl.flock(f, fcntl.LOCK_UN)

    def event(self, name, **data):
        with (self.root/'run-log.jsonl').open('a') as f:
            f.write(json.dumps({'at':now(),'event':name,**data})+'\n'); f.flush(); os.fsync(f.fileno())

    def validate(self, s):
        if s['schemaVersion'] != 1 or s['phase'] not in set(PHASES)|TERMINAL:
            raise ValueError('Invalid schema/phase')
        if s['requiresHumanDecision'] != (s['phase']=='HUMAN_DECISION'):
            raise ValueError('Human gate state mismatch')
        if digest(self.path(s['acceptedBase'])) != s['acceptedBaseHash']:
            raise ValueError('Accepted base changed')
        for p, h in s['protectedInputs'].items():
            if digest(self.path(p)) != h: raise ValueError('Protected input changed: '+p)
        if s['workingCandidate'] and digest(self.path(s['workingCandidate'])) != s['candidateHash']:
            raise ValueError('Candidate mutated since handoff; reject and restore immutable revision')
        if s['phase'] in {'CASE_AUTHORING','CASE_QA','IMPLEMENTATION_READY','CODE','IMPLEMENTATION_QA','RELEASE_READY'} and not s.get('manifestFrozen'):
            raise ValueError('Manifest freeze required')
        if s['phase'] in {'IMPLEMENTATION_READY','CODE','IMPLEMENTATION_QA','RELEASE_READY'} and not s.get('casesAccepted'):
            raise ValueError('Case QA acceptance required')
        return {'status':'PASS','phase':s['phase']}

    def sync(self, s):
        atomic(self.root/'CURRENT-TASK.json', s.get('activeTask'))
        for name in ['qa-queue','qa-result','fix-queue','code-queue']:
            atomic(self.root/(name+'.json'), s.get('queues',{}).get(name,{'items':[]}))
        # Derived view; rewrite prevents duplicate entries after crash/replay.
        entries = s.get('routingHistory',[])
        p = self.root/'routing-log.jsonl'
        p.write_text(''.join(json.dumps(e)+'\n' for e in entries))
        if s['requiresHumanDecision']:
            g=s['humanDecisionReason']
            (self.root/'human-decision-needed.md').write_text(
                'DECISION NEEDED\n\n'+ '\n\n'.join(k+':\n'+g[k] for k in
                ['Question','Why automation cannot choose','Option A','Option B','Recommended'])+'\n')
        else:
            (self.root/'human-decision-needed.md').write_text('NO DECISION PENDING\n')

    def next(self, s):
        self.validate(s)
        if s['status'] != 'ACTIVE' or s['phase'] in TERMINAL:
            self.sync(s)
            return {'status':'HELD','phase':s['phase'],'reason':s.get('holdReason')}
        if s.get('activeTask'):
            self.sync(s)
            return s['activeTask']
        tid = str(uuid.uuid4())
        phase=s['phase']; worker=PHASES[phase]
        task={'taskId':tid,'worker':worker,'phase':phase,'base':s['acceptedBase'],
              'baseHash':s['acceptedBaseHash'],'candidate':s['workingCandidate'],
              'candidateHash':s['candidateHash'],'inputs':list(s['protectedInputs'])+[s['acceptedBase']]+([s['workingCandidate']] if s['workingCandidate'] else []),
              'outputs':[f'agent-artifacts/orchestration/tasks/{tid}/result.json'],
              'scope':s['nextScope'],'stopConditions':['invalid hashes','unsupported capability','five consecutive zero-yield attempts'],
              'humanGateConditions':HUMAN,'createdAt':now(),'claim':None,
              'instructions':f'workers/{worker.replace("_","-")}.md'}
        s['activeTask']=task; s['activeBatchId']=tid
        self.save(s); self.sync(s)
        atomic(self.root/'tasks'/tid/'task.json',task)
        self.event('task-prepared', taskId=tid)
        return task

    def claim(self, s, owner):
        self.validate(s)
        t=s.get('activeTask')
        if not t or s['status']!='ACTIVE': raise ValueError('No runnable task')
        if t['claim'] and t['claim']['owner']!=owner: raise ValueError('Task already claimed; recover explicitly after confirming old worker stopped')
        if t['worker'] in {'TEST_QA','IMPLEMENTATION_QA'} and owner==s.get('authorContext'):
            raise ValueError('QA must use independent context')
        if not t['claim']: t['claim']={'owner':owner,'token':str(uuid.uuid4()),'at':now()}
        self.save(s); self.sync(s)
        return t['claim']

    def submit(self, s, result):
        r=read(result); tid=r['taskId']
        expected=(self.root/'tasks'/tid/'result.json').resolve()
        if Path(result).resolve()!=expected or not expected.is_relative_to(self.root/'tasks'):
            raise ValueError('Receipt must be tasks/<taskId>/result.json')
        if tid in s.get('completedTasks',[]):
            if s.get('receiptHashes',{}).get(tid)!=digest(result): raise ValueError('Conflicting replay')
            self.sync(s); return {'status':'ALREADY_PROCESSED'}
        self.validate(s)
        t=s.get('activeTask')
        if not t or tid!=t['taskId'] or s['status']!='ACTIVE': raise ValueError('Wrong task or held state')
        if not t['claim'] or r['claimToken']!=t['claim']['token']: raise ValueError('Unclaimed or stale worker')
        if r['worker']!=t['worker'] or r['baseHash']!=t['baseHash']: raise ValueError('Worker/base mismatch')
        evidence=r.get('evidence',{})
        if not evidence: raise ValueError('Required evidence missing')
        for p,h in evidence.items():
            if digest(self.path(p))!=h: raise ValueError('Evidence hash mismatch')
        if r.get('status')!='COMPLETE': raise ValueError('Incomplete output')
        phase=s['phase']; outcome=r['outcome']; q=s.setdefault('queues',{})
        if outcome=='HUMAN_DECISION':
            reason=r['humanDecision']
            if reason['category'] not in HUMAN: raise ValueError('Not a structural/methodology gate')
            for k in ['Question','Why automation cannot choose','Option A','Option B','Recommended']:
                if not reason.get(k): raise ValueError('Incomplete human gate')
            s.update(phase='HUMAN_DECISION',requiresHumanDecision=True,humanDecisionReason=reason)
        elif t['worker'] in {'TEST_BANK','CODE'}:
            if outcome=='ROUTING_OR_METHOD_REVIEW':
                if r.get('consecutiveZeroYield',0)<5: raise ValueError('Routing stop requires five zero-yield attempts')
                s.update(phase='ARCHITECTURE_READY',status='ROUTING_REVIEW',holdReason='Review routing evidence; no automatic retry of exhausted method')
                s['reroutedUnits']+=r.get('reroutedUnits',[])
            elif outcome=='READY_FOR_QA':
                if r.get('selfQA')!='PASS': raise ValueError('Self QA required')
                candidate=self.path(r['candidate'])
                if not candidate.is_relative_to(self.root/'tasks'/tid): raise ValueError('Candidate must be new immutable task artifact')
                if digest(candidate)!=r['candidateHash']: raise ValueError('Candidate hash mismatch')
                if not r.get('changedUnits'): raise ValueError('Empty content must not be sent to QA')
                s.update(workingCandidate=r['candidate'],candidateHash=r['candidateHash'],authorContext=t['claim']['owner'],pendingQA=True,pendingFixes=False)
                s['qaReturnPhase']='IMPLEMENTATION_READY' if t['worker']=='CODE' else ('CASE_AUTHORING' if phase=='CASE_AUTHORING' or s.get('manifestFrozen') else 'AUTHORING_READY')
                s['phase']='IMPLEMENTATION_QA' if t['worker']=='CODE' else ('CASE_QA' if s.get('manifestFrozen') else 'AWAITING_QA')
                q['qa-queue']={'taskId':tid,'candidate':r['candidate'],'candidateHash':r['candidateHash'],'evidence':evidence,'changedUnits':r['changedUnits']}
            else: raise ValueError('Invalid author transition')
        elif t['worker'] in {'TEST_QA','IMPLEMENTATION_QA'}:
            if r.get('candidateHash')!=s['candidateHash']: raise ValueError('QA candidate mismatch')
            required=['tests','build','runtime','regression'] if t['worker']=='IMPLEMENTATION_QA' else GATES
            if set(required)-set(r.get('gates',{})): raise ValueError('Missing QA gates')
            if outcome=='PASS':
                if any(r['gates'][g]!='PASS' for g in required) or r.get('issues')!=[]: raise ValueError('QA PASS has failed gates/issues')
                if not isinstance(r.get('remainingUnresolved'),int) or r['remainingUnresolved']<0: raise ValueError('Unresolved accounting required')
                ids=r.get('remainingUnresolvedIDs')
                if not isinstance(ids,list) or len(set(ids))!=len(ids) or len(ids)!=r['remainingUnresolved']:
                    raise ValueError('Unresolved ID registry mismatch')
                if r['remainingUnresolved']>0 and not r.get('nextScope'):
                    raise ValueError('QA must provide next eligible scope from routing evidence')
                s['nextScope']=r.get('nextScope',[])
                s['remainingUnresolvedIDs']=ids
                s.update(acceptedBase=s['workingCandidate'],acceptedBaseHash=s['candidateHash'],lastAcceptedQA=str(Path(result).resolve().relative_to(self.project)),remainingUnresolved=r['remainingUnresolved'],workingCandidate=None,candidateHash=None,pendingQA=False,pendingFixes=False)
                s['completedBatches'].append(tid)
                s['pendingCode']=False
                if phase=='IMPLEMENTATION_QA': s['phase']='RELEASE_READY'
                elif phase=='CASE_QA' and r.get('allCasesComplete'):
                    s.update(phase='IMPLEMENTATION_READY',casesAccepted=True,pendingCode=True)
                elif r['remainingUnresolved']==0 and not s.get('manifestFrozen'):
                    s['phase']='MANIFEST_FREEZE_READY'
                else: s['phase']=s['qaReturnPhase']
                q['qa-queue']={'items':[]}; q['fix-queue']={'items':[]}
            elif outcome=='FIX_REQUIRED':
                if not r.get('issues'): raise ValueError('Fix requires scoped issues')
                s.update(phase='CODE' if phase=='IMPLEMENTATION_QA' else 'FIX_READY',pendingQA=False,pendingFixes=True)
                q['fix-queue']={'candidate':s['workingCandidate'],'items':r['issues']}
            else: raise ValueError('Invalid QA transition')
            q['qa-result']=r
        else: raise ValueError('Unsupported transition')
        s.setdefault('completedTasks',[]).append(tid)
        s.setdefault('receiptHashes',{})[tid]=digest(result)
        s.setdefault('routingHistory',[]).append({'taskId':tid,'from':phase,'to':s['phase'],'at':now(),'outcome':outcome})
        s.update(activeTask=None,activeBatchId=None)
        self.save(s); self.sync(s); self.event('result-accepted',taskId=tid)
        return {'status':'ACCEPTED','phase':s['phase']}

    def recover(self, s, stopped):
        self.validate(s)
        t=s.get('activeTask')
        if t:
            result=self.root/'tasks'/t['taskId']/'result.json'
            if result.exists(): return self.submit(s,result)
            if stopped:
                # Operator attests old execution is stopped; invalidate stale tokens.
                t['claim']=None; self.save(s)
        self.sync(s)
        return {'status':'RESUMABLE' if t else 'IDLE','taskId':t['taskId'] if t else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default=str(Path(__file__).resolve().parent))
    p.add_argument('command',choices=['status','validate','next','claim','submit','recover','human-gate','enable','freeze','heartbeat'])
    p.add_argument('--owner'); p.add_argument('--result'); p.add_argument('--decision')
    p.add_argument('--confirmed-worker-stopped',action='store_true')
    a=p.parse_args(); x=Supervisor(a.root)
    try:
        with x.lock():
            s=x.load()
            if a.command=='status': out=s
            elif a.command=='validate': out=x.validate(s)
            elif a.command=='next': out=x.next(s)
            elif a.command=='claim':
                if not a.owner: raise ValueError('--owner (fresh context ID) required')
                out=x.claim(s,a.owner)
            elif a.command=='submit': out=x.submit(s,a.result)
            elif a.command=='recover': out=x.recover(s,a.confirmed_worker_stopped)
            elif a.command=='human-gate':
                g=read(a.decision)
                if g.get('category') not in HUMAN: raise ValueError('Not a human gate category')
                for k in ['Question','Why automation cannot choose','Option A','Option B','Recommended']:
                    if not g.get(k): raise ValueError('Incomplete decision')
                s.update(phase='HUMAN_DECISION',requiresHumanDecision=True,humanDecisionReason=g,status='ACTIVE')
                x.save(s); x.sync(s); out={'status':'HELD'}
            elif a.command=='enable':
                x.validate(s)
                if s['requiresHumanDecision']: raise ValueError('Human decision needs reviewed state migration; enable cannot override')
                if s['status']!='BOOTSTRAP_ONLY': raise ValueError('Only bootstrap can be enabled here')
                if not a.decision: raise ValueError('Path to explicit user continuation authorization required')
                s['authorization']={'path':a.decision,'sha256':digest(a.decision)}
                s.update(status='ACTIVE',holdReason=None); x.save(s); out={'status':'ACTIVE'}
            elif a.command=='freeze':
                x.validate(s); d=read(a.decision)
                if s['phase']!='MANIFEST_FREEZE_READY' or s['remainingUnresolved']!=0 or any(i['status']!='CLOSED' for i in s['preFreezeCleanup']): raise ValueError('Freeze prerequisites not met')
                if d.get('approvedBaseHash')!=s['acceptedBaseHash'] or d.get('approved') is not True: raise ValueError('Explicit scoped freeze approval required')
                s.update(manifestFrozen=True,phase='CASE_AUTHORING'); x.save(s); x.sync(s); out={'status':'FROZEN'}
            else:
                out=x.validate(s); task=x.next(s)
                out={'at':now(),'validation':out,'next':task}; atomic(x.root/'automation/heartbeat-status.json',out)
                x.event('heartbeat',status=task.get('status','TASK_READY'))
        print(json.dumps(out,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e:
        print(json.dumps({'status':'ERROR','error':str(e)}),file=sys.stderr); return 1
    return 0
if __name__=='__main__': sys.exit(main())
