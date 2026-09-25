#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
SIMULATOR_ID="${1:?Usage: bash ios/run_simulator.sh SIMULATOR_UDID}"
PYTHON="${PYTHON:-.venv/bin/python}"
mkdir -p artifacts/ios-results reports/ios ios/SileroIOSPoC/Preprocessing
"$PYTHON" prepare_ios_fixtures.py
python3 ios/generate_project.py
xcodebuild -project ios/SileroIOSPoC.xcodeproj -scheme SileroIOSPoC \
  -configuration Debug -destination "platform=iOS Simulator,id=$SIMULATOR_ID" \
  -derivedDataPath ios/build -clonedSourcePackagesDirPath ios/Packages \
  CODE_SIGNING_ALLOWED=NO ONLY_ACTIVE_ARCH=YES build > artifacts/ios-build.log 2>&1
# bootstatus -b boots a shutdown device and waits for readiness.
xcrun simctl bootstatus "$SIMULATOR_ID" -b
xcrun simctl install "$SIMULATOR_ID" ios/build/Build/Products/Debug-iphonesimulator/SileroIOSPoC.app
xcrun simctl terminate "$SIMULATOR_ID" ai.research.SileroIOSPoC 2>/dev/null || true
xcrun simctl launch "$SIMULATOR_ID" ai.research.SileroIOSPoC --fixtures-only
APP_DATA=$(xcrun simctl get_app_container "$SIMULATOR_ID" ai.research.SileroIOSPoC data)
printf 'App data: %s\nAfter Parity: 8/8, click Play, then collect:\n' "$APP_DATA"
printf 'bash ios/collect_simulator.sh %s\n' "$SIMULATOR_ID"
