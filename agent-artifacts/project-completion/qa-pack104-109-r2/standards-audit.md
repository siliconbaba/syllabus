# Narrow standards audit — R2 log distractors

**Conclusion: retaining QA104-109-01 as a major R2 defect is not justified by the exact runbook standard.** My earlier demand for “four strong strategies” and objection that C can be excluded without frequency arithmetic imposed a stronger gate than the contract. That assessment should be superseded by this audit. QA104-109-03 remains valid; the consolidated batch is still FIX REQUIRED on that independent DQ defect. No production/source/manifest files have been edited.

## Applicable standard

`agent-artifacts/contracts/TEST-BANK-RUNBOOK.md:9` requires “strongest action; three plausible competing strategies”. Line 14 requires “Four professional, actionable options A/B/C/D in fixed order; plausible distractors with distinct reasoning failures” and “Exactly one strongest under these facts”; it prohibits caricatures, gratuitous absolutes and a conspicuously nuanced answer. Neither line requires four near-optimal choices, four feasible solutions to every task constraint, or numeric calculation to eliminate every distractor. Line 16 requires a meaningful tradeoff for the Middle case as a whole, not an equally difficult tradeoff in each wrong option. Line 15 independently requires partial quality to reflect the actual decision under the facts.

## R2 application

R2 C is executable and professionally recognizable: use cheap, exact aggregate counts while stopping detail collection. Its error is substituting measurement of frequency for diagnostic evidence. The topic explicitly distinguishes contextual event logs from aggregate metrics and discusses storage cost; the option's stated appeal is therefore source-grounded. C is clearly wrong given the minimum of complete examples, but that clarity establishes the unique answer rather than proving a caricature. It retains the count purpose while sacrificing the diagnostic purpose. Its coherent whole-WHEN supplies supporting evidence of a real strategy; source grounding and the recognizable category confusion establish the additional contextual plausibility.

R2 D is likewise executable: bound storage through short retention while preserving complete recent events. Its error concerns investigation timing/coverage rather than aggregate-versus-detail confusion. The distinct reasoning failures required by line 14 are present. D is particularly attractive at high frequency; it need not remain equally competitive at low frequency to qualify as a plausible distractor. Its lower utility at low frequency must, however, be reflected in DQ.

The whole Middle decision still compares storage against sufficient diagnostic evidence: high-frequency full retention exceeds budget whereas sampling suffices; low-frequency full retention fits whereas sampling loses required evidence. A/B provide that meaningful joint constraint tradeoff. C/D introduce relevant, distinct alternatives for reducing cost without requiring their own near-optimal boundaries in each sibling.

## Consistency check against accepted risk options

Risk C waits until actual failure to avoid reserving resources unnecessarily; risk D prepares immediately to remove dependence on signals. Both are directly excluded by the explicit approved timing policy, yet remain recognized professional strategies that misapply economy or precaution. Rejecting log C merely because its detail loss violates the explicit objective would also reject those accepted risk options by the same argument. There is no contract-grounded reason for that asymmetry. Risk is Junior and logs Middle, but the level rule applies to the central decision and does not create a separate requirement that every Middle distractor be close to optimal.

## Disposition and minimal repair

- Close QA104-109-01 for R2: the old unavailable budget increase and deferred selection have been replaced by actionable, source-grounded strategies with distinct substantive errors.
- Keep QA104-109-03 open: in TC109, B preserves five representative records across the week; D preserves only roughly three at the end. With identical exact counts and both within budget, D=.4 above B=.3 lacks an evidenced benefit. Minimal viable repair is to adjust the rare sibling's partial scores so D does not outrank B, with a concise rationale based on actual retained evidence. No option or context redesign is necessary to repair that issue.
- Proposed blueprint/family reconciliation remains an explicit governance step, not a new content defect. Frequency-only mutation and A/B winners remain intact.
- My design-followup's assertion that the family intrinsically cannot support the runbook's four options was too strong. The first/last-100 proposal is unnecessary for repairing R2 and would make C/D failures less distinct, not more. Do not initiate it on the basis of my earlier “four strong” requirement.

This is a correction to the applicable standard, not a change made to secure a passing outcome. The arithmetic/DQ issue is independent and continues to block acceptance until repaired.
