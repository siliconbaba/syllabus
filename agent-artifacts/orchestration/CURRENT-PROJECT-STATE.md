# Detected state — 2026-10-25

Production: 100 accepted cases, 67 standalone / 33 linked. SHA verified against B2 QA and pipeline contract. Existing application edits predate bootstrap and are untouched.

Frozen production blueprint: v2.2.3, CURRENT.md and master SHA verified. This does NOT freeze cumulative v2.3 reconstruction.

Latest accepted cumulative candidate: hardtail-B2, SHA 625d6b2529c74da2bf51c4ae349f77d44182472fac9263a47f8f33f47b734ced. QA dated 2026-10-18 accepts routing/no-change regression; it inherits B1 content acceptance, not blanket approval of all rows. 72 unresolved; importEligible=false; readyToFreeze=false. B2 is a no-change wrapper over accepted B1.

U-EXP candidate is failed research, not accepted base: 0 changed rows; TC-221/263 unresolved, 4 rejected trials, no independent QA required for empty content. Latest unified-reconstruction-plan-delta-01 supersedes the initial U-EXP+U-SECURITY bundle: U-EXP R3→R5, replacement architecture review next. No high-confidence authoring unit proven. Planning systemic *risk* is not an independent-QA systemic methodology verdict, so no invented HUMAN_DECISION.

TC261 minor HT1-261-M01 remains open for pre-freeze cleanup.

Tools: agent-artifacts/pipeline-tools/{build_batch_context,verify_context,validate_batch,diff_case_sets,build_evidence_index,test_pipeline}.py. Existing context-packs/batch-04 belongs to prior frozen routing; never reuse blindly for current reconstruction. Use a new immutable hash-bound pack. Pipeline README shows tool arguments.

Read sources: contracts (all three runbooks), manifests/CURRENT.md; qa/manifest-v2.3-hardtail-b2/{QA-verdict.json,QA-report.md}; manifests/v2.3-recon-u-exp-candidate/{u-exp-reconstruction-report.md,validation-result.json,pre-freeze-cleanup.md}; test-bank/unified-reconstruction-plan-delta-01/*.md; pipeline-tools/README.md.

BOOTSTRAP_ONLY is an execution hold, not a product decision. No content worker has been launched.
