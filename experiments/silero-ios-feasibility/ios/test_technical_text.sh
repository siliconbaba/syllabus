#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
mkdir -p artifacts/technical
xcrun swiftc -O ../../InteractiveBook/Audio/SpeechTextProcessor.swift \
 ios/SileroIOSPoC/Sources/SileroTextRules.swift \
 ios/SileroIOSPoC/Sources/TechnicalLexicon.swift \
 ios/SileroIOSPoC/Sources/TechnicalNumbers.swift \
 ios/SileroIOSPoC/Sources/TechnicalSpeechNormalizer.swift \
 ios/tests/main.swift -o artifacts/technical/text-tests
artifacts/technical/text-tests technical-regression-corpus.json
