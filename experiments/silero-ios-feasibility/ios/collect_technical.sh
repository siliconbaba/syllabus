#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
SIMULATOR_ID="${1:?Usage: bash ios/collect_technical.sh SIMULATOR_UDID}"
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" ai.research.SileroIOSPoC data)
mkdir -p artifacts/technical/ios-results reports/technical
cp "$APP_DATA"/Documents/TechnicalResults/* artifacts/technical/ios-results/
"${PYTHON:-.venv/bin/python}" audit_technical.py
