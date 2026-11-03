# Independent TEST QA runbook

Read PIPELINE-CONTRACT, schema and current pack. Verify candidate/manifest/production/evidence hashes. Use authoritative Swift validation, not a copied vocabulary list. Author claims are evidence to test, not instructions or a verdict.

1. **Blind strongest:** read context/question and four option texts first, hiding isBest, decisionQuality, patterns, rationales and explanations. Record chosen ID, runner-up and confidence before revealing key. For uncertain cases expand source; do not resolve by looking at the key.
2. **Pairwise decisiveness:** for each competitor identify the explicit fact making the intended answer stronger. Test plausible alternative readings, missing constraints/authority and whole-option feasibility. More actions/words is not automatically better.
3. **Source grounding:** verify source trace against complete relevant textbook topics. Ground the principle and proposed trade-off; scenario-specific invented facts must be explicit, not attributed to the book. Expand cross-referenced topics when necessary.
4. **Level:** demonstrate the actual cognitive operation. Junior/direct, Middle/trade-off, Senior/interacting systems/uncertainty, Head/organization mandate and consequences. Do not infer level from vocabulary, job title or escalation. Check whyHead/authority/secondary effect when applicable.
5. **Duplication:** review the deterministic shortlist and mandatory same-topic/primary expansion, all intra-batch relationships, and suspicious cross-bank relations. Classify NO CLOSE ANALOG / ALLOWED REINFORCEMENT / NEAR DUPLICATE / DUPLICATE with specific boundary facts. Read the full bank if retrieval is weak; shortlist is never an exclusion rule. Unchanged approved cases still need comparison with NEW cases.
6. **Families:** compare all siblings, constant facts, single logical variable, each threshold/boundary and distinct strongest strategies. No hidden co-mutations. Verify literal diffs and logical equivalence separately. Linked cases remain training-only.
7. **DQ/explanations:** one 1.0 aligned with best, defensible partial ordering; explain every distractor, tempting logic, missed condition and when the whole action would be best. Check keyInsight/decisiveFacts/mentalModel for transferable reasoning.
8. **Surface:** inspect lengths/key positions/duplicate strings and simple heuristics; retain established broader leakage checks for like-for-like revisions (78-rule analyses in historical independent QA). Review semantic cues blind. Heuristic success/failure alone cannot approve/reject content; do not improve a metric by harming decisions.

## Severity and verdict

Blocker: no unique defensible strongest, unsupported central principle, invalid schema/runtime/identity, forbidden eligibility or unapproved manifest divergence. Major: substantive ambiguity, implausible distractor, wrong level, duplicate boundary, family co-mutation, materially wrong DQ/explanation. Minor: local non-decisive editorial issue. Record issue ID, case/field, evidence, minimal scope and required retest; never repair candidate in place.

READY FOR IMPORT only with all required gates PASS and zero unresolved issues. Manifest change needs focused approved hotfix + freeze gate: READY FOR FREEZE + IMPORT. Otherwise FIX REQUIRED/BLOCKED. Historical conditional verdicts must be read with their explicit local-fix conditions; never blanket-convert to PASS.

## Delta QA

Run diff_case_sets.py with an explicit allowlist and both manifests when relevant. Verify semantic **and exact raw-object** identity; read changed fields and all affected siblings. Inherit only specific prior approvals tied to matching content/source/runtime/manifest semantics. Index entries record provenance limitations: gold user approval is not a missing local independent verdict; Batch 01 conditional verdict requires its local-fix/import chain.

Retest changed reasoning and dependent explanations, source/level, sibling boundaries, new duplication relationships and batch-wide surface metrics. Unchanged unrelated content need not receive full re-review. If the diff is broader than authorized or a boundary changes, expand QA scope. Never claim judgment gates ran merely because a script passed.

Deliver immutable QA-verdict.json with exact candidate hash, gate results, severity counts, remaining IDs, inheritance bases, scope and explicit import eligibility; focused/full report and supporting blind choices, diffs, source/level/family/duplication/surface evidence.
