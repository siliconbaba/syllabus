# Independent packaging review — 2026-10-26

Verdict: FIX REQUIRED for reusable wrapper/localization behavior. No blocker found for the already generated beta75 test IPA itself; this is not approval of a current production release or a phone install.

Reviewed inputs are pinned in reviewed-source-hashes.json. Production source/content and implementation were not edited by this review.

## Findings

### PKG-01 / P2 — report redirection precedes validation and leaves failed artifacts

`scripts/build-sidestore.sh:18–20` redirects stdout to the final `$output.json` before the Python packager validates the source/output. Any packaging failure leaves a zero-byte final report; line8 then rejects a retry using the same filename. More seriously, selecting output within the built `.app` writes the report into the source bundle before Python correctly rejects the output location. The advertised source-preservation guarantee is therefore not true for the wrapper.

Concrete reproduction executes exactly the package/redirection step in a temporary fixture app: source is modified by `bad-location.ipa.json`, Python exits1 with `Output must be outside the source app`, and final report remains0bytes. See reproduce.py and repro-result.json. This does not need to run another Xcode build because the defect occurs after it.

Minimal fix: validate/resolve IPA and report paths before any writes; generate report in temporary location, publish it exclusively after successful packaging; clean temporary report on failure. Reject report symlinks and concurrent overwrites. Add failure→retry and output-inside-source tests at the wrapper/report layer, not just `package()`.

### PKG-02 / P2 — existing Russian display name can be lost

`scripts/package_sidestore.py:93–105` always replaces localized `CFBundleDisplayName` with the non-ASCII base value. A preexisting correct Russian localization is overwritten when the base display name differs (e.g. another language or a different long name). Other localization keys survive, so the current test misses this case.

Reproduction: base `Назва базова`, `ru.lproj` display `Русское локализованное имя`; after `localize_name`, Russian display becomes `Назва базова`. Evidence in repro-result.json. Source app is unchanged because packaging uses a copy; defect is in packaged visible name.

Minimal fix: preserve existing ru display-name key and only populate it from base when absent. Test both OpenStep .strings and binary/XML inputs, already-localized ASCII-base input, and repeat packaging.

## Positive independent verification

- All6 current unit tests pass.
- Actual preserved beta75 .app passes fresh unsigned/device-arm64/platform validation.
- Test IPA CRC and standard Payload/InteractiveBook.app layout pass; no AppleDouble or __MACOSX.
- Comparison to original bundle:31 source content files, only Info.plist differs; bundle ID unchanged. Russian localization is the intended additional resource for this source.
- Source main/framework binaries are unchanged, signing remains unsigned, and wrapper explicitly requests Release + generic iOS + CODE_SIGNING_ALLOWED=NO.
- Python packager rejects existing output, source-contained output, symlinks and simulator main metadata. Existing report handling is the uncovered layer.
- Python syntax/APIs fit Python3.9+ (the surrounding web builder also assumes3.9+); no dependency on hashlib.file_digest remains.

## Limits

Package helper cannot infer Release configuration from every arbitrary .app; Release guarantee is provided by build-sidestore.sh. It is intentionally scoped to this app with its current main executable and directly embedded framework, not a universal extension/watch-app packager. It rejects signed source instead of silently invalidating/removing signatures. No signing account changed, no actual device/Sidestore test, no fresh Release build performed by reviewer. No semantic claim about300-case readiness.
