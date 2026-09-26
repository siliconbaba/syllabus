# English pronunciation in Neural TTS

## Result and scope

Neural now resolves English words through reviewed Russian IT pronunciations or an offline phoneme dictionary, then a bounded pronunciation-aware fallback. Apple TTS, visible HTML, reader UI, Saved, ONNX weights, DSP and 48 kHz sample rate are unchanged. No production dependency was added.

**Remaining acceptance limitation:** no human/subjective listening assessment was performed. All 30 examples were synthesized and validated, and UI playback was activated for the ten required words. These facts do not certify perceived timbre, stress or pronunciation quality. The recordings and Simulator playback list are ready for human review.

## Reproduction and root cause

Before: the unknown-word path replaced digraphs, then transliterated individual characters. It retained silent final e and did not lengthen the preceding vowel. It could not distinguish English spelling from pronunciation.

| Input | Before | Now |
|---|---|---|
| scope | скопе | скоуп |
| spike | спике | спайк |
| pipeline | пайплайн | пайплайн |
| feature | фича | фича |
| framework | фреймворк | фреймворк |
| backend | бэкенд | бэкенд |
| frontend | фронтенд | фронтенд |
| release | релиз | релиз |
| rollback | откат | ролбэк |

Latency is now **латенси**. Throughput retains **трупут**. Queue → **кью**, cache → **кэш**. Rollback previously inherited the Apple dictionary's translation despite a conflicting Neural addition; the Neural-only override now wins.

## Architecture

1. Longest known phrases and IT/acronym rules match before number/symbol handling.
2. Remaining Latin tokens check the case-folded IT/acronym index.
3. camelCase splits into independently processed words, preserving acronym chunks.
4. A static CMUdict subset provides ARPAbet phonemes.
5. An explicit, tested phoneme-to-Cyrillic map produces the Silero speech copy.
6. Truly abbreviation-like unknowns (single letter, or short all-uppercase consonant strings) use letter names; known ordinary words win regardless of uppercase.
7. Other unknown words use a small deterministic grapheme-to-phoneme fallback.

The abbreviation gate precedes the lossy fallback so genuine unknown identifiers such as XQZ are not pronounced as invented words. It follows lexical recognition; uppercase alone never forces spelling. XYZ is an explicit acronym. Known hyphenated phrases win; otherwise each Latin component is processed independently and the existing punctuation pipeline remains intact.

Fallback covers silent final e/CVCe, ai/ay/oa/ee/ea/ie/igh/ou/ow/oo, tion/sion, ph/th/sh/ch/ck/qu/x, soft c/g, doubled consonants and suffixes ing/ed/er/ment/ity/ous. It first reuses known base pronunciations for inflections. This is an approximate fallback, not a complete English phonology or homograph disambiguator. Rare irregular names still need a reviewed lexical entry.

Stress digits from CMUdict remain in the source data, but no new Russian stress marks are injected without listening evidence. Existing Silero stress processing runs unchanged. For transparency, observed outputs include п+айплайн and деплойм+ент; their naturalness needs listening review, and the report does not label it verified.

## Curriculum audit

Source: all topic content in the current index.html, including user-openable details, headings, paragraphs, lists and table rows. Same excluded tag/class list as the reader: script/style, controls, code/pre, hidden content, URL-only link labels. The static scanner does not execute CSS; see its documented scope.

- 16,022 Latin-token occurrences.
- 1,333 unique lowercase ASCII tokens.
- Previous explicit dictionary: 81 unique tokens.
- Current explicit dictionary: 222 unique tokens.
- Another 948 unique tokens covered by the phoneme subset.
- 163 not directly in either dictionary: includes variable letters, mixed identifier pieces, camelCase compounds and rare command names; it is not a count of failed pronunciations.
- Full frequency/coverage/uncovered list: [coverage.json](tools/pronunciation/reports/coverage.json).
- All frequent ordinary words were addressed; remaining repeated single letters are mathematical/variable labels. The most frequent uncovered multi-character label is xx (13), followed by systemctl, keyerror, datetime and other rare terms.

The scanner only writes proposals and reports. It never overwrites approved pronunciations.

## Source, license, size, performance

[CMUdict official source](https://github.com/cmusphinx/cmudict), pinned commit:
74790861f652b15e4ac49015a90074ad62a27690

Original cmudict.dict SHA256:
81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22

License: BSD-2-Clause CMU notice, retained in [CMUdict-LICENSE.txt](InteractiveBook/WebContent/CMUdict-LICENSE.txt) and bundled with the app. Source version, download hash and original size: [SOURCE.json](tools/pronunciation/SOURCE.json).

- Approved subset: 1,039 entries, including curriculum and a small generic word set.
- EnglishPronunciation.swift: 41,755 bytes including the mapper/fallback and comments.
- License: 1,754 bytes.
- The full 3.6 MB source dictionary is downloaded only for maintenance and remains ignored.
- Static Swift tables initialize once. No runtime JSON parsing, network or Python.
- Simulator: 1,731-character batch, five runs approximately 6.16–6.75 ms.
- Same local universal Debug Simulator app: allocated size 289,532 → 289,692 KiB, **+160 KiB**. Current logical file size total: 296,589,666 bytes. This is a local Debug comparison, not an App Store/IPA size estimate.

## Tests and Simulator

- New independently authored pronunciation corpus: **100/100**.
- Previous English corpus: **34/34**.
- Current technical regression corpus: **94/94**.
- Frozen original vocabulary: **105/105**, with the one explicitly requested Neural rollback correction.
- Real-sentence/word fixture text: **30/30**.
- Additional assertions cover ARPAbet mappings, every stored phoneme, unknown-word fallback and Apple normalization separation.
- Full scripts/check.sh: see final status below.
- Separate research text runner: **94/94**.
- Frozen historical audits: 60/60 original text captures and 20 WAVs; 25/25 preprocessing stages; 8/8 original tensor sets and end-to-end waveform comparisons. These audits verify saved original captures and unchanged model hashes; they are not a claim that every old fallback expectation remains valid under the new pronunciation rules.

Intentional updates to the current technical expectations: frobnicate → фрабникэйт; example.com → игзэмпал.кам in the existing direct-normalizer URL fixture; myAPI → май эй пи ай. The frozen historical corpus was not rewritten. Existing punctuation behavior is preserved, e.g. parentheses become pause commas.

[Audio corpus](Tests/pronunciation-audio-corpus.json) contains **20 actual curriculum sentences**, source topic IDs and reviewed speech copies, plus the ten isolated acceptance words. Source text is a verified substring of the extracted topic content. Pipeline is tested as an isolated word because it was not found as an eligible spoken sentence by this extractor.

All 30 passed full unchanged Silero preprocessing → neural runtime → waveform in iPhone 17 Pro Simulator. WAV validation: 48 kHz, mono PCM16, nonempty signal, finite model outputs, exact sample/frame counts. Total duration: 112.9875 seconds. [Compact results and word hashes](tools/pronunciation/reports/simulator.json).

UI playback activated for:
scope, spike, pipeline, feature, framework, release, rollback, deployment, queue, cache, plus the curriculum sentence “Третий рычаг — scope: миграция по волнам.”
AVAudioPlayer reported successful playback; last recorded cache playback duration was 0.4875 s. This is playback verification, **not a claim of listening by ear**.

Local WAVs: build/english-pronunciation/audio/. Open the separate Silero Fixture PoC app in Simulator and tap any row. Reproduction and update commands: [maintenance README](tools/pronunciation/README.md).

## Delivery

Full check.sh: PASS (exit 0): production build, both WebKit viewports, reader/engine state tests, Saved tests and all pronunciation corpora.
Implementation commit: 3be159d3d312394a92bd4aa9d999642e302cae86 — fix: improve English pronunciation in neural TTS.
Push status: ordinary push to origin/main succeeded; remote refs/heads/main was verified at 3be159d3d312394a92bd4aa9d999642e302cae86. This delivery-metadata update is recorded in a subsequent documentation-only commit.
