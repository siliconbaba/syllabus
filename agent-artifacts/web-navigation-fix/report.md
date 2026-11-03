# Web navigation update

Scenario reported: macOS Safari, 10.3 → 11.4 lands on 10.4. Isolated old WebKit and Chromium did not reproduce the exact failure; direct Safari UI access timed out. Therefore an exact root cause is not claimed.

Navigation now transfers focus from the closing sidebar to the reader with preventScroll, explicitly performs instant target alignment (cancels pending scrolling), then aligns again after the next layout frame before saving history/current topic. No arbitrary pixel offset adjustment, textbook content change or persistence schema change.

Added regression coverage for focused menu links: 10.3 → 11.4 → 10.4 → 1.1, checking target position, focus and persisted topic. Existing WebKit suite PASS at 390×760, 320×568 and 1280×900: navigation, state restoration, saved excerpts, gestures, content/search/diagrams and speech integration. Standalone rebuilt HTML also checked in WebKit; selected topic positioned 16±1 px below reader top. Physical Safari tab reproduction remains unverified; user should retry the new standalone file.

Built with scripts/build_web.py from current canonical WebContent. Content validation PASS: 129 topics, 100 interview questions / 300 answer variants, seven System Design cases. All CSS/JS embedded; no external assets. Native Trainer bank is not embedded by this existing standalone-book builder.

Changed source files: InteractiveBook/WebContent/reader.js and Tests/reader.test.js. Existing unrelated changes preserved. No commit/push.

HTML SHA-256: `bd5f3138e3295fe35a8b179bdb0f6611de140be3d18669268c399d9700b9fbef`
