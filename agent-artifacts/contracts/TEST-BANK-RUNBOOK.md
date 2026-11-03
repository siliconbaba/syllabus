# TEST BANK runbook

Read PIPELINE-CONTRACT, current schema, then the batch context pack; verify its source hashes. Read only this batch's rows/families, complete relevant source topics and analog dossiers first. Do not read all historical reports when a verified unchanged-case evidence index suffices.

## Preflight before prose

For **each** planned case classify analogs as NO CLOSE ANALOG / ALLOWED REINFORCEMENT / NEAR DUPLICATE / DUPLICATE, recording IDs and the decision-boundary distinction. Review all top-N plus every same-topic and same-primary-pattern production case. Compare planned cases with each other too. Similarity is not a verdict. Weak retrieval, near synonyms, suspicious boundary overlap or cross-topic references require full-bank/source expansion. A different topic/title/domain/level does not prove uniqueness. Stop unresolved near duplicates/duplicates; do not silently rewrite the manifest.

Skeleton first: actor and decision authority; objective; constraints; 1–3 decisive facts; decision boundary; strongest action; three plausible competing strategies; source trace. Confirm the skeleton realizes the manifest before drafting all fields. No new runtime codes without explicit approval.

## Authoring requirements

- Context provides enough information to choose now: feasible actions, trade-off, meaningful uncertainty, relevant costs/limits/ownership. No missing numerical boundary, hidden authority, fabricated source principle or reliance on unstated organizational conventions. Avoid unnecessary details and answer-shaped phrasing.
- Four professional, actionable options A/B/C/D in fixed order; plausible distractors with distinct reasoning failures. Exactly one strongest under **these** facts, not merely the most comprehensive or longest answer. Defend it pairwise against each competitor. No caricatures, gratuitous absolutes or one conspicuously nuanced option.
- decisionQuality is numeric 0…1, exactly one 1.0, matching isBest. Partial quality reflects the actual decision under the given facts, not wording/style or random fractions. It is not a user-facing level prediction.
- Junior: bounded direct application; Middle: resolve a meaningful trade-off and choose a proportionate action; Senior: integrate interacting constraints/uncertainty and secondary consequences; Head: organization/portfolio-wide mechanism, mandate, resource allocation and cross-system consequences. Title, project size and escalation alone do not establish level. Preserve manifest level; raise defects instead of inflating prose.
- Senior realization gate: Senior fails if a strong Middle can solve the situation by simply comparing given constraints, dependencies, resources, thresholds or deadlines. Senior must require a substantive system cause, substantial uncertainty, mechanism redesign, interacting trade-offs or secondary system consequences. For every redesigned Senior, record both `specific Senior reasoning` and `why strong Middle reasoning is insufficient`; complexity of wording or a larger scale is not evidence.
- Runtime metadata re-derivation: after any substantive redesign, derive `scenario → decisive facts → actual decision → strongest reasoning → patterns/runtime metadata` anew. For every pattern, identify the concrete user decision that evidences that pattern. If there is no such evidence, do not assign the pattern; previous metadata is not a reason to retain it.
- Families: preserve declared common situation and constants. Change only the specified logical variable; show how its states change optimal strategy. Preserve family IDs/member order/positions from manifest; production has no familyPosition field. Every sibling must stand alone. Verify siblings together; no incidental authority/cost/scope changes.
- sourceTopicExplanation identifies a concrete substantive principle in the correct topic. Sidecar trace records topic ID, source excerpt/anchor and how the principle supports the decision. Do not confuse a topic title with grounding; distinguish author-created scenario facts from textbook claims.
- Explain every option: explanation, whyTempting, whyNotBest and whenItWouldBeBest. WHEN must make the **whole option** best, not just one sub-action. Best-option strings must also be meaningful. No invented claims in explanations.
- “whatToNotice” is authored as **decisiveFacts + keyInsight**; “thinkingModel” is **mentalModel**. They are concepts, not additional production JSON fields. Explain the transferable boundary, not a slogan. Keep authorRationale and source trace editorial.
- No pre-answer leakage of key/quality/level through title, context, option length, specificity, numbering or jargon. Balanced positions/lengths are diagnostics, not quotas that justify weakening an option. Do not reorder options mechanically.

## Self-QA and handoff

Run validate_batch.py (strict actual loader/runtime, expected manifest metadata, eligibility/families, lengths/positions/duplicates/hashes). Mechanically scan surface cues, then perform independent-of-key self-choice and pairwise analysis. Keep broader established surface analyses (e.g. 78-rule independent QA convention) when comparing prior revisions; the tool's four simple rules do not replace them. Resolve or explicitly justify every flag, including repeated generic questions/shared family text.

Deliver immutable candidate directory: cases JSON, skeleton/source trace, semantic preflight classes, per-case self-QA, family boundary/constant audit, level and surface audit, validation-summary + raw reports + hashes. README lists exact manifest/production hashes. READY FOR INDEPENDENT QA only after all mechanical checks pass and no unresolved semantic defect. Self-QA is never permission to import.
