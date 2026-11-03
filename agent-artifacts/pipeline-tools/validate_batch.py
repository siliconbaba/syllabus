#!/usr/bin/env python3
"""Manifest-policy checks around the actual production Swift loader, not a replacement schema."""
import argparse, collections, re
from common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True,type=int);p.add_argument('--manifest',required=True);p.add_argument('--cases',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    m=read(a.manifest);rows=batch_rows(m,a.batch);bank=read(a.cases);cs=bank['cases'];issues=[]
    def check(ok,where,expected,actual):
        if not ok:issues.append({'at':where,'expected':expected,'actual':actual})
    check([c['id'] for c in cs]==[r['plannedId'] for r in rows],'IDs',[r['plannedId'] for r in rows],[c['id'] for c in cs])
    plans={r['plannedId']:r for r in rows};fields=['partId','topicId','domain','requiredLevel','primaryPattern','secondaryPatterns','scenarioFamilyId','trainingEligible','assessmentEligible']
    lengths={};positions=collections.Counter();strings=collections.defaultdict(list);hits=collections.Counter()
    for c in cs:
        cid=c['id'];plan=plans.get(cid,{})
        for k in fields:check(c.get(k)==plan.get(k),cid+'.'+k,plan.get(k),c.get(k))
        opts=c['options'];check(len(opts)==4 and {o['id'] for o in opts}==set('ABCD'),cid+'.options','A/B/C/D unique',[o['id'] for o in opts])
        best=[o for o in opts if o['isBest']];check(len(best)==1,cid+'.isBest',1,len(best))
        check(sum(o['decisionQuality']==1 for o in opts)==1,cid+'.quality', 'exactly one 1.0',[o['decisionQuality'] for o in opts])
        for o in opts:check(isinstance(o['decisionQuality'],(float,int)) and not isinstance(o['decisionQuality'],bool) and 0<=o['decisionQuality']<=1 and (o['decisionQuality']==1)==o['isBest'],cid+'.'+o['id']+'.quality','0..1; best iff 1',o['decisionQuality'])
        check(c.get('trainingEligible') is True and c.get('assessmentEligible')==(not bool(c.get('scenarioFamilyId'))),cid+'.eligibility','standalone only assessment',[c.get('trainingEligible'),c.get('assessmentEligible')])
        lengths[cid]=[{ 'id':o['id'],'words':len(re.findall(r'\w+',o['text'])),'chars':len(o['text'])} for o in opts]
        for field in ['context','question']:
            strings[(field,c[field])].append(cid)
        for o in opts:strings[('option.text',o['text'])].append(cid+'.'+o['id'])
        if len(best)==1:
            positions[best[0]['id']]+=1
            for name,fn in [('longest',lambda o:len(o['text'])),('shortest',lambda o:-len(o['text'])),('mostClauses',lambda o:o['text'].count(',')+o['text'].count(';')),('mostNumbers',lambda o:len(re.findall(r'\d',o['text'])))]:
                top=max(fn(o) for o in opts);tied=[o for o in opts if fn(o)==top]
                hits[name]+=sum(o['isBest'] for o in tied)/len(tied)
    families={r['scenarioFamilyId'] for r in rows if r.get('scenarioFamilyId')}
    for f in families:
        contract=next(x for x in m['familyManifest'] if x['scenarioFamilyId']==f)
        members=[c['id'] for c in cs if c.get('scenarioFamilyId')==f]
        check(set(members)==set(contract['memberIds']),f+'.members',contract['memberIds'],members)
        pos=[plans[i]['familyPosition'] for i in members if i in plans];check(sorted(pos)==list(range(1,len(members)+1)),f+'.positions','1..N',pos)
    probe=runtime(a.cases);write(Path(a.output)/'runtime-loader.json',probe)
    if probe.get('schema')!='PASS' or probe.get('runtime')!='PASS':issues.append({'runtimeLoader':probe})
    duplicates=[{'field':k[0],'occurrences':v,'text':k[1]} for k,v in strings.items() if len(v)>1]
    surface={'status':'REQUIRES_INDEPENDENT_QA','method':'4 exploratory rules; fractional random-tie credit; no pass threshold or semantic verdict','bestSimpleHeuristic':f'{max(hits.values(),default=0):g}/{len(cs)}','rules':dict(hits),'exactDuplicateStrings':len(duplicates)}
    write(Path(a.output)/'batch-metrics.json',{'count':len(cs),'standalone':sum(not c.get('scenarioFamilyId') for c in cs),'linked':sum(bool(c.get('scenarioFamilyId')) for c in cs),'familyCount':len(families),'levels':dict(collections.Counter(c['requiredLevel'] for c in cs)),'correctPositions':dict(positions),'optionLengths':lengths,'duplicateStrings':duplicates,'surface':surface,'hashes':{'cases':sha(a.cases),'manifest':sha(a.manifest),'catalog':sha(CATALOG)}})
    summary(a.output,issues,schema=probe.get('schema','FAIL'),runtime=probe.get('runtime','FAIL'),families='FAIL' if any('.members' in str(i) or '.positions' in str(i) for i in issues) else 'PASS',surface=surface)
    if issues:raise SystemExit(1)
if __name__=='__main__':entry(main)
