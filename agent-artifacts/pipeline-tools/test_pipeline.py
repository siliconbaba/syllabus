#!/usr/bin/env python3
"""Regression tests for tooling. Fixtures are temporary; no historical artifact is edited."""
import copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from common import *
from build_batch_context import retrieve
from diff_case_sets import differences
HERE=Path(__file__).resolve().parent
MANIFEST=ROOT/'agent-artifacts/manifests/v2.2.3/production_manifest_masterplan_v2_2_3.json'
BATCH=ROOT/'agent-artifacts/test-bank/batch-03-r3/cases_TC076_TC100_r3.json'
class PipelineTests(unittest.TestCase):
 def test_safety_and_stability(self):
  rows=batch_rows(read(MANIFEST),4);cs=read(PRODUCTION)['cases'];a=retrieve(rows,cs);self.assertEqual(a,retrieve(rows,list(reversed(cs))))
  for row,result in zip(rows,a):
   must={c['id'] for c in cs if c['topicId']==row['topicId'] or c['primaryPattern']==row['primaryPattern']}
   self.assertTrue(must<={x['id'] for x in result['analogs']});self.assertGreaterEqual(len(result['analogs']),6)
 def test_raw_and_semantic_diff(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);x=read(BATCH);y=copy.deepcopy(x);y['cases'][0]['options'][1]['explanation']+=' Changed.'
   write(t/'a.json',x);write(t/'b.json',y)
   args=[sys.executable,str(HERE/'diff_case_sets.py'),'--baseline',str(t/'a.json'),'--revision',str(t/'b.json'),'--output',str(t/'out')]
   self.assertEqual(subprocess.run(args,capture_output=True).returncode,1)
   self.assertEqual(subprocess.run(args+['--allowed-changed','TC-076'],capture_output=True).returncode,0)
   d=read(t/'out/case-diff.json');self.assertEqual(d['changedIds'],['TC-076']);self.assertEqual(d['byteIdenticalCount'],24);self.assertEqual(d['fieldDiffs']['TC-076'][0]['field'],'/options/1/explanation')
   (t/'b.json').write_text(json.dumps(x,ensure_ascii=False))
   self.assertEqual(subprocess.run(args,capture_output=True).returncode,0)
   d=read(t/'out/case-diff.json');self.assertEqual(d['changedIds'],[]);self.assertEqual(d['byteIdenticalCount'],0)
 def test_duplicate_keys_ids(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x.json';p.write_text('{"x":1,"x":2}')
   with self.assertRaises(ValueError):read(p)
   write(p,{'cases':[{'id':'X'},{'id':'X'}]})
   with self.assertRaises(ValueError):raw_cases(p)
 def test_schema_runtime_negative(self):
  self.assertEqual(runtime(BATCH)['schema'],'PASS')
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'cases.json';x=read(BATCH);del x['cases'][0]['sourceTopicExplanation'];write(p,x)
   self.assertEqual(runtime(p)['schema'],'FAIL')
   x=read(BATCH);x['cases'][0]['primaryPattern']='nonexistent-code';write(p,x)
   self.assertEqual(runtime(p)['runtime'],'FAIL')
 def test_bad_family_eligibility_detected(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);x=read(BATCH);x['cases'][0]['assessmentEligible']=True;write(t/'cases.json',x)
   result=subprocess.run([sys.executable,str(HERE/'validate_batch.py'),'--batch','3','--manifest',str(MANIFEST),'--cases',str(t/'cases.json'),'--output',str(t/'out')],capture_output=True)
   self.assertEqual(result.returncode,1);self.assertTrue(any('eligibility' in str(i) for i in read(t/'out/validation-summary.json')['issues']))
 def test_pack_reproducibility_and_tampering(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t)
   args=[sys.executable,str(HERE/'build_batch_context.py'),'--batch','4','--manifest',str(MANIFEST),'--production',str(PRODUCTION),'--output',str(t/'pack')]
   subprocess.run(args,check=True,capture_output=True)
   current=ROOT/'agent-artifacts/context-packs/batch-04'
   self.assertEqual(read(current/'artifact-hashes.json'),read(t/'pack/artifact-hashes.json'))
   self.assertEqual(read(t/'pack/authoring-readiness.json')['status'],'BLOCKED')
   (t/'pack/manifest-rows.json').write_text('[]\n')
   result=subprocess.run([sys.executable,str(HERE/'verify_context.py'),'--pack',str(t/'pack'),'--output',str(t/'verify')],capture_output=True)
   self.assertEqual(result.returncode,1)
   self.assertEqual(read(t/'verify/validation-summary.json')['issues'],[{'packHashMismatch':'manifest-rows.json'}])
 def test_stale_evidence_blocks_pack(self):
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);write(t/'index.json',{'productionSha256':'stale'})
   result=subprocess.run([sys.executable,str(HERE/'build_batch_context.py'),'--batch','4','--manifest',str(MANIFEST),'--production',str(PRODUCTION),'--evidence',str(t/'index.json'),'--output',str(t/'out')],capture_output=True)
   self.assertEqual(result.returncode,1);self.assertEqual(read(t/'out/validation-summary.json')['status'],'FAIL')
if __name__=='__main__':unittest.main(verbosity=2)
