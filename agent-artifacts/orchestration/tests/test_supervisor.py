import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MODULE=Path(__file__).resolve().parents[1]/'supervisor.py'
spec=importlib.util.spec_from_file_location('supervisor',MODULE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)
        self.root=self.project/'agent-artifacts/orchestration';self.root.mkdir(parents=True)
        self.base=self.project/'base.json';self.base.write_text('{"dummy":0}')
        self.x=m.Supervisor(self.root)
        self.s={'schemaVersion':1,'project':'fixture','phase':'AUTHORING_READY','status':'ACTIVE','acceptedBase':'base.json','acceptedBaseHash':m.digest(self.base),'protectedInputs':{},'requiresHumanDecision':False,'humanDecisionReason':None,'workingCandidate':None,'candidateHash':None,'nextScope':['dummy only'],'activeTask':None,'remainingUnresolved':1,'remainingUnresolvedIDs':['DUMMY-1'],'completedTasks':[],'completedBatches':[],'reroutedUnits':[],'preFreezeCleanup':[],'manifestFrozen':False,'casesAccepted':False,'pendingQA':False,'pendingFixes':False,'pendingCode':False}
        self.x.save(self.s)

    def task(self,owner='author'):
        t=self.x.next(self.s);c=self.x.claim(self.s,owner)
        d=self.root/'tasks'/t['taskId'];d.mkdir(exist_ok=True,parents=True)
        e=d/'evidence.md';e.write_text('Dummy evidence for router tests only')
        r={'taskId':t['taskId'],'worker':t['worker'],'baseHash':t['baseHash'],'claimToken':c['token'],'status':'COMPLETE','evidence':{str(e.relative_to(self.project)):m.digest(e)}}
        return t,d,r

    def submit(self,d,r):
        p=d/'result.json';m.atomic(p,r);return self.x.submit(self.s,p)

    def author(self):
        t,d,r=self.task();c=d/'candidate.json';c.write_text('{"dummy":1}')
        r.update(outcome='READY_FOR_QA',candidate=str(c.relative_to(self.project)),candidateHash=m.digest(c),selfQA='PASS',changedUnits=['DUMMY-1'])
        self.submit(d,r);return d,r,c

    def qa(self):
        t,d,r=self.task('qa-independent')
        r.update(outcome='PASS',candidateHash=self.s['candidateHash'],gates={g:'PASS' for g in m.GATES},issues=[],remainingUnresolved=1,remainingUnresolvedIDs=['DUMMY-2'],nextScope=['DUMMY-2'])
        return d,r

    def test_requested_dry_run(self):
        self.author();self.assertEqual(self.s['phase'],'AWAITING_QA')
        d,r=self.qa();self.submit(d,r)
        self.assertEqual(self.s['phase'],'AUTHORING_READY');self.x.validate(self.s)

    def test_no_double_processing(self):
        d,r,c=self.author();self.assertEqual(self.submit(d,r)['status'],'ALREADY_PROCESSED')
        first=self.x.next(self.s);self.assertEqual(self.x.next(self.s)['taskId'],first['taskId'])
        r['selfQA']='FAIL'
        with self.assertRaises(ValueError):self.submit(d,r)

    def test_lock_works_between_processes(self):
        with self.x.lock():
            p=subprocess.run([sys.executable,str(MODULE),'--root',str(self.root),'next'],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('locked',p.stderr)
        with self.x.lock():pass

    def test_invalid_transition_rejected(self):
        t,d,r=self.task();r['outcome']='PASS'
        with self.assertRaises(ValueError):self.submit(d,r)
        self.assertEqual(self.s['phase'],'AUTHORING_READY')

    def test_qa_candidate_mutation_rejected(self):
        _,_,c=self.author();d,r=self.qa();c.write_text('{"dummy":"tampered"}')
        with self.assertRaisesRegex(ValueError,'Candidate mutated'):self.submit(d,r)

    def test_independent_context_required(self):
        self.author();self.x.next(self.s)
        with self.assertRaisesRegex(ValueError,'independent'):self.x.claim(self.s,'author')

    def test_human_gate_stops(self):
        t,d,r=self.task();r.update(outcome='HUMAN_DECISION',humanDecision={'category':'schema',**{k:'fixture' for k in ['Question','Why automation cannot choose','Option A','Option B','Recommended']}})
        self.submit(d,r);self.assertEqual(self.x.next(self.s)['status'],'HELD');self.assertTrue(self.s['requiresHumanDecision'])

    def test_recovery_after_interruption(self):
        t,d,r=self.task();self.assertEqual(self.x.recover(self.s,False)['taskId'],t['taskId'])
        with self.assertRaises(ValueError):self.x.claim(self.s,'other')
        self.x.recover(self.s,True);self.x.claim(self.s,'other')
        r.update(outcome='ROUTING_OR_METHOD_REVIEW',consecutiveZeroYield=5)
        with self.assertRaisesRegex(ValueError,'stale'):self.submit(d,r)

    def test_recovery_valid_receipt_and_views(self):
        _,_,c=self.author();d,r=self.qa();m.atomic(d/'result.json',r)
        self.x.recover(self.s,False);self.assertEqual(self.s['phase'],'AUTHORING_READY')
        (self.root/'CURRENT-TASK.json').write_text('broken')
        self.x.recover(self.s,False);self.assertIsNone(m.read(self.root/'CURRENT-TASK.json'))

    def test_bootstrap_hold(self):
        self.s['status']='BOOTSTRAP_ONLY';self.assertEqual(self.x.next(self.s)['status'],'HELD');self.assertIsNone(self.s['activeTask'])

    def test_bad_evidence(self):
        t,d,r=self.task();r.update(outcome='ROUTING_OR_METHOD_REVIEW',consecutiveZeroYield=5);r['evidence']['base.json']='bad'
        with self.assertRaisesRegex(ValueError,'Evidence'):self.submit(d,r)

    def test_fix_routing(self):
        self.author();d,r=self.qa();r.update(outcome='FIX_REQUIRED',issues=[{'id':'DUMMY-ISSUE'}])
        self.submit(d,r);self.assertEqual(self.s['phase'],'FIX_READY')

    def test_zero_yield_stop(self):
        t,d,r=self.task();r.update(outcome='ROUTING_OR_METHOD_REVIEW',consecutiveZeroYield=5,reroutedUnits=['dummy'])
        self.submit(d,r);self.assertEqual(self.x.next(self.s)['status'],'HELD')

    def test_premature_implementation_rejected(self):
        self.s['phase']='CODE'
        with self.assertRaisesRegex(ValueError,'freeze'):self.x.validate(self.s)

    def test_future_case_and_implementation_routes(self):
        self.s.update(phase='CASE_AUTHORING',manifestFrozen=True)
        self.author();self.assertEqual(self.s['phase'],'CASE_QA')
        d,r=self.qa();r.update(remainingUnresolved=0,remainingUnresolvedIDs=[],allCasesComplete=True)
        self.submit(d,r);self.assertEqual(self.s['phase'],'IMPLEMENTATION_READY')
        self.author();self.assertEqual(self.s['phase'],'IMPLEMENTATION_QA')
        d,r=self.qa();r.update(gates={g:'PASS' for g in ['tests','build','runtime','regression']},remainingUnresolved=0,remainingUnresolvedIDs=[])
        self.submit(d,r);self.assertEqual(self.s['phase'],'RELEASE_READY')

    def test_registry_mismatch_rejected(self):
        self.author();d,r=self.qa();r['remainingUnresolvedIDs']=[]
        with self.assertRaisesRegex(ValueError,'registry'):self.submit(d,r)

    def test_process_death_releases_kernel_lock(self):
        code = "import fcntl,time; f=open(%r,'a+'); fcntl.flock(f,fcntl.LOCK_EX); print('locked',flush=True); time.sleep(60)" % str(self.root/'LOCK.json')
        p=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(p.stdout.readline().strip(),'locked')
            p.kill();p.wait()
            with self.x.lock():pass
        finally:
            if p.poll() is None:p.kill();p.wait()
            p.stdout.close()

    def test_freeze_readiness_only(self):
        self.author();d,r=self.qa();r.update(remainingUnresolved=0,remainingUnresolvedIDs=[])
        self.submit(d,r);self.assertEqual(self.s['phase'],'MANIFEST_FREEZE_READY');self.assertEqual(self.x.next(self.s)['status'],'HELD')

if __name__=='__main__':unittest.main()
