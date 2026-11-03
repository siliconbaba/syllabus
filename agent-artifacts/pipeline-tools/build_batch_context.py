#!/usr/bin/env python3
import argparse, collections, math, re, sys
from common import *
sys.path.insert(0,str(ROOT/'scripts'))
from check_content import Parser, norm

def tokens(text):return set(re.findall(r'[a-zа-яё0-9]{3,}',str(text).lower()))
def retrieve(rows,cases,n=6):
    texts={c['id']:tokens(' '.join([c['context'],c['question'],*c['decisiveFacts'],c['keyInsight']])) for c in cases}
    df=collections.Counter(t for ts in texts.values() for t in ts);out=[]
    for row in rows:
        ts=tokens(' '.join([row['oneSentenceScenarioConcept'],row['oneSentenceDecisionBoundary'],*row['decisiveFactsConcept']]))
        scored=[]
        for c in cases:
            reasons=[];score=0
            for k,w in [('topicId',6),('domain',3),('primaryPattern',5),('requiredLevel',1)]:
                if row[k]==c[k]:score+=w;reasons.append(k)
            overlap=set([row['primaryPattern']]+row['secondaryPatterns'])&set([c['primaryPattern']]+c['secondaryPatterns']);score+=2*len(overlap)
            words=sorted(ts&texts[c['id']]);lex=sum(math.log((len(cases)+1)/(df[t]+1))+1 for t in words)/max(1,len(ts));score+=lex
            scored.append({'id':c['id'],'retrievalScore':round(score,6),'reasons':reasons,'patternOverlap':sorted(overlap),'sharedTerms':words})
        scored.sort(key=lambda x:(-x['retrievalScore'],x['id']));top={x['id'] for x in scored[:n]}
        safety={c['id'] for c in cases if c['topicId']==row['topicId'] or c['primaryPattern']==row['primaryPattern']}
        selected=[x for x in scored if x['id'] in top|safety]
        out.append({'plannedId':row['plannedId'],'topN':n,'weakRetrieval':not any(x['reasons'] and any(k in x['reasons'] for k in ['topicId','primaryPattern']) for x in scored[:n]),'analogs':selected,'safetyAdded':sorted(safety-top),'safetyCoverage':'PASS','semanticVerdict':'NOT_EVALUATED'})
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',type=int,required=True);p.add_argument('--manifest',required=True);p.add_argument('--production',required=True);p.add_argument('--output',required=True);p.add_argument('--evidence',default=str(ROOT/'agent-artifacts/contracts/approved-case-evidence.json'));a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);m=read(a.manifest);rows=batch_rows(m,a.batch);cs=read(a.production)['cases'];ev=read(a.evidence)
    if ev['productionSha256']!=sha(a.production):raise ValueError('Stale approved evidence index: regenerate with approval provenance')
    for name,h in ev.get('contextHashes',{}).items():
        if sha(name)!=h:raise ValueError('Stale evidence context: '+name)
    byid={c['id']:c for c in cs}
    if len(ev['cases'])!=len(cs) or {c['id'] for c in ev['cases']}!=set(byid):raise ValueError('Incomplete evidence index')
    for item in ev['cases']:
        if canonical(byid[item['id']])!=item['contentHash']:raise ValueError('Evidence case hash mismatch '+item['id'])
        for name,h in item['evidenceHashes'].items():
            if sha(ROOT/name)!=h:raise ValueError('Historical evidence changed: '+name)
    famids={r['scenarioFamilyId'] for r in rows if r.get('scenarioFamilyId')};families=[f for f in m['familyManifest'] if f['scenarioFamilyId'] in famids]
    rowids={r['plannedId'] for r in rows}
    if any(not set(f['memberIds'])<=rowids for f in families):raise ValueError('Cross-batch family: explicitly expand context; do not omit siblings')
    vocab=runtime();topics=sorted({r['topicId'] for r in rows});domains=sorted({r['domain'] for r in rows});patterns=sorted({p for r in rows for p in [r['primaryPattern']]+r['secondaryPatterns']})
    if set(domains)-vocab['domains'].keys() or set(patterns)-vocab['patterns'].keys():raise ValueError('Unknown runtime vocabulary in planned batch')
    parser=Parser();parser.feed(BOOK.read_text());nodes={n.attrs.get('id'):n for n in parser.root.all() if n.has('topic')};catalog={t['id']:t for t in read(CATALOG)['topics']};sections=[];sourceindex=[]
    for tid in topics:
        if tid not in nodes or tid not in catalog:raise ValueError('Missing source topic '+tid)
        # Whole topic, including all substantive examples/tables; never truncate source to keywords.
        node=nodes[tid];parts=[]
        def walk(n):
            if n.tag in ['script','style'] or n.has('studied'):return
            for child in n.children:
                if isinstance(child,str):parts.append(child)
                else:walk(child)
            if n.tag in ['p','li','h3','h4','h5','tr','td','th','div','pre']:parts.append('\n')
        walk(node);text='\n'.join(norm(s) for s in ''.join(parts).splitlines() if norm(s))
        (out/'source-topics').mkdir(exist_ok=True)
        (out/'source-topics'/f'{tid}.md').write_text(f'# {tid} — {catalog[tid]["title"]}\n\n{text}\n')
        sections.append(f'## {tid} — {catalog[tid]["title"]}\n\n{text}\n')
        sourceindex.append({'topicId':tid,'title':catalog[tid]['title'],'characters':len(text),'textSha256':hashlib.sha256(text.encode()).hexdigest()})
    (out/'source-topics.md').write_text('# Full relevant textbook topics\n\nSource: InteractiveBook/WebContent/index.html. No substantive truncation; cross-topic references may require expansion.\n\n'+'\n'.join(sections))
    short=retrieve(rows,cs);selected={x['id'] for r in short for x in r['analogs']}
    # Full analog dossiers once, not duplicated under every planned row.
    (out/'analog-cases').mkdir(exist_ok=True)
    for c in cs:
        if c['id'] in selected:write(out/'analog-cases'/f'{c["id"]}.json',c)
    write(out/'production-analog-cases.json',{'cases':[c for c in cs if c['id'] in selected]})
    contract={'batch':a.batch,'range':[rows[0]['plannedId'],rows[-1]['plannedId']],'manifestVersion':m['manifestVersion'],'count':len(rows),'standalone':sum(not r.get('scenarioFamilyId') for r in rows),'linked':sum(bool(r.get('scenarioFamilyId')) for r in rows),'families':len(families),'levels':dict(collections.Counter(r['requiredLevel'] for r in rows)),'trainingEligible':sum(r['trainingEligible'] for r in rows),'assessmentEligible':sum(r['assessmentEligible'] for r in rows),'topicIds':topics,'domains':{d:vocab['domains'][d] for d in domains},'patterns':{p:vocab['patterns'][p] for p in patterns},'sources':{str(Path(a.manifest).resolve()):sha(a.manifest),str(Path(a.production).resolve()):sha(a.production),str(BOOK):sha(BOOK),str(CATALOG):sha(CATALOG),str(ROOT/'InteractiveBook/Trainer/TrainerScoringMapping.swift'):sha(ROOT/'InteractiveBook/Trainer/TrainerScoringMapping.swift')},'authoringStarted':False}
    contract['sources'].update(ev['contextHashes'])
    contract['sources'][str(Path(a.evidence).resolve())]=sha(a.evidence)
    preflight=ROOT/f'agent-artifacts/test-bank/batch-{a.batch:02}/preflight-validation.json'
    readiness={'status':'NOT_ASSESSED','note':'Mechanical preparation never grants semantic authoring approval.'}
    if preflight.is_file():
        for name,h in read(preflight.parent/'input-hashes.json').items():
            if sha(ROOT/name)!=h:raise ValueError('Existing preflight is stale: '+name)
        for name,h in read(preflight.parent/'artifact-hashes.json').items():
            if sha(preflight.parent/name)!=h:raise ValueError('Existing preflight artifact mismatch: '+name)
        existing=read(preflight)
        readiness={'status':'BLOCKED' if existing.get('manifestBlockerIDs') else 'REQUIRES_SEMANTIC_REVIEW','source':str(preflight),'sourceSha256':sha(preflight),'manifestBlockerIDs':existing.get('manifestBlockerIDs',[]),'note':'Existing external preflight, not a new semantic verdict by this generator.'}
        contract['sources'][str(preflight)]=sha(preflight)
        contract['sources'][str(preflight.parent/'authoring-report.md')]=sha(preflight.parent/'authoring-report.md')
    write(out/'authoring-readiness.json',readiness)
    write(out/'batch-contract.json',contract);write(out/'manifest-rows.json',rows);write(out/'family-contracts.json',families);write(out/'source-topic-index.json',sourceindex);write(out/'production-analog-shortlist.json',short);write(out/'approved-evidence-index.json',{**ev,'cases':[c for c in ev['cases'] if c['id'] in selected]})
    (out/'README.md').write_text('''# Batch context pack (preparation only)

Author: read PIPELINE-CONTRACT and TEST-BANK-RUNBOOK in ../../contracts, then batch-contract.json, manifest-rows.json, family-contracts.json and source-topics.md. Review production-analog-shortlist.json; read individual analog-cases/TC-XXX.json dossiers and source-topics/TOPIC.md just in time for each skeleton. Aggregated source-topics.md and production-analog-cases.json are convenience copies: do not read both aggregate and per-item copies.

QA: follow TEST-QA-RUNBOOK; use a key-hidden candidate view first. The shortlist is not a duplication verdict. Approved evidence supports unchanged historical content only.

Authoritative: original frozen manifest, actual Swift runtime, schema and textbook at the paths/hashes in batch-contract.json. These files are derived context, not a new source of truth. Verify hashes before reuse.

Do not reread the whole manifest/textbook or repeat QA on unchanged historical cases. Expand to the full bank/source when retrieval is weak, source references cross topics, or semantic suspicion arises. All independent substantive gates remain required. No candidate cases have been authored.
''')
    with (out/'README.md').open('a') as handle:
        handle.write('\nAuthoring readiness: **'+readiness['status']+'**. Read authoring-readiness.json before writing.\n')
    summary(out,authoringReadiness=readiness['status'],runtime='PASS',families='PASS',sourceTopics=len(topics),plannedRows=len(rows),shortlistCoverage=len(short),averageAnalogs=sum(len(x['analogs']) for x in short)/len(short),sameTopicPatternSafety='PASS',authoringStarted=False,semanticQA='NOT_RUN')
    write(out/'artifact-hashes.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
if __name__=='__main__':entry(main)
