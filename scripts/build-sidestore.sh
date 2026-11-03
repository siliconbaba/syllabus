#!/bin/bash
# Build an unsigned device release, then validate and package it for SideStore.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
[[ $# -eq 1 && "$1" != --* ]] || fail 'Использование: bash scripts/build-sidestore.sh PATH_TO_NEW.ipa'
output="$1"
[[ "$output" == *.ipa ]] || fail 'Имя результата должно оканчиваться на .ipa.'
[[ ! -e "$output" && ! -e "$output.json" ]] || fail 'IPA или отчёт уже существует; выберите новое имя.'
# Validate destinations before creating reports or starting a build.
python3 - "$output" "$BOOK_ROOT" <<'PY_PATH'
from pathlib import Path
import sys
output = Path(sys.argv[1])
for candidate in (output, Path(str(output) + '.json')):
    if candidate.is_symlink() or any(part.endswith('.app') for part in candidate.resolve().parts):
        raise SystemExit('Результат не должен быть symlink или находиться внутри .app.')
PY_PATH
prepare_xcode
python3 "$BOOK_ROOT/scripts/check_content.py"
python3 "$BOOK_ROOT/scripts/build_trainer_catalog.py" --check
# Resource staging performs checksum validation; do not silently ship a partial neural voice.
bash "$BOOK_ROOT/scripts/prepare_silero_models.sh"
/usr/bin/xcodebuild -project "$BOOK_ROOT/InteractiveBook.xcodeproj" -scheme InteractiveBook \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$BOOK_ROOT/build/sidestore-release" CODE_SIGNING_ALLOWED=NO build
mkdir -p "$(dirname "$output")"
report_temp="$(mktemp -t syllabus-ipa-report)"
trap 'rm -f "$report_temp"' EXIT
python3 "$BOOK_ROOT/scripts/package_sidestore.py" \
  --app "$BOOK_ROOT/build/sidestore-release/Build/Products/Release-iphoneos/InteractiveBook.app" \
  --output "$output" > "$report_temp"
python3 - "$report_temp" "$output.json" <<'PY_REPORT'
import shutil, sys
with open(sys.argv[1], 'rb') as source, open(sys.argv[2], 'xb') as target:
    shutil.copyfileobj(source, target)
PY_REPORT
printf '\nIPA: %s\nПроверка и SHA-256: %s.json\nSideStore должен подписать приложение вашим аккаунтом.\n' "$output" "$output"
