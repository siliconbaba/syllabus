# Silero v5_5_ru → iOS: фактические результаты

**Обновление:** последующий [ONNX + DSP эксперимент](REPORT_ONNX_DSP.md) успешно прошёл численное сравнение на 8/8 fixtures. Ниже сохранены результаты первого этапа, включая исходные экспортные блокеры.

Дата: 2026-09-24. Исследование выполнено вне production-приложения.

## Решение

**Neural core отделяется и вызывается напрямую без потери waveform на проверенном корпусе. Однако готового мобильного exported core не получено.** Поэтому «практически без потерь на iOS» — обоснованная цель следующего PoC, а не доказанный результат этого эксперимента. Сложность дальнейшего PoC: **high**.

Не менялись sample rate, веса, квантизация, Swift-приложение, UI или Apple TTS. Нет замены ударений упрощённым словарём. Не запускалось на физическом iPhone. Не проводился субъективный слепой A/B-тест.

## Артефакт и окружение

Источник: https://models.silero.ai/models/tts/ru/v5_5_ru.pt

Размер: 145420684 байта. SHA256:

```
50081637b602126ee06cb3bc8a744d25651d2da149ee8864b9a379bfdd934437
```

Python 3.14.3, PyTorch 2.14.0, macOS arm64; ONNX 1.23.0, ONNX Runtime 1.30.0. Полный lock — `requirements-lock.txt`. Reference: CPU, xenia, 48000 Hz. Эти результаты относятся именно к указанному хешу и версиям инструментов.

Загрузка штатная: `torch.package.PackageImporter(...).load_pickle('tts_models', 'model')`.

Объект: `multi_acc_v3_package.TTSModelMultiAcc_v3`, обычный Python-класс, **не** `nn.Module`. Публичные методы: `apply_tts`, `save_wav`, `to`, `unpack_q_model`. Внутри один `PartTTSModelMultiAcc_v3`, один синтезирующий `RecursiveScriptModule` и обёртка `SileroStress` с двумя вспомогательными моделями. Полные signatures, 286 записей `named_modules` включая root, параметры и buffers сохранены в `reports/inventory.json`.

Синтезирующее ядро: 20905064 параметра и 11 зарегистрированных buffers. Это не размер всего package: preprocessing содержит дополнительные веса и словари; часть ScriptModule-атрибутов не является registered buffer. Инвентаризация auxiliary-моделей приведена отдельно.

Speakers и ID: aidar=0, baya=1, kseniya=2, eugene=3, xenia=4. Это integer conditioning, не аудиореференс и не Python-объект голоса. Speaker embeddings: акустическая модель `[5,128]`, предиктор длительности `[5,64]`, предиктор тона `[5,64]`.

## Реальный pipeline

```text
raw Russian text / SSML
  → Python normalization / XML prosody parsing
  → Python homograph tagging + WordPiece
      → tensor homograph model → Python choice from dictionary
  → stress/ё: Python rules + TorchScript n-gram string lookup
      → embedding + stress/ё classifiers → Python string reconstruction
  → character tokenizer (не phonemizer), SOS/EOS + symbol IDs
  → tensor preparation: sequence, rates, pitch coefficients, speaker ID
  + raw-text question classifier → per-token type_ids
  + optional focus/intensity processing → focus_mask / gt_pitch
  → duration predictor + pitch predictor + acoustic model
  → Vocos-style convolutional backbone + spectral head
  → complex spectrum → IRFFT → overlap-add / window normalization
  → waveform 48000 Hz
```

| Этап | Фактическая логика и данные | Перенос в Swift / exported graph |
|---|---|---|
| Normalization | Python `re`, lowercase, дефисы, whitelist из 47 символов; `prepare_text_input` и `prepare_tts_model_input` | Swift возможен с точным воспроизведением Unicode/regex; в численный graph не включать |
| Homographs | Python поиск слов из 1924-entry homodict, вставка `[HOMO]`; собственный BasicTokenizer/WordPiece, vocab 83830; tensor model принимает token IDs и границы слова, затем sigmoid/round; Python выбирает написание | Tokenizer/словари/постобработка → Swift; нейросеть → отдельный graph, её экспорт ещё не проверен |
| Stress и ё | `SileroStress` сначала вызывает homosolver, затем AccentorNgram; 16969 exceptions, 126523 ngrams; TorchScript accentor принимает **List[str]**, сам делает строковый lookup, затем embedding_bag и два classifier | Не весь accentor является tensor-only. Для экспорта отделять ngram indices/offsets от embedding/classifiers; строки и правила → Swift с теми же данными |
| Tokenization для TTS | `phons=False`; посимвольные ID, `+` для ударения, `ё`, punctuation, `|` SOS, `~` EOS; `preprocess_tacotron` | Простой точный Swift mapping; tensor packing допустим в graph. В этой конфигурации нет отдельного G2P/phonemizer |
| SSML | `xml.etree.ElementTree`, рекурсивные `speak`, `break`, `prosody`, `p`, `s`; duration map в шагах 12.5 ms, vectors rate/pitch | XML и правила → Swift; полученные тензоры и явные паузы → ядро. Dict ветви отдельно усложняют export |
| Questions | Python `classify_sentence/classify_text`: regex, вопросительные слова/обороты, punctuation → шесть типов; `build_type_ids_inference` делает `[1,T]` int64 | Swift реалистичен; влияет на tensor pitch predictor. Это не отдельный question neural model |
| Focus/intensity | Python звёздочки, поиск слов, маска; multi-sentence focus может дополнительно вызвать pitch predictor и собрать `gt_pitch` | Нужно портировать и эту orchestration для полного паритета; baseline без focus |
| Speaker | Python name→ID; embeddings внутри neural core | Swift таблица имён + tensor ID; embeddings остаются в graph |
| Synthesis | TorchScript duration/pitch/acoustic/vocoder modules, data-dependent длины | Веса переносимы, автоматический export текущего графа заблокирован |
| Waveform | Complex spectral head, `fft_irfft`, windowing, fold/`col2im`, crop, division; при 48000 нет PQMF downsampling | Кандидат на точный real-valued graph либо отдельный DSP-этап; эквивалентность потребуется измерить |

Внешние зависимости оригинального package: PyTorch и стандартные Python-модули (`re`, `xml`, `json`, `gzip`, `unicodedata` и др.). В reference не потребовались сторонний phonemizer, transformers, сервер или скачивание дополнительных моделей. Исходные пути словарей в коде относятся к сборке Silero; в загруженном объекте необходимые данные уже присутствуют.

### Источники внутри package

Все пути ниже относительно `artifacts/package/`, извлекаемого `fetch_model.py`:

- `multi_acc_v3_package.py`: wrapper 111–178; normalization 275–317; SSML 351–537; `apply_tts` 581–799; question type tensor 831–857; merge 859–927; tokenizer 929–943; unpack 1003+.
- `models/model.py`: порядок homosolver → accentor.
- `models/homosolver.py`: поиск, tensor inference и реконструкция слова.
- `models/accentor.py`: stress/ё confidence/rules, exceptions и восстановление строки.
- `custom_tokenizers/bert_tokenizer.py`: собственная реализация tokenizer.
- `.data/ts_code/code/__torch__/models/modules.py`: строковые ngrams внутри TorchScript, затем embedding_bag.
- `.data/ts_code/code/__torch__/vocoder/hifigan/vocos/vocos/heads.py`: complex spectral head.
- `.data/ts_code/code/__torch__/tts_package/package_utils.py`: ISTFT. Для этой модели FFT=2400, window=2400, hop=600, padding=`same`.

### Важные особенности reference

Модель не проговаривает цифры и латиницу автоматически: `Мы исправили 25 ошибок за 3 дня.` → `мы исправили ошибок за дня.`; `API вернул ошибку HTTP 500.` → `вернул ошибку .`; `SLA` также удаляется. Для честного reference тексты не исправлялись. Будущая нормализация технического текста — отдельная продуктовая задача, не условие паритета с данным package.

В омографическом примере оригинал даёт `в ст+аром з+амке вис+ит з+амок`: второе слово семантически ожидалось `зам+ок`. Значит, сохранение поведения оригинала само по себе не гарантирует безошибочное произношение. Эти ошибки не маскировались ручными ударениями.

Question handling находится внутри `.pt`, но преимущественно в Python. Типы: st=0, wh_q=1, general_q=2, alternative_q=3, tag_q=4, exclam=5. В многопредложном тексте распределение типов строится по длинам raw text, затем подгоняется к длине sequence; порт должен воспроизвести реальное правило, а не предполагать идеальное выравнивание после добавления `+`.

## Граница neural core и прямой вызов

Перехват: подмена одного элемента `part.models[model_id]` прозрачным вызываемым proxy только в исследовательском процессе. Штатный `apply_tts` полностью выполняет preprocessing, proxy копирует kwargs и возвращает результат неизменённого core. Затем core вызывается повторно с теми же inputs и RNG state. Протокол в `reference.py`.

Минимальная найденная граница, возвращающая waveform: `part.models[0](**model_kwargs)`. Результат `(audio, dur_hat)`; wrapper выбирает `audio.cpu()[0]`. `wrapped_jit_v=None`, отдельный внешний vocoder для baseline не требуется.

Пример «Когда будет готов релиз?»:

| Аргумент | Значение / контракт |
|---|---|
| sequence | int64 `[1,30]`, включая ударения и SOS/EOS |
| speaker_ids | int64 `[1]`, значение `[4]` |
| sr | Python int `48000` |
| symb_durs | пустой Dict[int,int] |
| durs_rate | float32 `[1,30]`, единицы |
| pitch_coefs | float32 `[1,30]`, единицы |
| type_ids | int64 `[1,30]`, единицы (`wh_q`) |
| device | `cpu` |
| focus_mask | None |
| остальные defaults core | gt_durs=None, gt_pitch=None, accent_word=-1, question=False |

Значения каждого tensor — `reports/question-inputs.json`; исполняемый fixture — `artifacts/question-fixture.pt`. Waveform примера содержит 75000 samples, 1.5625 секунды. Контракт поддерживает variable T; waveform length зависит от предсказанных durations, поэтому фиксированного trace на одной длине недостаточно.

## Golden corpus и численные результаты

Все восемь случаев из `corpus.json` завершились успешно. Исходный PyTorch wrapper против прямого PyTorch core: **max absolute error=0, RMSE=0, bit_equal=true для каждого**. Длительности от 1.2 до 13.1375 секунды. Полные тексты после обработки и метрики: `reports/reference-results.json`.

Пары `*-reference.wav` / `*-direct.wav` сохранены для прослушивания, но это **не PyTorch vs mobile-runtime A/B**. Exported waveform-runtime не получен, поэтому его численные и слуховые метрики отсутствуют. Аналогично нет измерений latency/RAM на iPhone. Времена reference в JSON — одиночные CPU-прогоны на Mac, не бенчмарк устройства.

## Экспорт: что реально проверено

1. **torch.export напрямую**: отказ `Exporting a ScriptModule is not supported`.
2. **TS2EPConverter** из предлагаемого PyTorch пути: `prim::Constant`, `Unsupported constant type: cs` (complex scalar).
3. **nn.Module wrapper → torch.export**: `GuardOnDataDependentSymNode`, ветка `if dur_hat[0][0] > 5` после duration prediction. Даже static token length не устраняет зависимость от данных.
4. **ONNX, scripted wrapper, opset 18, dynamo=False**: `Unknown number type: complex`, spectral head использует complex constant, далее IRFFT. Dynamic axes заданы для token tensors и waveform, но валидный graph не создан — dynamic shapes не подтверждены исполнением.
5. **Дополнительный ONNX probe отдельно duration и pitch predictors**: оба остановились на `prim::is_nested`, неподдержанном этим exporter/opset. Это exporter blocker; не доказательство невозможности этих transformer-вычислений на ONNX Runtime.

Полные stack traces и результаты — `reports/*-error.txt`, `export-results.json`, `component-export-results.json`. `reports/core-operators.json` сохраняет список операторов. Дополнительные видимые сложности: `aten::repeat_interleave`, data-dependent allocation, `aten::item`, ветви/циклы TorchScript, `aten::fft_irfft`, `aten::col2im`. Они **не все экспериментально подтверждённые ошибки exporter**: часть обнаружена только статическим анализом, потому что экспорт остановился раньше.

Пользовательские Silero binary custom ops не потребовались для CPU reference. Это не означает, что каждый стандартный ATen op поддерживается выбранным мобильным backend. Unsupported `prim::is_nested` не предлагается заменять произвольным custom-op без проверки dense-input контракта.

**ExecuTorch .pte не получен:** нет успешного ExportedProgram, lowering не выполнялся и пакет ExecuTorch не устанавливался. **Core ML не пробовался:** условие успешного экспорта ядра не выполнено; оптимизации здесь преждевременны.

## Что придётся перенести и сохранить

Swift-часть: normalization; точный character mapping; homograph WordPiece tokenizer с тем же vocabulary; поиск слов и выбор вариантов; ngram enumeration/lookup и exceptions; rules stress/ё; question classification и заполнение type IDs; SSML parsing, duration map, prosody vectors; focus orchestration и speaker mapping. Нейронные модели stress/homographs нельзя заменить только regex/словарём без риска деградации.

Stress-модель уже содержит строковую логику внутри TorchScript; её надо разделить на host-side подготовку indices/offsets и численный graph. Homosolver уже tensor-only на уровне собственной модели, но ему нужны идентичные token IDs/границы и штатная однократная распаковка embedding weights. Возможность получить preprocessing отдельно подтверждена вызовами `prepare_text_input`, `accentor` и перехватом kwargs; JSON содержит промежуточные строки.

## Ответы и следующий шаг

1. **Отделить core? Да**, экспериментально.
2. **Вызвать напрямую? Да**, 8/8 точных совпадений CPU float waveform.
3. **ExecuTorch/ONNX экспорт? Нет** для неизменённого waveform core в проверенном toolchain.
4. **Блокеры:** ScriptModule frontend, complex constants/spectrum, data-dependent duration branch; у отдельных predictors — `prim::is_nested`.
5. **Auto-stress/homographs/questions:** все внутри package; stress/homographs используют отдельные модели и словари, questions — Python rules с conditioning pitch model.
6. **Swift:** перечисленная orchestration/text processing, с сохранением исходных данных и вспомогательных сетей.
7. **Качество на iOS почти без потерь? Пока не доказано.** Веса не нужно переучивать; математически эквивалентный перенос выглядит возможным, но требует проверки всех трёх моделей и DSP, не только акустического core.
8. **Сложность high:** три нейронных пути, строковый TorchScript preprocessing, динамическая длительность и complex DSP, отсутствие работающего mobile graph и device parity.
9. **Наиболее реалистичный следующий кандидат — ONNX Runtime + точный отдельный DSP**, как рабочая гипотеза, не готовая рекомендация к интеграции. Его scripted exporter уже добирается до конкретных операторов, есть официальный iOS runtime. ExecuTorch остаётся альтернативой после восстановления export-friendly nn.Module; Core ML отложить до доказанного графа.
10. **Минимальный следующий эксперимент:** на сохранённых fixtures выделить duration/pitch/acoustic + spectral real outputs, устранить dense-transformer `is_nested` ветки без изменения математики, отделить IRFFT/overlap-add от complex graph и выполнить их эквивалентно вне него. Сначала ONNX Runtime CPU на Mac против исходного float waveform на всех восьми входах, затем тот же набор в отдельном iOS command/test target на физическом iPhone. Сравнить lengths, duration outputs, max abs/RMSE, relative L2/SNR и log-spectral difference плюс слепое A/B. Это даст ответ о переносимости **синтезирующего ядра**. Для окончательного end-to-end ответа дополнительно требуются exact preprocessing fixtures и parity двух auxiliary-моделей на расширенном корпусе; один короткий WAV не доказывает сохранение русского произношения.

## Внешние первичные источники

- [Silero: официальный репозиторий, standalone PackageImporter usage](https://github.com/snakers4/silero-models). Архитектурные выводы выше получены из скачанного файла, а не распространены с других версий Silero.
- [PyTorch ExecuTorch: export и runtime](https://github.com/pytorch/executorch/blob/main/docs/source/intro-how-it-works.md).
- [ONNX Runtime Mobile: официальный iOS путь](https://onnxruntime.ai/docs/tutorials/mobile/).

Production diff после исследования остался прежним: только ранее существовавшая локальная Team в pbxproj. Новые файлы находятся исключительно в `experiments/silero-ios-feasibility/`. Публикация не выполнялась.
