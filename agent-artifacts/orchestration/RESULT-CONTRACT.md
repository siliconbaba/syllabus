# Result protocol

The control plane owns STATE.json and derives CURRENT-TASK/queues from it. Workers must not mutate control files. tasks/<UUID>/result.json is the commit marker written last, atomically. Evidence files and candidate are immutable after handoff.

Common fields: taskId, worker, claimToken (from claim), baseHash, status: COMPLETE, outcome, evidence: {syllabus-relative-path: SHA256}. Every evidence path must exist inside project and match bytes. Required reports are listed in worker contracts; the CLI checks envelope and hashes, not scholarly quality. Receipts are not cryptographically authenticated; a trusted local runner must enforce roles and read-only QA mounts where possible. Hash checking detects content mutation; it does not prevent arbitrary OS writes by an unrestricted agent.

Author outcome READY_FOR_QA adds candidate (inside its tasks/UUID directory), candidateHash, changedUnits (nonempty), selfQA: PASS. ROUTING_OR_METHOD_REVIEW adds consecutiveZeroYield >=5, reroutedUnits; requires evidence of attempts. Persist detailed routing/failed-unit records with evidence. This enters a routing review hold without asking a product question. A supervisor must inspect that evidence and perform an explicit reviewed state migration to a new non-exhausted scope; no automatic infinite retry.

QA outcome PASS or FIX_REQUIRED adds candidateHash, gates, issues, remainingUnresolved, remainingUnresolvedIDs and nextScope (next eligible units from routing evidence when unresolved remain). PASS requires all gates PASS and no issues; QA owner differs from author. Reports must reconcile remainingUnresolvedIDs as well as count. CASE_QA allCasesComplete requires full target evidence. Human outcome adds humanDecision: category matching HUMAN constant and Question / Why automation cannot choose / Option A / Option B / Recommended.

`submit --result <absolute path>` validates before saving STATE. Replay of identical accepted receipt is a no-op; a changed receipt for the same task is rejected. Never delete historical receipts/evidence. Queue views recover from STATE after a crash. Record changed code as an immutable patch; actual application integration needs authorized scope and QA evidence.

Future structural approvals, cleanup closure and routing-review resolutions currently require an explicit reviewed state migration under the supervisor lock. There is no arbitrary CLI transition command or automatic freeze bypass. This is an intentional integration boundary; do not edit state while an execution is active.
