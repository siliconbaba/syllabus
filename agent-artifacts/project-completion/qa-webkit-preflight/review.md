# Independent WebKit preflight review — 27 October2026

Verdict: PASS for bounded environment classification and explicit headless routing. Full WebKit UI regression remains NOT_RUN in the present occluded desktop. Reviewer made no production/test implementation edits.

## Changes checked

Tests/WebKitSmoke.swift now defers phases0/1 until2real rAF callbacks occur. Successful preflight also requires JavaScript visibilityState=visible and native window visible occlusion state. The first version checked only frame count; primary agent fixed this during review. New navigation/provisional failure and WebContent termination delegates make those failures explicit.

scripts/check.sh defaults to full mode, retains set-e, and only skips the GUI block for explicit --headless. Both the skip point and final banner distinguish non-UI PASS from full-suite PASS. Invalid arguments exit nonzero before builds. Bash syntax validation passes. Headless full execution is owned by the primary; this review did not start another build or claim its results.

## Executed evidence

- Actual amended harness compiled successfully with current Xcode; compile-r2.txt is empty because no compiler diagnostics occurred.
- Actual390×760 run: exit2 after21.70s including loading, versus former180s generic timeout.
- Output: Loaded phase0, then ENVIRONMENT_UNAVAILABLE because window occluded, with remaining UI assertions NOT_RUN and phase0.
- No false full/functional PASS printed. Failure is nonzero, so default scripts/check.sh stops and cannot print its final full-suite PASS banner.
- Invalid check.sh mode rejected; source file hashes pinned in runtime-result.json.
- No other GUI harness overlapped this review. GUI lane free after completion.

## Remaining boundaries

1. The positive visible-frame path cannot be exercised while the desktop remains occluded. Code review confirms both visibility guards; a complete functional run in an unlocked visible desktop is still required.
2. Visibility loss after preflight, during a later phase, still uses the global180s fallback. This is a diagnostic limitation, not a false PASS: no assertion was removed or replaced. Phase0/1 reload preflight covers the reproduced startup fault.
3. Window visible but no frames correctly fails rather than being treated as a passed test. The report does not infer all possible OS/display causes.
4. The older reader.test.js navigation predicate `scrollTop>10000` can observe a previous location. It is a separate test robustness issue and remains outside this patch. No current product failure is inferred from it.
5. The --headless mode does not establish UI/navigation/gesture/restoration correctness; any completion summary must keep this gap visible.

No new finding blocks use of the preflight/headless distinction. Do not mark the whole project regression green from this verdict.
