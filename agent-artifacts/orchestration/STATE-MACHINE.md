# State machine

AUTHORING_READY / ARCHITECTURE_READY / FIX_READY → TEST_BANK → AWAITING_QA.
AWAITING_QA PASS → AUTHORING_READY; FIX_REQUIRED → FIX_READY.
Five zero-yield attempts → ARCHITECTURE_READY + ROUTING_REVIEW hold.
Zero unresolved after QA → MANIFEST_FREEZE_READY; explicit scoped freeze approval and closed cleanup → CASE_AUTHORING.
CASE_AUTHORING → CASE_QA → CASE_AUTHORING / FIX_READY; complete case acceptance → IMPLEMENTATION_READY.
IMPLEMENTATION_READY / CODE → IMPLEMENTATION_QA → RELEASE_READY / CODE.
Structural contract or independent systemic-methodology defect → HUMAN_DECISION (no task dispatch).

QA never writes candidate; mutation invalidates its handoff hash. Frozen production v2.2.3 is recorded separately from unfinished cumulative reconstruction. Bootstrap is ARCHITECTURE_READY + BOOTSTRAP_ONLY, not HUMAN_DECISION and not an active content run.

No automatic production import, deployment, commit or push. Readiness is not permission. Current CLI supports the above paths but future freeze/implementation are fixture-tested routing only, not production readiness certification.
