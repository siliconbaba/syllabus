#!/usr/bin/env python3
import argparse, hashlib
from common import *

def differences(a,b,path=''):
    if type(a)!=type(b):return [{'field':path,'before':a,'after':b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:out.append({'field':path+'/'+k,'beforePresent':k in a,'afterPresent':k in b,'before':a.get(k),'after':b.get(k)})
            else:out.extend(differences(a[k],b[k],path+'/'+k))
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [{'field':path,'before':a,'after':b}]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [{'field':path,'before':a,'after':b}]

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--revision',required=True);p.add_argument('--output',required=True);p.add_argument('--allowed-changed',default='');p.add_argument('--baseline-manifest');p.add_argument('--revision-manifest');a=p.parse_args()
    left,right=read(a.baseline),read(a.revision);lr,rr=raw_cases(a.baseline),raw_cases(a.revision)
    old={c['id']:c for c in left['cases']};new={c['id']:c for c in right['cases']};shared=sorted(old.keys()&new.keys());changed=[i for i in shared if old[i]!=new[i]];added=sorted(new.keys()-old.keys());removed=sorted(old.keys()-new.keys());allowed=set(filter(None,a.allowed_changed.split(',')))
    unexpected=sorted((set(changed)|set(added)|set(removed))-allowed)
    fs={c.get('scenarioFamilyId') for c in left['cases']+right['cases']}-{None};fam=[]
    for f in sorted(fs):
        ids=sorted({c['id'] for c in left['cases']+right['cases'] if c.get('scenarioFamilyId')==f})
        fam.append({'familyId':f,'siblings':ids,'changedSiblings':[i for i in ids if i in changed or i in added or i in removed], 'siblingDiffs':{i:differences(old.get(i),new.get(i)) for i in ids if old.get(i)!=new.get(i)},'declaredMutationChanged':[i for i in ids if old.get(i,{}).get('decisiveMutation')!=new.get(i,{}).get('decisiveMutation')], 'constantsChanged':'REQUIRES_SEMANTIC_QA: case prose cannot prove preservation of logical constants'})
    contracts=[]
    if bool(a.baseline_manifest)!=bool(a.revision_manifest):raise ValueError('provide both manifest versions')
    if a.baseline_manifest:
        l={f['scenarioFamilyId']:f for f in read(a.baseline_manifest)['familyManifest']};r={f['scenarioFamilyId']:f for f in read(a.revision_manifest)['familyManifest']}
        for f in sorted(l.keys()|r.keys()):
            contracts.append({'familyId':f,'constantsChanged':l.get(f,{}).get('factsThatMustRemainConstant')!=r.get(f,{}).get('factsThatMustRemainConstant'),'declaredMutationChanged':l.get(f,{}).get('singleLogicalVariable')!=r.get(f,{}).get('singleLogicalVariable') or l.get(f,{}).get('stateByMember')!=r.get(f,{}).get('stateByMember'),'diff':differences(l.get(f),r.get(f))})
    report={'changedIds':changed,'unchangedIds':[i for i in shared if i not in changed],'addedIds':added,'removedIds':removed,'unexpectedIds':unexpected,'byteIdenticalCount':sum(lr[i]==rr[i] for i in shared),'formatOnlyChangedIds':[i for i in shared if old[i]==new[i] and lr[i]!=rr[i]],'fieldDiffs':{i:differences(old[i],new[i]) for i in changed},'rootDiff':differences({k:v for k,v in left.items() if k!='cases'},{k:v for k,v in right.items() if k!='cases'}),'families':fam,'familyContractDiffs':contracts,'hashes':{'baseline':sha(a.baseline),'revision':sha(a.revision)}}
    write(Path(a.output)/'case-diff.json',report)
    issues=[{'unexpectedIds':unexpected}] if unexpected else []
    if report['rootDiff']:issues.append({'unexpectedRootDiff':report['rootDiff']})
    summary(a.output,issues,unexpectedChanges=len(unexpected)+bool(report['rootDiff']),families='REVIEW' if any(f['changedSiblings'] for f in fam) else 'PASS')
    if issues:raise SystemExit(1)
if __name__=='__main__':entry(main)
