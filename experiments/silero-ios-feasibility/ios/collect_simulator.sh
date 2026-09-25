#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
SIMULATOR_ID="${1:?Usage: bash ios/collect_simulator.sh SIMULATOR_UDID}"
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" ai.research.SileroIOSPoC data)
mkdir -p artifacts/ios-results reports/ios
cp "$APP_DATA"/Documents/Results/* artifacts/ios-results/
cp artifacts/ios-results/report.json reports/ios/simulator-report.json
if [ -f artifacts/ios-results/playback.json ]; then
  cp artifacts/ios-results/playback.json reports/ios/playback.json
fi
"${PYTHON:-.venv/bin/python}" audit_ios.py
