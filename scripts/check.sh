#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
prepare_xcode
mkdir -p "$BOOK_ROOT/build/checks"
/usr/bin/xcodebuild -project "$BOOK_ROOT/InteractiveBook.xcodeproj" -scheme InteractiveBook \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath "$BOOK_ROOT/build/simulator" CODE_SIGNING_ALLOWED=NO build
/usr/bin/xcrun swiftc "$BOOK_ROOT/Tests/WebKitSmoke.swift" -o "$BOOK_ROOT/build/checks/webkit-smoke" -framework Cocoa -framework WebKit
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 390 760
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 320 568

/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Audio/SpeechTextProcessor.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechReaderManager.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechEngine.swift" "$BOOK_ROOT/InteractiveBook/Audio/AppleSpeechEngine.swift" "$BOOK_ROOT/Tests/SpeechTests.swift" -o "$BOOK_ROOT/build/checks/speech-tests" -framework AVFoundation -framework Combine
"$BOOK_ROOT/build/checks/speech-tests"

/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Audio/SpeechTextProcessor.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechEngine.swift" "$BOOK_ROOT/InteractiveBook/Audio/AppleSpeechEngine.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechReaderManager.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/SileroTextRules.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalLexicon.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalNumbers.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalSpeechNormalizer.swift" "$BOOK_ROOT/Tests/EngineTests.swift" -o "$BOOK_ROOT/build/checks/engine-tests" -framework AVFoundation -framework Combine
"$BOOK_ROOT/build/checks/engine-tests"
