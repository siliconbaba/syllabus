# WebKit timeout diagnosis — 26 October2026

Status: environment/rendering precondition failure REPRODUCED; production regression NOT ESTABLISHED. Full suite remains incomplete for this run. No production edits by reviewer.

## Existing evidence

`build-check/full-check-2026-10-26.log` shows successful app build and then only `Loaded test phase0` followed by180s timeout. `project-audit/2026-10-25/check.log` shows successful native-state restoration and phases0–4 at all3widths. Current reader.js and reader.test.js have October12 modification dates; WebKitSmoke.swift has October1 date. They were already present during the25October PASS. Date comparison is supporting context, not proof against every possible runtime regression.

The normal harness prints its first marker from didFinish, not from completion of JS setup/tests. Its evaluateJavaScript error handler catches synchronous evaluation failures, while the asynchronous suite only reports at final success/failure. No lifecycle termination callback or intermediate visibility/frames/JS timer evidence exists. Thus the original180s log alone cannot identify why progress stopped.

## Isolated instrumented reproduction

Artifact-only `WebKitDiagnostic.swift` adds document-start markers, JS error/unhandled-rejection handlers,2s JS heartbeat, rAF counter, native5s heartbeat and process/navigation-failure callbacks. It invokes the real unchanged reader/audio tests and retains all assertions. All runs were coordinated with the primary agent; no concurrent GUI tests were started.

`diagnostic-390-r2.log` records:

- document-start / didFinish phase0;
- before-audio / after-audio / reader-scheduled;
- evaluateJavaScript returned with error=nil;
- document.readyState=complete, visibility=hidden, animation frame count0 throughout;
- native visible=true, occluded=true, active=false, loading=false;
- JS timer heartbeats initially run, then cease; native heartbeat continues until timeout;
- no process-termination/error callback observed.

This demonstrates that page load, synchronous extraction and JS submission succeeded, while no render frame was delivered. Main reader initialization and navigation both require two rAF callbacks. This process cannot exercise those behaviors under the observed visibility state. The initial theory “rAF stalled only” was too narrow: the test's timer-based10s deadline also did not produce a result; timer/microtask scheduling ceased progressing in the hidden view. We do not infer the exact OS-level reason (locked session, display sleep, occlusion policy, focus denial) from these observations.

A second artifact-only harness uses `.floating` window level and `orderFrontRegardless()` in addition to the existing activate/makeKeyAndOrderFront. `diagnostic-floating-390.log` reproduced hidden/occluded/active=false/frame0. Therefore blindly adding stronger activation or longer delays is not an evidenced fix in this environment.

The initial `diagnostic-390.log` has an instrumentation-only unsupported-return-type error; the diagnostic appended a bare postMessage expression. R2 explicitly ends evaluation with `void0`. That initial error is not a production or original-harness finding.

## Precise harness improvement

1. Before running the phase JS, wait for native window `.occlusionState.contains(.visible)` and JavaScript `visibilityState==='visible'`, plus at least2real animation frames after load. Use native deadline15–20s; report every few seconds. A loaded HTML document alone is insufficient.
2. If deadline expires, fail explicitly `ENVIRONMENT_UNAVAILABLE: WebKit hidden/occluded; no animation frames`, with native state and latest JS heartbeat. Do not call this PASS or content FAIL; exit nonzero (e.g.77). The full shell suite should still be marked incomplete.
3. Keep `webViewWebContentProcessDidTerminate`, `didFail`, and `didFailProvisionalNavigation` callbacks with separate errors. Add current phase/step in timeout messages and flush output.
4. Tests should wait for real requested navigation completion (hash plus target geometry/progress), not arbitrary sleep or merely `scrollTop>10000`. That separate existing assertion can be true at an old topic, as noted in historical narrow-screen failures; do not use this environment fault as proof that assertion is fixed.
5. Never replace production rAF with timers, alter production code to make hidden tests pass, or silently skip layout/navigation assertions. If the environment is visible but real frames advance and navigation fails, treat that as a real test/product investigation.

## Reproduction / next check

With an unlocked, visible macOS GUI session and no competing test windows, compile the diagnostic with the same three source files as scripts/check.sh and run at390×760. Require `visibility=visible`, increasing frames and full phase success. Then run original full scripts/check.sh once. If original still hangs under those observed conditions, extend step markers around test waits/clicks; this report does not claim current device/UI usability is proven.

No new generic sleep duration, CoreAnimation/private setting or product code change is justified by the evidence. The source bank/scoring/persistence are unaffected.
