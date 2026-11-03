# Recovery

1. Run `python3 supervisor.py status`, then `validate`.
2. Run `recover`. Existing task ID survives. If result.json exists, validation/submit is retried; incomplete/invalid output fails closed. Missing output leaves task resumable.
3. A held claim survives process exit. Resume in the same actual context using the original token. For another context, first verify the previous worker has stopped, then `recover --confirmed-worker-stopped`; claim again. Old token cannot submit.
4. Do not delete LOCK.json; deleting a locked inode creates a second lock. Kernel releases flock on crash. Stale PID metadata alone does not mean locked.
5. Hash mismatch: preserve failed evidence, restore immutable input from verified source and investigate; do not just rewrite expected hashes. Invalid JSON: restore last verified state/receipt backup; never guess acceptance.
6. STATE commits before views. recover rebuilds CURRENT-TASK and queues after partial view writes. Completed receipt replay is idempotent. run-log is diagnostic and may omit a post-commit event; routingHistory in STATE is authoritative.

Human-gate resolution and routing-review scope changes require a reviewed migration under lock, with explicit decision evidence. They are not bypassed by enable. Resume usage-limited scheduled execution from Scheduled; preserve files and claims.
