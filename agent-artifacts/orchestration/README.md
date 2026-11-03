USER NORMAL OPERATION

1. Normally do nothing.
2. Check human-decision-needed.md only when notified.
3. If automation pauses because of usage limits, resume the configured automation; state is preserved.

These normal-operation steps apply after native setup and a verified worker run. Bootstrap currently remains BOOTSTRAP_ONLY; no content execution or schedule is active.

Run from this directory: `python3 supervisor.py status`, `validate`, `next`, `recover`. `next` only prepares a descriptor; never executes content. `python3 -m unittest discover -s tests -v` uses temporary dummy files.

Read CURRENT-PROJECT-STATE.md for B2 acceptance vs frozen v2.2.3 and U-EXP failed research. Read SETUP-AUTOPILOT.md, RESULT-CONTRACT.md, STATE-MACHINE.md and RECOVERY.md before activating. Production authoring scope remains controlled by contracts. STATE is authoritative; queues are derived views, not worker-editable authority.

Limitations: no end-to-end scheduled LLM run tested; QA isolation must be supplied by the runner; hash checks detect but cannot prevent unrestricted OS writes. Future approval/cleanup/routing migrations require reviewed decisions. launchd only routes. No production changes, import, commit/push.
