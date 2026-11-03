# Focused independent retest — packaging R2

Date:2026-10-26. Verdict: PASS for current-project packaging and closure of PKG-01/PKG-02. This is readiness to retry SideStore, not confirmation of installation or Apple Developer Portal registration.

## Retest

- PKG-01 closed: source-contained .app output is rejected by wrapper before Xcode/report writes. Executed invalid-path fixture remained empty. Packaging report now goes to temporary storage and is published exclusively only after successful packager exit; EXIT trap removes temporary report. Failure path inspected; no second full build necessary for this focused check.
- PKG-02 closed: existing Russian display name preserved through setdefault. Executed OpenStep .strings case with different non-ASCII base name retains Russian display and other keys;7unit tests pass.
- New vendor-signature path is appropriately scoped: main executable must remain unsigned; signed embedded framework permitted only when inspecting source. Removal happens only on staging copies, then staging and extracted archive both must be unsigned.

## Fresh100-case IPA independently examined

Path: agent-artifacts/releases/checkpoint-100-2026-10-26/InteractiveBook-checkpoint-100.ipa
SHA256: cc87f55f75aff19c8c8886eb809626e97253e0df4db6115b41c3e220ac29efa0

CRC, extraction, iPhoneOS arm64, unsigned main/framework, ASCII technical display, unchanged bundle ID: PASS. Current TrainerContent has100cases; bank and main executable exactly match source build bytes. Compared with source, changed existing files are only Info.plist and ORT binary (signature removal); added file is ru.lproj/InfoPlist.strings. Source files remained unchanged during review. See validation.json for exact script hashes and reproducible validate.py.

Source vendor framework has a readable but already unverifiable signature (`code has no resources but signature indicates they must be present`). This is consistent with a build copy lacking signing resources. It does not invalidate the unsigned final artifact, and no claim of valid original vendor signing is made. Final framework passes the unsigned/device check.

No remaining finding blocks retry of this checkpoint IPA. Full whole-project completion,300-case bank, actual signing/installation and runtime device smoke are outside this verdict. No implementation edits, commit/push or production content changes by reviewer.
