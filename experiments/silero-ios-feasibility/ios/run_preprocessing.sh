#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
SIMULATOR_ID="${1:?Usage: bash ios/run_preprocessing.sh SIMULATOR_UDID}"
PYTHON="${PYTHON:-.venv/bin/python}"
"$PYTHON" prepare_ios_fixtures.py
"$PYTHON" prepare_ios_preprocessing.py
python3 ios/generate_project.py
xcodebuild -project ios/SileroIOSPoC.xcodeproj -scheme SileroIOSPoC -configuration Debug \
 -destination "platform=iOS Simulator,id=$SIMULATOR_ID" -derivedDataPath ios/build \
 -clonedSourcePackagesDirPath ios/Packages CODE_SIGNING_ALLOWED=NO ONLY_ACTIVE_ARCH=YES build > artifacts/preprocessing/ios-build.log 2>&1
xcrun simctl bootstatus "$SIMULATOR_ID" -b
xcrun simctl install "$SIMULATOR_ID" ios/build/Build/Products/Debug-iphonesimulator/SileroIOSPoC.app
xcrun simctl terminate "$SIMULATOR_ID" ai.research.SileroIOSPoC 2>/dev/null || true
xcrun simctl launch "$SIMULATOR_ID" ai.research.SileroIOSPoC "${@:2}"
if [ "${2:-}" = "--technical" ]; then
 printf 'Wait for text 60/60 and audio 20/20, then Play. Collect:\nbash ios/collect_technical.sh %s\n' "$SIMULATOR_ID"
else
 printf 'Wait for Preprocessing: 25/25; waveform: 8/8, then Play. Collect:\nbash ios/collect_preprocessing.sh %s\n' "$SIMULATOR_ID"
fi
