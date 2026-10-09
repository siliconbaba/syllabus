# Batch 01 production import

Import: PASS. BATCH 01 PRODUCTION INTEGRATION: COMPLETE.

Source: `agent-artifacts/test-bank/batch-01-r2/cases_TC026_TC050_r2.json`.
Production: `InteractiveBook/TrainerContent/cases.json`.

Exactly TC-026…TC-050 appended, semantic content and option ordering identical to the final r2 candidate. No auxiliary authoring/QA fields existed in the candidate, none imported. Existing serialization (UTF-8, two-space indentation, non-ASCII text) retained.

Gold regression PASS: only assessmentEligible true → false for TC-001/002/003/004/017/018; trainingEligible remains true. All other gold fields and all other gold cases unchanged.

50 cases; 35 standalone; 15 linked; 50 training eligible; 35 assessment eligible. Levels J6 / M30 / S10 / H4. Seven complete families, including four new Batch 01 families. Correct-option positions in the batch: A6 / B6 / C6 / D7.

Family positions are not fields of production schema 2.0. New family membership and unique positions were verified against authoritative manifest v2.2 without importing those auxiliary fields. Production families satisfy the actual schema: matching topics, complete siblings and distinct nonempty mutations.

Authoritative TrainerBank.load, mapping coverage, trainer, scoring and schema tests: PASS. Full `bash scripts/check.sh`: PASS (exit 0), iOS Simulator build PASS, WebKit 390×760 / 320×568 / 1280×900 PASS; TTS, saved and pronunciation checks PASS. The previous WebKit timeout did not recur.

Exact pre-import schema-2 snapshot regression PASS: Continue/review survives, old DiagnosticHistory and profile remain immutable, new training has 50 cases, fresh diagnostic selects 35 eligible standalone cases. Existing tests also cover mixed, section/topic filtering and mistakes.

Tests/TrainerTests.swift and Tests/TrainerSchemaTests.swift were updated only for the new bank size, eligibility policy and preserving the original 25-case gold regression scope. Scoring, thresholds, schema, manifests, runtime Swift and UI were not modified.

Production SHA-256: `a16c00b2be4d2d841b401ce15a076320b6a7c33f91a0b7a077b7d80d86800dcc`.
Candidate SHA-256: `61483afc2868ef762cc652ef845e7b4d78a9144d9ec6d9211a6801c59f657d2c`.
Unexpected existing-file changes: 0. Commit/push: not performed.

Evidence: validation-result.json, production-bank-stats.json, check.log, snapshot-regression.log. Replay structural/content checks: `python3 agent-artifacts/work-imports/batch-01/validate_import.py`. SnapshotRegression.swift is a test-only executable compiled with existing TrainerModels, TrainerStore, TrainerScoringMapping and TrainerScoringEngine; it is not part of the production target. cases-before-import.json preserves the exact input snapshot.
