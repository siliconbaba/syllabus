# Deterministic pipeline tools

Run from the syllabus repository root with Python 3 and full Xcode. Standard library only. No network or production dependencies. Swift preparation reuses scripts/common.sh; the probe compiles actual TrainerModels/TrainerScoringMapping into a temporary directory, then uses the production TrainerBank.load with a temporary copy of the real catalog. It never changes input files.

```bash
python3 agent-artifacts/pipeline-tools/build_evidence_index.py --output agent-artifacts/contracts
python3 agent-artifacts/pipeline-tools/build_batch_context.py \
  --batch 4 \
  --manifest agent-artifacts/manifests/v2.2.3/production_manifest_masterplan_v2_2_3.json \
  --production InteractiveBook/TrainerContent/cases.json \
  --output agent-artifacts/context-packs/batch-04
python3 agent-artifacts/pipeline-tools/verify_context.py \
  --pack agent-artifacts/context-packs/batch-04 \
  --output agent-artifacts/work-imports/pipeline-optimization/pack-verification
```

Generation above is preparation, not Batch 04 authoring. Do not overwrite a handed-off immutable context pack: choose a new versioned output path. Verification output must be outside the pack, so its own checksum does not become stale.

For a future authored candidate (substitute real values):

```bash
python3 agent-artifacts/pipeline-tools/validate_batch.py --batch N \
  --manifest MANIFEST.json --cases CANDIDATE.json --output NEW_VALIDATION_DIR
python3 agent-artifacts/pipeline-tools/diff_case_sets.py \
  --baseline BEFORE.json --revision AFTER.json --allowed-changed TC-NNN,TC-MMM \
  --baseline-manifest BEFORE_MANIFEST.json --revision-manifest AFTER_MANIFEST.json \
  --output NEW_DIFF_DIR
python3 agent-artifacts/pipeline-tools/test_pipeline.py
```

All operation CLIs emit validation-summary.json and exit nonzero on mechanical failure. Structural success is not semantic approval. Native loader/schema/runtime details are in runtime-loader.json; lengths, key positions, duplicate strings and simple surface heuristics in batch-metrics.json. Surface rules use fractional tie credit; they are not comparable with historical first-tie 78-rule scores. Independent broader surface QA remains required.

Diffs distinguish semantic changes, raw UTF-8 object changes and formatting-only changes; ID additions/removals are unexpected unless allowlisted. Root changes also fail. Family sibling diffs expose all changed fields. Logical preservation of prose constants needs judgment; with both manifests, literal contract constants and declared mutation changes are also reported.

The evidence builder recognizes the explicitly accepted 100-case baseline only. Following future accepted imports, extend its approval registry/lineage deliberately; changing a hash is not approval. Null local QA provenance for Gold and conditional QA for Batch 01 are retained honestly. Canonical content hashes do not cover formatting; rawObjectSha256 does. Matching a content hash does not exempt new cross-case relationships from duplication QA.

Context retrieval: weighted topic/domain/primary/secondary/level match + inverse-frequency lexical overlap from scenario/decision boundary/decisive facts. Stable ID tie-break. Top 6 plus ALL same-topic and same-primary cases; no confidence claim or automatic duplicate verdict. Read full per-case analog dossiers and complete source topics just in time; avoid reading aggregate and per-item duplicates. Expand to the full bank whenever necessary.
