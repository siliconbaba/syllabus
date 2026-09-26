# Offline English pronunciation maintenance

Only the Neural/Silero speech copy uses this layer. Apple TTS, HTML, weights and DSP are unchanged.

## Audit the current curriculum

From the repository root:

    python3 tools/pronunciation/scan.py

Outputs under ignored build/english-pronunciation/:
- coverage.json: unique lowercase ASCII tokens, counts, explicit/CMUdict/fallback coverage, complete uncovered list.
- blocks.json: topic IDs and source text for review.

The parser follows the exclusions and container walk in audio-reader.js, including table cells. It audits the **union** of all topic content and user-openable details, not just one viewport or selected level. It excludes script/style, UI controls, code/pre, hidden attributes, inline-hidden content, and URL-only link labels. It does not execute CSS; a change to runtime visibility rules should be reflected here. ASCII pieces of mixed identifiers and single-letter variable labels are deliberately reported, not silently removed.

## Propose an updated dictionary subset

Download the static source file, not an online lookup API:

    mkdir -p build/english-pronunciation
    curl --fail --location https://raw.githubusercontent.com/cmusphinx/cmudict/74790861f652b15e4ac49015a90074ad62a27690/cmudict.dict -o build/english-pronunciation/cmudict.dict
    python3 tools/pronunciation/scan.py --cmudict build/english-pronunciation/cmudict.dict

The script verifies the source SHA256 from SOURCE.json. It writes proposed-phonemes.json ONLY. It never changes the approved Swift table or IT pronunciations. Selection: actual curriculum tokens and camelCase parts plus fallback-words.txt; exclude explicit overrides and single letters. Review differences, homographs, and pronunciation variants before transferring approved entries to EnglishPronunciation.dictionary. CMUdict first/base variants are used in the initial subset; this cannot disambiguate an English homograph from sentence context.

IT terms and abbreviations belong in TechnicalLexicon. Its phrase matching runs before token conversion. Rollback intentionally overrides the shared Apple translation only in Neural. Keep research copies of the three pronunciation files identical to production, then run:

    bash scripts/check.sh
    bash experiments/silero-ios-feasibility/ios/test_technical_text.sh

## Corpus audio in Simulator

    bash experiments/silero-ios-feasibility/ios/run_preprocessing.sh SIMULATOR_UDID --pronunciation

Requires the existing verified research artifacts and Python environment documented in the research README. This launches the separate **Silero Fixture PoC** app. Wait for 30 audio examples; tap any row to play. The first 20 are real curriculum sentences with topic provenance, followed by 10 isolated acceptance words. It uses the same unchanged Silero preprocessing, 48 kHz model and DSP. No test UI or dependency is added to production.

Results are in the PoC container Documents/PronunciationResults/: reviewed speech text, stressed text, timings, finite waveform checks and WAVs. Capture them to ignored build/english-pronunciation/audio/. Original TechnicalResults and frozen golden artifacts are not overwritten.

Automated waveform validation does not establish perceived pronunciation quality. The report distinguishes generation/playback verification from human listening.

## Limitations

CMUdict is American English; Cyrillic is an approximation. Explicit Russian IT usage wins. Stress digits are retained in the source table but not injected as Russian stress until listening proves a benefit. Rare out-of-dictionary words use a small deterministic phoneme fallback (CVCe, digraphs, consonant groups and suffixes); English irregular spelling and proper names cannot be universally solved with these rules. New important terms should be reviewed and added to the lexicon.
