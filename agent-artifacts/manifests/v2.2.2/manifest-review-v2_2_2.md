# Frozen manifest v2.2.2

CURRENT AUTHORITATIVE MANIFEST = v2.2.2. Batch 03+ must use this directory. v2.2, v2.2.1 and v2.2.2-candidate are historical/audit artifacts only.

Baseline: v2.2.1. Candidate: v2.2.2-candidate. Independent QA: READY TO FREEZE (Blocker 0, Major 0, Minor 0).

Reason: Batch 03 semantic preflight found 6 collisions against production TC-001…075.
Changed rows: TC-076/077/078/079/080/087/088/091/093.
Changed family contracts: F-DR-T01, F-TD-P01.

Independent QA findings: original blockers fixed 6/6; cross-bank near duplicates 0; cross-bank duplicates 0; internal Batch 03 near duplicates 0; internal Batch 03 duplicates 0; source grounded 9/9; level feasible 9/9; unexpected regression 0.

Freeze checks independently confirm 266 other rows and 41 other family contracts unchanged, 275 planned IDs, 181 standalone / 94 linked, 35 pairs / 8 triplets, 11×25 batches. Batch 03: 25 cases, 16 standalone, 9 linked, 4 families; J5/M12/S5/H3. CSV/JSON consistency PASS. Runtime was recompiled from current production sources; all derived rows and 300 engine impulse responses match candidate. Unknown domains/primary/secondary patterns: 0.

No semantic transformation on promotion: root manifestVersion and added freezeProvenance only. All manifest rows, family contracts and runtime coverage are unchanged from candidate. Historical embedded candidate statuses/provenance are retained as evidence; this freeze review, root freezeProvenance and validation-result.json establish the final status.

Candidate and previous baseline retained unchanged. Production bank SHA-256 unchanged: 2540570c2b907ea0e48cb9752e715486126e006a6100bd27e2f9f170d2c99689.

Independent QA: ../../qa/manifest-v2.2.2/QA-report-focused.md and QA-verdict.json. Freeze evidence: ../../work-imports/manifest-v2.2.2-freeze/. Family mutation coherence is covered by independent focused QA; freeze rechecks membership, positions, metadata, member states/boundaries and byte/semantic preservation.

Batch 03 authoring may start: YES. No cases authored in this task. No production/schema/runtime changes. No commit/push. Full application checks were not rerun because this is a manifest-only promotion; compiled runtime validation was run.
