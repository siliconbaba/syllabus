# Silero v5_5_ru: feasibility на iOS

Изолированное исследование от 2026-09-24. Production Swift, Apple TTS и Xcode target не изменялись. Ничего не отправлено в GitHub.

**Текущий результат, этап 2:** пять ONNX-графов + независимый DSP проходят численный parity на 8/8 prepared fixtures, с одинаковыми длительностями. Отдельный runtime-only запуск не импортирует PyTorch. Слуховой A/B и iPhone пока не проверены. Актуальный отчёт: [REPORT_ONNX_DSP.md](REPORT_ONNX_DSP.md). История первого этапа: [REPORT.md](REPORT.md).

## Воспроизведение

Проверено на macOS arm64, Python 3.14.3, PyTorch 2.14.0 (CPU). Команды выполнять из этого каталога. Зависимости устанавливаются только в `.venv`. Для другого Python нужны совместимые колёса; смена версий требует повторения измерений.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python fetch_model.py
.venv/bin/python inspect_model.py
.venv/bin/python reference.py
.venv/bin/python export_probe.py > artifacts/export.log 2>&1
.venv/bin/python component_probe.py > artifacts/components.log 2>&1
```

`fetch_model.py` проверяет точный SHA256. Если файл по URL изменился, скрипт останавливается, а не подменяет baseline. Загрузка через `torch.package.PackageImporter(...).load_pickle('tts_models', 'model')` выполняет официальный упакованный Python-код. Скачанные исходники извлекаются в `artifacts/package/` для изучения.

Baseline: CPU, 4 потока после загрузки (внутренний импорт Silero меняет число потоков), xenia, 48000 Hz, исходные defaults stress/yo/homographs, seed 20260924. В `reference.py` вызывается штатная однократная распаковка весов homosolver — это поведение оригинального `apply_tts`, не новая квантизация.

## Результаты и файлы

- `corpus.json`: восемь исходных русских текстов; цифры и латиница намеренно не заменяются.
- `reports/inventory.json`: объект, методы, submodules, параметры, buffers, speaker mappings.
- `reports/preprocessing-data.json`, `stress-inventory.json`, `homographs-inventory.json`: данные и вспомогательные модели.
- `reports/*-inputs.json`: значения всех подготовленных входов, shapes, dtypes и настройки.
- `artifacts/*-fixture.pt`: те же входы, RNG state, исходный float waveform.
- `artifacts/*-reference.wav`, `*-direct.wav`: пары для прослушивания (PCM16, 48000 Hz). Метрики считаются до PCM-преобразования.
- `reports/reference-results.json`: тексты после обработки, длительности, max abs / RMSE / exact equality.
- `artifacts/neural-core.jit.pt`: отдельно сериализованное исходное ядро TorchScript, **не** мобильный exported runtime.
- `reports/export-results.json`, `component-export-results.json`, `*-error.txt`: реальные ошибки экспорта.
- `requirements-lock.txt`: версии исследовательского окружения.

Экспортные скрипты записывают неуспех в JSON и завершают эксперимент без падения: код выхода 0 не означает успешного экспорта. При полном успехе `torch.export` скрипт попробует ExecuTorch; сейчас этот этап недостижим, ExecuTorch не устанавливался, `.pte` не создан. Для будущего прогона после исправления графа нужно отдельное окружение с совместимой парой torch/executorch.

`.gitignore` исключает `.venv`, все модели, WAV, fixtures и извлечённые исходники в `artifacts/`. Большой исходный файл (145420684 байта) не добавлять в git. Исследовательские скрипты и JSON-отчёты можно версионировать отдельно, но в этом задании публикация не выполнялась.

## Этап 2: ONNX + независимый DSP

Используются уже созданные golden fixtures. Не перезапускайте reference.py без необходимости. Исходные fixtures не переписываются. Все новые бинарные результаты попадают в `artifacts/onnx-dsp/` и игнорируются git.

```sh
mkdir -p artifacts/onnx-dsp reports/onnx-dsp
# Capture добавляет outputs в копию graph и сверяет исходный waveform с golden.
.venv/bin/python capture_spectral.py > artifacts/onnx-dsp/capture.log 2>&1
# Экспорт разрешён только после успешного DSP parity.
.venv/bin/python stage2_export.py > artifacts/onnx-dsp/adapter-export.log 2>&1
.venv/bin/python stage2_parity.py > artifacts/onnx-dsp/parity.log 2>&1
.venv/bin/python audit_stage2.py
# Отдельный процесс без torch: только ORT + NumPy и подготовленные npz inputs.
.venv/bin/python run_onnx_only.py > artifacts/onnx-dsp/onnx-only.log 2>&1
```

Перед первым запуском `capture_spectral.py` создайте каталоги:

```sh
mkdir -p artifacts/onnx-dsp reports/onnx-dsp
```

Успех экспорта проверяется по `reports/onnx-dsp/adapter-export.json`, а не по одному коду возврата скрипта. `stage2_parity.py` загружает все пять моделей; отсутствующий файл/ошибка runtime приводит к остановке. `audit_stage2.py` проверяет regression bounds, одинаковые durations/lengths и стандартные операторы. Эти bounds численные, не универсальный критерий неслышимости.

`boundary_probe.py`, `export_predictors.py`, `export_utils.py` — сохранённые диагностические/неудачные промежуточные пути; для воспроизведения успешной цепочки они не нужны.

`run_onnx_only.py` не использует исходную модель, её package, auxiliary-модели или preprocessing. Для запуска ему нужны пять `.onnx`, `window.npy` и подготовленные `*-prepared-inputs.npz`. Reference `.npy` нужны только для сравнения. Проверяется, что модуль torch не загружен.

Baseline host-контракт: batch=1, 48000 Hz, без SSML duration overrides/focus, pitch coefficients=1. Все восемь inputs имеют разные token lengths; значения durations вычисляются предиктором при каждом запуске. Адаптеры не являются универсальной заменой всех API Silero.

## Этап 3: отдельный iOS fixture PoC

Завершён: все 8 fixtures прошли ORT CPU float32 → Swift orchestration → DSP в iOS Simulator. Подробности, численные метрики и ограничения: [REPORT_IOS_FIXTURE.md](REPORT_IOS_FIXTURE.md).

```sh
# Требуются существующие stage 2 artifacts, Xcode и сеть для первого SPM resolve.
# Узнать UUID: DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
bash ios/run_simulator.sh SIMULATOR_UDID
# Дождаться Parity: 8/8, нажать Play; собрать результаты и проверить независимо:
bash ios/collect_simulator.sh SIMULATOR_UDID
```

Либо `.venv/bin/python prepare_ios_fixtures.py`, открыть `ios/SileroIOSPoC.xcodeproj` и Run. iOS16, SPM ORT1.24.2; FFT2400 через vendored KissFFT131.1.0, поскольку проверенные vDSP DFT setup возвращают nil для этого размера. Инструкции физического устройства и ограничения — в отчёте. Production-приложение не связано с этим target. Модели/fixtures/build/Packages в git не включаются.

## Этап 4: raw Russian text → Swift preprocessing → waveform

Завершён для plain-text baseline: 25/25 stage comparisons, исходные 8/8 end-to-end. [REPORT_IOS_PREPROCESSING.md](REPORT_IOS_PREPROCESSING.md) содержит архитектуру, auxiliary hashes, метрики, ограничения и подробные команды. Golden исходных восьми примеров сохранён.

```sh
mkdir -p artifacts/preprocessing reports/preprocessing
# При отсутствии auxiliary artifacts:
.venv/bin/python preprocessing_probe.py > artifacts/preprocessing/probe.log 2>&1
.venv/bin/python export_preprocessing.py > artifacts/preprocessing/export.log 2>&1
.venv/bin/python capture_preprocessing.py > artifacts/preprocessing/capture.log 2>&1
# С готовыми artifacts достаточно:
bash ios/run_preprocessing.sh SIMULATOR_UDID
# После 25/25 + 8/8 и Play:
bash ios/collect_preprocessing.sh SIMULATOR_UDID
```

Default Run standalone project теперь проверяет preprocessing; `--fixtures-only` сохраняет прежний этап (старый run_simulator.sh передаёт аргумент сам). Вся обработка в приложении — Swift + official ORT, без Python. Два auxiliary models и исходные словари используются только исследовательским target. A/B WAV находятся в `artifacts/preprocessing/ios-results/ab/`. Латиница/цифры по-прежнему удаляются согласно оригинальному Silero; SSML/focus и production integration вне scope.

## Этап 5: технический текст перед Silero (opt-in)

`TechnicalSpeechNormalizer` преобразует термины, числа и символы в speech copy, не меняя оригинальный Silero preprocessing. 105 терминов (23 из production-словаря без копирования, 82 новых), 60 exact text/whitelist cases и 20 аудиопримеров.

```sh
bash ios/test_technical_text.sh
bash ios/run_technical.sh SIMULATOR_UDID
# После text/audio pass и выбора Play:
bash ios/collect_technical.sh SIMULATOR_UDID
```

[REPORT_TECHNICAL_NORMALIZATION.md](REPORT_TECHNICAL_NORMALIZATION.md) содержит все expected strings, ограничения, варианты произношений и ссылки на WAV. В отдельном PoC есть кнопка «Технические примеры»; основной reader не изменён. Без `--technical` сохраняется прежний exact-parity режим. Субъективная оценка произношений — ручное прослушивание, не результат numerical tests.

## Файлы вне Git

`artifacts/`, `ios/SileroIOSPoC/Fixtures/`, `ios/SileroIOSPoC/Preprocessing/` и результаты в `reports/` генерируются локально и не публикуются. В Git остаются небольшие закреплённые SHA256 manifests; исторические отчёты описывают локальные результаты. Перед командами запуска выберите Simulator через `xcrun simctl list devices available` и задайте `SIMULATOR_ID`. Для production используйте проверенный набор по `../../docs/SILERO_BUILD.md`; автоматической загрузки экспортированных весов нет.
