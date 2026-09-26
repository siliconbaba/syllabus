#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
prepare_xcode
mkdir -p "$BOOK_ROOT/build/checks"
/usr/bin/xcodebuild -project "$BOOK_ROOT/InteractiveBook.xcodeproj" -scheme InteractiveBook \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath "$BOOK_ROOT/build/simulator" CODE_SIGNING_ALLOWED=NO build
/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/BookMessageTrust.swift" "$BOOK_ROOT/InteractiveBook/Saved/SavedExcerptStore.swift" "$BOOK_ROOT/Tests/WebKitSmoke.swift" -o "$BOOK_ROOT/build/checks/webkit-smoke" -framework Cocoa -framework WebKit
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 390 760
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 320 568

/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Audio/SpeechTextProcessor.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechReaderManager.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechEngine.swift" "$BOOK_ROOT/InteractiveBook/Audio/AppleSpeechEngine.swift" "$BOOK_ROOT/Tests/SpeechTests.swift" -o "$BOOK_ROOT/build/checks/speech-tests" -framework AVFoundation -framework Combine
"$BOOK_ROOT/build/checks/speech-tests"

/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Audio/SpeechTextProcessor.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechEngine.swift" "$BOOK_ROOT/InteractiveBook/Audio/AppleSpeechEngine.swift" "$BOOK_ROOT/InteractiveBook/Audio/SpeechReaderManager.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/SileroTextRules.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalLexicon.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/EnglishPronunciation.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalNumbers.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalSpeechNormalizer.swift" "$BOOK_ROOT/Tests/EngineTests.swift" -o "$BOOK_ROOT/build/checks/engine-tests" -framework AVFoundation -framework Combine
"$BOOK_ROOT/build/checks/engine-tests"

/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Saved/SavedExcerptStore.swift" "$BOOK_ROOT/Tests/SavedTests.swift" -o "$BOOK_ROOT/build/checks/saved-tests" -framework Combine
"$BOOK_ROOT/build/checks/saved-tests"

/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Audio/SpeechTextProcessor.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/SileroTextRules.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalLexicon.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/EnglishPronunciation.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalNumbers.swift" "$BOOK_ROOT/InteractiveBook/Audio/Silero/TechnicalSpeechNormalizer.swift" "$BOOK_ROOT/Tests/EnglishTests.swift" -o "$BOOK_ROOT/build/checks/english-tests"
"$BOOK_ROOT/build/checks/english-tests" "$BOOK_ROOT/Tests/english-corpus.json"

"$BOOK_ROOT/build/checks/english-tests" "$BOOK_ROOT/experiments/silero-ios-feasibility/technical-regression-corpus.json"

"$BOOK_ROOT/build/checks/english-tests" "$BOOK_ROOT/Tests/pronunciation-corpus.json"
python3 "$BOOK_ROOT/tools/pronunciation/scan.py"

"$BOOK_ROOT/build/checks/english-tests" "$BOOK_ROOT/Tests/original-technical-terms.json"
"$BOOK_ROOT/build/checks/english-tests" "$BOOK_ROOT/Tests/pronunciation-audio-corpus.json"
