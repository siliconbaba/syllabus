#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
prepare_xcode
python3 "$BOOK_ROOT/scripts/sync_runtime_contract.py" --check
python3 "$BOOK_ROOT/scripts/check_content.py"
python3 "$BOOK_ROOT/scripts/build_trainer_catalog.py" --check
mkdir -p "$BOOK_ROOT/build/checks"
/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Trainer/TrainerModels.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerStore.swift" "$BOOK_ROOT/Tests/TrainerTests.swift" -o "$BOOK_ROOT/build/checks/trainer-tests" -framework Combine
"$BOOK_ROOT/build/checks/trainer-tests" "$BOOK_ROOT/InteractiveBook/TrainerContent/cases.json"
/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Trainer/TrainerModels.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerStore.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerScoringMapping.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerScoringEngine.swift" "$BOOK_ROOT/Tests/ScoringFixtures.swift" "$BOOK_ROOT/Tests/ScoringTests.swift" -o "$BOOK_ROOT/build/checks/scoring-tests" -framework Combine
"$BOOK_ROOT/build/checks/scoring-tests" "$BOOK_ROOT/InteractiveBook/TrainerContent/cases.json" "$BOOK_ROOT/build/scoring-fixtures"
/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/Trainer/TrainerModels.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerStore.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerScoringMapping.swift" "$BOOK_ROOT/InteractiveBook/Trainer/TrainerScoringEngine.swift" "$BOOK_ROOT/Tests/TrainerSchemaTests.swift" -o "$BOOK_ROOT/build/checks/trainer-schema-tests" -framework Combine
"$BOOK_ROOT/build/checks/trainer-schema-tests" "$BOOK_ROOT/InteractiveBook/TrainerContent/cases.json"
/usr/bin/xcodebuild -project "$BOOK_ROOT/InteractiveBook.xcodeproj" -scheme InteractiveBook \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath "$BOOK_ROOT/build/simulator" CODE_SIGNING_ALLOWED=NO build
/usr/bin/xcrun swiftc "$BOOK_ROOT/InteractiveBook/BookMessageTrust.swift" "$BOOK_ROOT/InteractiveBook/Saved/SavedExcerptStore.swift" "$BOOK_ROOT/Tests/WebKitSmoke.swift" -o "$BOOK_ROOT/build/checks/webkit-smoke" -framework Cocoa -framework WebKit
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 390 760
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 320 568
"$BOOK_ROOT/build/checks/webkit-smoke" "$BOOK_ROOT/InteractiveBook/WebContent" "$BOOK_ROOT/Tests" 1280 900

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
