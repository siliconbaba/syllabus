# Silero v5_5_ru: raw Russian text → iOS preprocessing → waveform

Дата: 2026-09-25. **Этап успешен для проверенного plain-text baseline.**

В отдельном SileroIOSPoC внутри iOS Simulator обычная русская строка обрабатывается Swift-кодом и двумя auxiliary ONNX models. Получены точные строки, token/type/speaker IDs, shapes, durs_rate и pitch_coefs. После полного stage parity запущен существующий synthesizer: все 8 исходных примеров прошли waveform parity.

**25/25 preprocessing cases, 8/8 end-to-end cases.** Все 8 новых waveform побитово совпали с предыдущим iOS fixture-only прогоном. Это особенно сильная проверка: замена заранее подготовленных tensors на результаты Swift preprocessing не добавила ошибки к численному synthesizer.

Исходная модель SHA256: `50081637b602126ee06cb3bc8a744d25651d2da149ee8864b9a379bfdd934437`. Оригинальные 8 raw texts, prepared NPZ и waveform references не перезаписывались. Новые stage captures — отдельный `artifacts/preprocessing/golden.json`, создание повторно разрешено только при совпадающих bytes.

## Реализованный pipeline и границы

```text
raw Russian String
  → Swift: strip/newline handling, lowercase, whitelist, punctuation/hyphens/spaces
  → Swift: homograph dictionary, tags, BasicTokenizer/WordPiece, padded IDs/boundaries
  → ONNX: original homograph BERT + classifier
  → Swift: sigmoid/round, dictionary variant, reconstruction
  → Swift: Accentor tokenization, exceptions, UTF-8 ngram indices/offsets
  → ONNX: original embedding_bag(mean), stress classifier, ё classifier
  → Swift: confidence/user-stress/ё/exception rules, reconstruction
  → Swift: exact character mapping, SOS |, EOS ~
  → Swift: classification of ORIGINAL raw string, type_ids with original length rules
  → prepared tensors + xenia=4
  → existing 5 ONNX graphs + Swift orchestration + KissFFT DSP
  → float32 waveform; WAV only after parity
```

Файлы разделены логически: `SileroTextRules.swift` (Normalizer, Tokenizer, QuestionClassifier), `SileroAuxiliary.swift` (HomographProcessor, StressProcessor), `SileroPreprocessor.swift` (composition и отдельный test harness). API `prepare(text,speaker:)` не принимает golden/expected results. Preprocessor получает только исходные словари/веса и raw string. Golden используется исключительно внешним harness после вычисления результата. Нет lookup ответа по целой фразе, подмены prepared tensors или Python внутри приложения.

Speaker mapping: aidar=0, baya=1, kseniya=2, eugene=3, xenia=4. Проверенный voice baseline — xenia, 48000 Hz, batch1, float32, CPU; symb_durs={}, focus_mask=None, pitch coefficients=1. Другие голоса здесь не benchmark/test coverage.

## Важные детали исходного поведения

- Сначала strip и обработка newline: после punctuation newline становится пробелом, иначе `. `. Далее исходная whitelist. NBSP/tab могут исчезать **до** свёртки пробелов и склеивать слова. Это не исправлялось.
- Латиница и цифры удаляются, а не произносятся. Исключений для API/HTTP/SLA нет. NFD `Е` + combining diaeresis после whitelist становится `е`, не `ё`.
- Homograph tags `[HOMO]`/`[/HOMO]`, BasicTokenizer punctuation, greedy WordPiece, max_input_chars_per_word=100, CLS/SEP, padding=0 и boundaries перенесены. Generic Chinese/control-token branches не нужны на входе после русской whitelist: они недостижимы в этом pipeline. WordPiece IDs сравниваются до neural inference.
- Homograph model использует тот же исходный padding без дополнительно придуманного attention mask. Штатное `unpack_q_model()` выполняется на Python перед экспортом: восстановление embeddings — часть оригинального Silero, не новая квантизация/изменение весов.
- Accentor получает в model batch также пустые clean tokens от разделителей; prediction_mask используется для восстановления строки. Нельзя просто удалять пустые слова.
- **TorchScript string ngrams используют UTF-8 byte offsets.** Swift повторяет порядок byte slicing, пропуская невалидные UTF-8 slices, которых нет в строковом словаре. Python-side проверка для всех captured words дала bit-exact embeddings между исходным string module и extracted indices/offsets + embedding_bag. Unicode-character-order ngrams дали бы другой порядок float summation.
- Сохранены exception dictionary, одногласные слова, `-то`, пользовательский `+`, заданная `ё`, confidence >0.5 и согласование ё со stress. Никаких упрощённых ударений по эвристике.
- Question classifier использует **raw text**, а не normalized/stressed text. WH words/fillers, tag regex, alternative `или`, punctuation и split нескольких предложений перенесены. type_ids заполняются по длинам raw characters и затем обрезаются/дополняются первым type до stressed sequence length — исходная странность сохранена.
- Swift code-point indexing используется там, где Python индексирует str; для ngrams отдельно UTF-8. Foundation regex применяется к заданным исходным правилам. Доказанная exact parity ограничена проверенным corpus, это не исчерпывающий тест всех Unicode/regex различий Python и Foundation.

Исходные словари: 126523 ngrams, 16969 exceptions, 1924 homographs, 83830 WordPiece vocabulary entries. Они извлечены из загруженного оригинального package без замены. В corpus 164 processing-enabled word occurrences; только 4 попадают в exception dictionary, так что проверка не сводится к словарным исключениям.

## Auxiliary graphs и runtime

Официальный ORT iOS 1.24.2 через существующий SPM, CPU EP, четыре intra-op потока. Два graph реально загружены и исполнены в Simulator; никаких custom ops/CoreML EP/Python/TorchScript runtime в приложении. Deployment target iOS16, test Simulator iPhone17Pro/iOS26.3.1 на Apple Silicon; Xcode26.2.

| Graph | Размер bytes | SHA256 | Inputs → output |
|---|---:|---|---|
| accent | 8248029 | `7667f328055d495ef48ce4bf7c9596e86bb74d5c537dd4a19ed826e1e72fb230` | int64 indices[N], offsets[W] → float32 [W,17] (stress10 + ё7) |
| homograph | 117110437 | `cdcc460acb3925ff0946734c41f282035bea0ffa7b0d455d9b718a75794af826` | int64 input_ids[B,L], homo_start_ids[B], homo_end_ids[B] → float32 [B,1] |

Accent numeric wrapper сохраняет embedding_bag mean и исходные classifiers; concatenation двух outputs нужна только для интерфейса одновыходного bridge. Homograph экспортирован напрямую из исходного tensor-only TorchScript module. Экспорт opset18, legacy exporter; переменные token/batch/word dimensions. ONNX checker и рекурсивная проверка доменов, включая Loop subgraphs, подтвердили стандартные ONNX operations.

Auxiliary models не интегрированы в production. Словари/веса/fixtures в ignored resource folder `ios/SileroIOSPoC/Preprocessing`; hashes всех четырёх файлов — `reports/preprocessing/resources-manifest.json`.

### Numerical parity auxiliary models

Maxima по 25 cases (BERT только в случаях с омографами):

| Runtime vs original PyTorch | Model | max abs | RMSE | relative L2 |
|---|---|---:|---:|---:|
| Mac ORT | accent | 0.078125 | 0.0310821806 | 4.3065671e-07 |
| Mac ORT | homograph | 4.76837158e-06 | 3.81469727e-06 | 1.63016505e-06 |
| iOS ORT | accent | 0.078125 | 0.0310821806 | 4.3065671e-07 |
| iOS ORT | homograph | 3.81469727e-06 | 3.81469727e-06 | 1.77836187e-06 |

У accent logits max abs 0.078125 выглядит большим без масштаба сигнала: относительная ошибка около 4e-7. Это сырые logits, включая пустые/необрабатываемые tokens, не waveform и не вероятности. На Python→ORT совпали stress/ё argmax и homograph decisions. На iOS совпала полная реконструкция строк и tensors; независимый audit ограничивает auxiliary relative L2 <1e-5. Математика и weights не подгонялись под ответы.

## Stage parity и расширенный corpus

Для всех 25 cases точны **22 проверки**: normalized, tags, WordPiece tokens, padded IDs, start/end boundaries, homograph-resolved string, stress raw/clean/mask, ngram indices/offsets, stressed/final text, character IDs, SOS/EOS sequence, classification, type_ids, speaker IDs, durs_rate, pitch_coefs и shapes (группы входят в 22 JSON keys).

8 исходных cases: statement, question, homograph, yo, number, technical, abbreviations, long. Они дополнительно сверены с прежними stage2 NPZ, а не только новыми captures.

17 новых cases в `preprocessing-corpus.json`:

| Case | Classification | Stage parity |
|---|---|---|
| extra_homo_context | `st` | exact |
| extra_yo_restore | `st` | exact |
| extra_stress_words | `st` | exact |
| extra_wh_question | `wh_q` | exact |
| extra_general_question | `general_q` | exact |
| extra_alternative_question | `alternative_q` | exact |
| extra_tag_question | `tag_q` | exact |
| extra_exclamation | `exclam` | exact |
| extra_multi | `st|wh_q|exclam` | exact |
| extra_punctuation | `st|general_q|general_q|st` | exact |
| extra_hyphens | `st` | exact |
| extra_quotes | `st` | exact |
| extra_technical_ru | `st` | exact |
| extra_user_stress | `st` | exact |
| extra_unicode | `st|wh_q` | exact |
| extra_known_latin | `st` | exact |
| extra_known_digits | `st` | exact |

Покрыты все шесть типов st/wh_q/general_q/alternative_q/tag_q/exclam, составной st|wh_q|exclam, омографы, ё restoration, разные ударения, дефисы, кавычки, punctuation, переносы/Unicode и technical Russian. Расхождений в выбранном расширенном corpus нет.

Known limitations оригинала подтверждены: `API вернул HTTP 500, а SLA нарушен.` → `вернул , а нарушен.`; `В 2026 году исправили 25 ошибок.` → `в году исправили ошибок.` Эти cases документируют удаление, а не корректное чтение технического текста.

Семантически ошибочное произношение сохранено: `На двери висит замок, а на горе стоит замок.` → `... зам+ок ... зам+ок.` — второй замок также выбран как запор. Swift повторяет оригинальное решение; исправление ухудшило бы parity.

## End-to-end waveform

Только после 25/25 stage checks создан synthesizer. В runCase передаются Swift-produced tensors; fixture input tensors в этом режиме не загружаются. Fixtures содержат только ожидаемые durations/spectral/waveform для последующего сравнения. Нет hardcoded durations: duration graph и host rules исполняются заново.

Все integer durations, intermediate shapes и lengths совпали. Все 8 outputs **bit-exact к предыдущему iOS fixture-only результату**. Ни normalization/gain alignment, ни сдвиг waveform не применялись.

Сравнение с исходным Python `apply_tts` golden:

| Case | Samples | max abs | RMSE | relative L2 | SNR dB |
|---|---:|---:|---:|---:|---:|
| statement | 139200 | 0.000116411597 | 3.7737979e-06 | 3.20795666e-05 | 89.875 |
| question | 75000 | 2.90870667e-05 | 2.17050337e-06 | 1.75348368e-05 | 95.122 |
| homograph | 229800 | 0.00034369342 | 6.09609352e-06 | 5.22838329e-05 | 85.633 |
| yo | 135000 | 5.42551279e-05 | 3.427782e-06 | 2.88789496e-05 | 90.788 |
| number | 87600 | 0.000326395035 | 1.55179696e-05 | 0.000120605425 | 78.373 |
| technical | 145800 | 0.00213739276 | 3.62004961e-05 | 0.00027962873 | 71.068 |
| abbreviations | 57600 | 0.000172160566 | 1.1470184e-05 | 9.91446989e-05 | 80.075 |
| long | 630600 | 0.00010679476 | 2.76277577e-06 | 2.74935059e-05 | 91.215 |

Итого относительно оригинального Silero SNR 71.07–95.12 dB, worst relative L2 0.000279629; это прежний numerical baseline. Относительно Mac ONNX+DSP SNR 79.05–100.07 dB. Не следует путать эти два reference.

A/B WAV PCM16 mono48k сохранены отдельно: `artifacts/preprocessing/ios-results/ab/<id>-python.wav` и `<id>-ios.wav`; float32 результаты — рядом в `.f32`. Метрики считаются до PCM conversion. В Simulator нажата Play homograph после успеха: AVAudioPlayer play=true, isPlaying=true, duration=4.7875 s. Это подтверждение playback, не субъективный listening test отсутствия слышимых отличий.

## Воспроизведение

Из `experiments/silero-ios-feasibility/`, существующее `.venv` и artifacts предыдущих этапов:

```sh
# Только первый раз / для независимого восстановления auxiliary artifacts:
.venv/bin/python preprocessing_probe.py > artifacts/preprocessing/probe.log 2>&1
.venv/bin/python export_preprocessing.py > artifacts/preprocessing/export.log 2>&1
.venv/bin/python capture_preprocessing.py > artifacts/preprocessing/capture.log 2>&1
# Capture откажется заменить несовпадающий golden: разбирать различие, не удалять эталон.

# Подготовка resources, сборка, установка, запуск:
bash ios/run_preprocessing.sh "$SIMULATOR_ID"
# Дождаться Preprocessing: 25/25; waveform: 8/8, нажать Play; затем:
bash ios/collect_preprocessing.sh "$SIMULATOR_ID"
```

Для чистого первого запуска создать `mkdir -p artifacts/preprocessing reports/preprocessing` до перенаправления логов. Модель и stage2 artifacts восстанавливаются по существующему README; новые exports не затрагивают пять synthesis ONNX. Для другого Simulator подставить его UUID. Для ручного Run открыть `ios/SileroIOSPoC.xcodeproj`: default запускает preprocessing experiment. Старый numerical-only путь сохранён: launch argument `--fixtures-only` (его использует `ios/run_simulator.sh`).

`prepare_ios_preprocessing.py` проверяет SHA256/standard ops и копирует resources. `audit_preprocessing.py` независимо сравнивает сохранённые actual Swift stages с Python captures, исходные 8 NPZ, waveform metrics и старые iOS outputs. Полные actual stages находятся в ignored `artifacts/preprocessing/ios-results/preprocessing.json`; компактный отчёт и independent-audit.json — в reports/preprocessing.

## Изменения и ограничения

Изменён только исследовательский project: добавлены Swift source files и folder resource; сохранён прежний bridge, ORT dependency, FFT и engine flow. FixtureHarness получил необязательные подготовленные tensors и использует именно их sequence для mask. App теперь умеет raw preprocessing mode и прежний fixtures-only mode. Production dependencies, SpeechReaderManager, SpeechTextProcessor, SpeechControls, BookView, Apple TTS, HTML, background/Now Playing не менялись. Существовавшие до исследования две DEVELOPMENT_TEAM строки в production project оставлены как были. GitHub не обновлялся.

Этот baseline ещё не поддерживает полный SSML/focus, nondefault stress/ё options, symbol duration overrides, random voice, иные sample rates. `*`/`^` явно отклоняются текущим normalizer как вне тестируемого режима; это не заявленная parity этих управляющих символов. Generic пустые/невалидные строки, чрезмерно длинные BERT contexts, все Unicode edge cases и все словари не исчерпаны 25 примерами. UI выбора голосов/читательские очереди не добавлялись. Physical iPhone не тестировался, Simulator timings не дают прогноза его скорости/памяти.

## Ответ на главный вопрос и следующий шаг

**Да, в проверенном plain-text режиме Silero работает end-to-end непосредственно в iOS runtime без Python.** Normalization, homograph resolution, stress/ё, tokenizer и question/type handling дали exact parity на выбранных 25 строках; исходные 8 дали точные tensors и прежний waveform baseline.

Считать это доказательством переносимости проверенной архитектуры можно. Считать гарантией идентичности на любой русской строке, всех options и всех устройствах — пока нельзя. Субъективное отсутствие слышимых отличий требует A/B-прослушивания; численно дополнительных отличий от предыдущего iOS baseline нет.

Рекомендуемый следующий отдельный шаг — **physical-device benchmark того же PoC**: проверить parity, cold/warm latency, peak memory и прослушивание на реальном iPhone. До production engine integration дополнительно нужен больший regression corpus. Technical text normalization для API/HTTP/SLA/чисел — отдельный верхний слой с новыми произносительными эталонами; он сознательно изменит поведение Silero и не должен смешиваться с этим parity baseline. Дополнительный эксперимент ради самого отделения preprocessing больше не является блокером.
