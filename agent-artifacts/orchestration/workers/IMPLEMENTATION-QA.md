Read CURRENT-TASK.json, STATE.json and the three project contracts under agent-artifacts/contracts. Verify all task/base/candidate/protected-input hashes. All paths in descriptors are relative to syllabus. Work only in the local Work workspace with access to syllabus. Do not use synced sources as writable files. Do not edit STATE.json or derived queues directly; submit a validated receipt through supervisor.py. Do not commit/push.

Claim before work: `python3 supervisor.py claim --owner <actual-fresh-context-id>`. Keep the returned claimToken. Resume only the claimed task. Save result.json last, atomically, under tasks/<taskId>/. Candidate and evidence must be immutable revision files. A limit interruption is not completion. Write progress in that task directory and resume it; never fabricate PASS.

Receipt fields: taskId, worker, claimToken, baseHash, status=COMPLETE, outcome, evidence={project-relative-file:sha256}. Evidence must contain actual reports and raw validations. Supervisor validates identity/hashes/transitions, not semantic truth. See RESULT-CONTRACT.md. Stop on unsupported capability. Structural contract changes use HUMAN_DECISION; routine blocked units reroute with evidence.

IMPLEMENTATION QA

Fresh context independent of CODE. Inspect actual patch and source; verify tests/build/runtime/regression with raw outputs. All four gates required for PASS; issues=[] and remainingUnresolved=0. Failures produce scoped FIX_REQUIRED; do not patch candidate. RELEASE_READY is readiness, never deployment authorization.
