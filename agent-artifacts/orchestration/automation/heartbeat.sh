#!/bin/sh
set -eu
cd '/Users/denis/.codex/.chatgpt-projects/g-p-6ab2d0e595d0819198b17a9dbcd2a4d2/syllabus/agent-artifacts/orchestration'
# heartbeat acquires one lock around validate and next (no nested locks).
exec /opt/homebrew/bin/python3 '/Users/denis/.codex/.chatgpt-projects/g-p-6ab2d0e595d0819198b17a9dbcd2a4d2/syllabus/agent-artifacts/orchestration/supervisor.py' heartbeat >> '/Users/denis/.codex/.chatgpt-projects/g-p-6ab2d0e595d0819198b17a9dbcd2a4d2/syllabus/agent-artifacts/orchestration/automation/heartbeat.log' 2>&1
