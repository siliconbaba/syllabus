# Runtime scoring contract — TEST BANK / TEST QA

Read-only reference copies. Do not edit the Swift files or hash manifest in this directory manually.
The authoritative sources remain `../../InteractiveBook/Trainer/TrainerScoringMapping.swift`
and `../../InteractiveBook/Trainer/TrainerScoringEngine.swift`.

Stable paths from the shared project root:

- `syllabus/agent-artifacts/runtime-contract/TrainerScoringMapping.swift`
- `syllabus/agent-artifacts/runtime-contract/TrainerScoringEngine.swift`
- `syllabus/agent-artifacts/runtime-contract/runtime-contract-hashes.json`

These are ordinary UTF-8 files in the shared project workspace, readable directly by agents
with access to that workspace. They are not automatically uploaded to separate cloud chats.
For a chat without local project access, attach these files and the hash manifest.

Regenerate directly from source, from the syllabus repository:

```sh
python3 scripts/sync_runtime_contract.py
python3 scripts/sync_runtime_contract.py --check
```

`bash scripts/check.sh` verifies byte identity and hashes to catch stale copies.
Use the mapping source as vocabulary authority; the engine source defines scoring behavior.
`negotiation-batna` maps to `.stakeholders` (Stakeholder maturity), without an engine change.
