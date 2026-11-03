# Production test-bank pipeline contract

Authoritative routing contract. Tools prepare evidence; they never approve content.

- Target: **300 total = 200 standalone assessment cases + 100 linked training instances**. Planned additions: 275 = 181 standalone + 94 linked; Gold: 25 = 19 + 6. Ordinary diagnostics use standalone, assessment-eligible, unseen evidence only. Linked: trainingEligible=true, assessmentEligible=false. No family-aware scoring / Slice 5 without an explicit decision.
- Current accepted production: TC-001…150, SHA-256 `8f50c50908484ef7a83c2179e51b4688b1c3907acab5d493d4766003ac554bd2`. 150 / 99 standalone / 51 linked. This is a checkpoint, not a permanent expected count.
- Manifest routing: `agent-artifacts/manifests/CURRENT.md`; **Batch 04** uses the frozen projection in `agent-artifacts/manifests/batch-04-frozen/`. **Batch 05** uses `agent-artifacts/manifests/batch-05-frozen/`. For other rows use **v2.2.3**, master `agent-artifacts/manifests/v2.2.3/production_manifest_masterplan_v2_2_3.json`. Candidates are never automatically authoritative.
- Production: `InteractiveBook/TrainerContent/cases.json`; catalog: adjacent `topics.json`; schema: `docs/TRAINER-CONTENT-SCHEMA.md`.
- Runtime truth: `InteractiveBook/Trainer/TrainerModels.swift`, `TrainerScoringMapping.swift`, `TrainerScoringEngine.swift`. Reference copies in `agent-artifacts/runtime-contract/` must match source hashes. No inferred aliases or metadata retagging to fit scoring.
- Source: `InteractiveBook/WebContent/index.html`. Full relevant topics are extracted into context packs; links to other topics may require reading more source.

All paths are relative to syllabus. All production artifacts belong directly under `syllabus/agent-artifacts/`, never /mnt/data. Synced sources are read-only.

## Routing and versioning

`context-packs/batch-XX/`: generated, hash-bound preparation. `test-bank/batch-XX[-rN]/`: authored candidates, skeletons, trace, self-QA. `qa/batch-XX[-rN]/`: independent review and verdict. `work-imports/batch-XX/`: integration evidence. `contracts/approved-case-evidence.json`: accepted content lineage, not a replacement QA verdict. `pipeline-tools/`: deterministic CLIs and tests.

Treat published candidates, QA, manifests and import reports as immutable. Fixes get a new revision directory. Refresh a context pack only before use; preserve a handed-off pack under a new version instead of overwriting. Case revision is per case; never normalize all revisions. Content schema, case revision, manifest version and persistence schema are distinct. A changed manifest requires scoped approval and freeze before import.

Every CLI writes validation-summary.json; PASS covers only checks actually run. NOT_APPLICABLE / NOT_RUN / REQUIRES_INDEPENDENT_QA never mean content approval. Pin inputs by hashes; stale packs/evidence must fail closed. Surface statistics and retrieval scores are screening signals only.

## Steady state

Clean: deterministic context generation → TEST BANK preflight + skeleton/authoring + self-QA → independent TEST QA → WORK import + full regression. Context generation needs no reasoning agent: normally **3 reasoning/execution passes**.
Local defects: + targeted author revision + focused independent QA (normally about 5 passes).
Manifest defect only: surgical manifest hotfix → focused manifest/content QA; do not reopen the masterplan.

Never remove author self-QA, independent QA, semantic duplication, source grounding, level realization, family validation, surface leakage or production regression gates. Start a batch only with explicit authorization; generating a context pack is not authoring authorization. No opportunistic application changes, commit/push, IPA or Slice 5.
