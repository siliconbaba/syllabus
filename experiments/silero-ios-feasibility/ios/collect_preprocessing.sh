#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
SIMULATOR_ID="${1:?Usage: bash ios/collect_preprocessing.sh SIMULATOR_UDID}"
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" ai.research.SileroIOSPoC data)
mkdir -p artifacts/preprocessing/ios-results reports/preprocessing
cp "$APP_DATA"/Documents/PreprocessingResults/preprocessing.json artifacts/preprocessing/ios-results/
cp "$APP_DATA"/Documents/Results/*.f32 "$APP_DATA"/Documents/Results/*.wav artifacts/preprocessing/ios-results/
if [ -f "$APP_DATA"/Documents/Results/playback.json ]; then
 cp "$APP_DATA"/Documents/Results/playback.json artifacts/preprocessing/ios-results/
fi
"${PYTHON:-.venv/bin/python}" audit_preprocessing.py
