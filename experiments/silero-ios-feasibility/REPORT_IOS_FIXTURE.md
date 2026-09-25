# iOS fixture PoC — Silero v5_5_ru

Дата: 2026-09-25 (Europe/Moscow). **Успех: 8/8 fixtures в iOS Simulator.**

Доказанная ранее цепочка ONNX + внешний DSP работает внутри отдельного iOS/Swift приложения. Все пять graphs реально исполняются, predicted integer durations, shapes и длины совпадают. Это подтверждает numerical synthesizer для подготовленных inputs, но не перенос всего Silero с обработкой русского текста.

## Конфигурация и воспроизведение

- Apple Silicon Mac M4, Simulator iPhone 17 Pro; runtime сообщает iOS 26.3.1 (23D8133), UI показывает 26.3.
- Xcode 26.2, SDK 26.2; deployment target iOS 16.0.
- Официальный ONNX Runtime **1.24.2**, Swift Package Manager, exact version; lock-файл в отдельном Xcode project. CPU EP, float32, batch=1, xenia, 48000 Hz; intra-op=4, inter-op=1, graph optimization ALL. CoreML EP/custom operators не подключаются.
- [Официальный SPM package](https://github.com/microsoft/onnxruntime-swift-package-manager/tree/1.24.2), commit `b7fb7f7dea8a2469e6335d95a61b8f36d0dc83b2`. Бинарный архив SHA256 `f7100a992d2a8135168c8afd831e6a58b465349101982aa58b3e11d36e600b54`.
- ObjC API package не представляет BOOL tensor в enum, необходимый для mask. Небольшой `ORTBridge.mm` вызывает публичный C++ API той же официальной библиотеки, поддерживая float32/int64/bool. Это host bridge, не custom ONNX operator.
- Mac stage 2 использует ORT 1.30.0; поэтому побитовое совпадение между runtime не предполагалось.

Из текущего исследовательского каталога с уже готовыми stage 2 artifacts:

```sh
# Список устройств и UUID:
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
# Подготовка копий исходных tensors, сборка и запуск (подставить UUID):
bash ios/run_simulator.sh "$SIMULATOR_ID"
# Дождаться Parity: 8/8, нажать Play в приложении; затем:
bash ios/collect_simulator.sh "$SIMULATOR_ID"
```

Первое разрешение SPM требует сети. Скрипты используют `.venv/bin/python` (NumPy из существующего окружения); можно задать `PYTHON`. Новых Python-зависимостей не добавлено. Модели не экспортируются повторно. Если stage 2 artifacts отсутствуют, их сначала надо восстановить по предыдущему README; одних исходников iOS harness для синтеза недостаточно.

Для ручного запуска открыть `ios/SileroIOSPoC.xcodeproj`, scheme `SileroIOSPoC`, выбрать Simulator и Run. Ресурсы предварительно создать `.venv/bin/python prepare_ios_fixtures.py`. Для будущего физического iPhone выбрать свой Team/уникальный Bundle ID в отдельном project; архитектурная переделка не требуется, но сборка и скорость на устройстве здесь не проверялись.

## Модели и fixtures

Пять моделей скопированы без изменения bytes. SHA256 перепроверены после сборки, исходный window.npy не изменён; `window.bin` — ровно его 2400 float32 значений. `resources-manifest.json` описывает little-endian row-major binary, shape/dtype и SHA256 каждого tensor. При конвертации проверен byte/value round-trip.

| Graph | Размер, bytes | SHA256 |
|---|---:|---|
| duration | 2279956 | `cb078455e1f62cce8eea8c162289e2ef7fecd64f564c081a4151fe92337e8980` |
| pitch | 2281630 | `6de663792367cde7305614469f1dd52a0bcacf24aae4183fe90acd655d565103` |
| encoder | 14200427 | `d349307b3d77b8ac870b14ae0a53877cd96d5c454bfa79d6987da113c34d9479` |
| decoder | 11563943 | `f9970f6b3e66c3d5dcaaefb7c45a5aa26bf1077b0ada40f4f1129251944fc054` |
| spectral | 58288938 | `dd8b27331f5b6499990490af06ec8ca9779508d4071aed2440496cad9cbf7bcf` |

Всего моделей: 88,614,894 bytes.

Inputs sequence, speaker_ids, type_ids, durs_rate, pitch_coefs взяты из существующих stage 2 fixtures. Mask вычисляется `sequence == 0`. Preprocessing не запускается. Baseline без SSML/focus, pitch_coefs=1. Reference durations используются только после синтеза для сравнения.

Host duration processing: `roundEven(max(exp(log)-1,0))`, первый token cap=5, деление на durs_rate и roundEven, caps первого/последнего=5/7, предпоследний=13, третий с конца cap=13. Pitch abs<0.001 → 0. Encoder повторяется по вычисленным durations; затем decoder → spectral.

Для каждого примера проверены shapes: duration `[1,T]`, pitch `[1,1,T]`, encoder `[1,T,128]`, decoder `[1,192,F]`, spectral `[1,2402,F]`, samples=`600*F`. Все durations совпали целочисленно. Дополнительный Python audit независимо проверил сохранённые Swift float32 waveform, metrics и SHA256 без torch.

## Numerical parity

Без gain alignment, resampling, сдвига waveform или подгонки scaling. Сравниваются исходные float32, до PCM16. Regression bounds: relative L2 < 0.001 для полного пути относительно Mac и golden; DSP-only < 1e-5; durations/shapes/length exact. Это инженерные bounds, не универсальное доказательство субъективной неслышимости.

### iOS против Mac ONNX + NumPy DSP

| Fixture | T | F | Samples | max abs | RMSE | relative L2 | SNR dB |
|---|---:|---:|---:|---:|---:|---:|---:|
| statement | 59 | 232 | 139200 | 0.0002527982 | 7.2369629e-06 | 6.1518588e-05 | 84.220 |
| question | 30 | 125 | 75000 | 3.9177015e-05 | 1.2283427e-06 | 9.9234114e-06 | 100.067 |
| homograph | 81 | 383 | 229800 | 6.8631023e-05 | 2.4977109e-06 | 2.1421903e-05 | 93.383 |
| yo | 53 | 225 | 135000 | 8.0704689e-05 | 4.2909948e-06 | 3.6151486e-05 | 88.837 |
| number | 34 | 146 | 87600 | 0.00014451146 | 7.4755681e-06 | 5.8100005e-05 | 84.716 |
| technical | 62 | 243 | 145800 | 0.00035445392 | 1.4449047e-05 | 0.00011161123 | 79.046 |
| abbreviations | 19 | 96 | 57600 | 7.6834112e-05 | 3.5125708e-06 | 3.036154e-05 | 90.354 |
| long | 274 | 1051 | 630600 | 8.7974593e-05 | 3.3210652e-06 | 3.3049272e-05 | 89.617 |

### iOS против оригинального PyTorch golden

| Fixture | max abs | RMSE | relative L2 | SNR dB |
|---|---:|---:|---:|---:|
| statement | 0.0001164116 | 3.7737979e-06 | 3.2079567e-05 | 89.875 |
| question | 2.9087067e-05 | 2.1705034e-06 | 1.7534837e-05 | 95.122 |
| homograph | 0.00034369342 | 6.0960935e-06 | 5.2283833e-05 | 85.633 |
| yo | 5.4255128e-05 | 3.427782e-06 | 2.887895e-05 | 90.788 |
| number | 0.00032639503 | 1.551797e-05 | 0.00012060542 | 78.373 |
| technical | 0.0021373928 | 3.6200496e-05 | 0.00027962873 | 71.068 |
| abbreviations | 0.00017216057 | 1.1470184e-05 | 9.9144699e-05 | 80.075 |
| long | 0.00010679476 | 2.7627758e-06 | 2.7493506e-05 | 91.215 |

На technical max abs относительно golden 0.002137, несколько выше прежнего Mac max abs ~0.001783; при этом relative L2 0.000280 лучше прежнего ~0.000321. Резкого роста общей ошибки нет. Intermediate duration_log/pitch/mel/spectral differences сохранены в JSON; DSP изолирован отдельно на идентичных Mac spectral inputs.

## FFT/DSP: существенное отличие от предпочтённого варианта

**Accelerate/vDSP не использован как FFT backend.** Реальные вызовы split-complex DFT n=2400, interleaved complex n=2400 и interleaved real count=1200 возвращают nil и на Mac, и внутри Simulator. У поддерживаемых этими API radix-size сочетаний нет требуемого размера. Проблема — доступность setup, а не найденный неправильный коэффициент vDSP. Radix-2 FFT также не соответствует n=2400. Проба сохранена в `ios/AccelerateLengthProbe.swift`, результаты iOS — в JSON scaling.

Использован готовый [KissFFT 131.1.0](https://github.com/mborgerding/kissfft/tree/131.1.0), commit `8f47a67f595a6641c566087bf5277034be64f24d`, float32 C implementation, исходники и BSD-3-Clause license в `ios/SileroIOSPoC/Vendor`. Собственный FFT не написан; преобразование спектра, window/OLA/crop/envelope выполнены Swift. KissFFT включён исключительно в исследовательский target.

KissFFT inverse не нормирован: явное деление на **2400** соответствует NumPy `irfft(n=2400,norm="backward")`. Аналитические проверки DC, Nyquist и cosine bin37 дали максимальные ошибки 1.01e-11, 1.01e-11, 2.06e-10; порог 1e-8. Мнимые части DC/Nyquist обнуляются как у irfft.

DSP: min(exp(logmag),100), cos/sin phase; 1201 complex bins → inverse2400; исходное float32 window; hop600; overlap-add и window²; crop900 с двух сторон; деление на envelope. Дополнительной нормализации громкости нет.

При подаче одних и тех же Mac spectral tensors в Swift DSP relative L2 составляет 1.27–1.35e-7, SNR 137.40–137.90 dB, max abs ≤2.3842e-7. Это отдельно доказывает scaling/window/OLA и локализует существенно большую полную ошибку в различиях neural runtime перед DSP.

## Timings Simulator

Один измеренный прогон, не benchmark и не прогноз iPhone. Swift -O, C -O2. Timings synthesis исключают session initialization, чтение входных fixtures, regression comparisons и WAV; total включает промежуточные копии tensors и host overhead. DSP-only повтор для сравнения также вне total.

| Session | Initialization ms |
|---|---:|
| decoder | 21.021 |
| duration | 93.053 |
| encoder | 29.005 |
| pitch | 27.379 |
| spectral | 117.491 |
| **Сумма** | **287.949** |

| Fixture | duration ms | pitch ms | encoder ms | repeat_expansion ms | decoder ms | spectral ms | dsp ms | total ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| statement | 3.439 | 1.290 | 6.694 | 0.149 | 9.852 | 37.513 | 11.617 | 71.356 |
| question | 1.817 | 1.186 | 6.438 | 0.063 | 3.575 | 19.480 | 7.257 | 40.269 |
| homograph | 1.803 | 3.658 | 5.271 | 0.051 | 12.454 | 50.649 | 15.943 | 90.932 |
| yo | 2.015 | 1.147 | 4.182 | 0.088 | 6.546 | 29.136 | 9.178 | 53.053 |
| number | 0.460 | 0.654 | 3.533 | 0.043 | 5.072 | 12.592 | 7.322 | 29.957 |
| technical | 0.524 | 1.206 | 4.371 | 0.035 | 11.540 | 22.559 | 11.150 | 52.097 |
| abbreviations | 0.575 | 0.726 | 4.014 | 0.034 | 2.916 | 10.958 | 2.714 | 22.253 |
| long | 2.347 | 5.327 | 10.657 | 0.172 | 48.238 | 92.960 | 30.947 | 193.732 |

Duration host processing отдельно в JSON (0–0.0011 ms, разрешение часов ограничено). Process physical footprint через task_info: 143–237 MiB в точках после fixtures, после завершения 225.5 MiB. Это не peak и не память одного neural core: включает app, runtime, fixtures и проверки. Оптимизация памяти не выполнялась.

## Аудио и Xcode

WAV PCM16 mono48k записывается только после parity-pass; float32 `.f32` сохраняется отдельно. Нажата кнопка **Play long** после `Parity: 8/8`; AVAudioPlayer вернул true, isPlaying=true, duration=13.1375 s. UI подтвердил воспроизведение. Это проверка playback API, не субъективная экспертиза тембра. `reports/ios/playback.json` хранит результат. Все восемь iOS WAV находятся в `artifacts/ios-results/`, рядом float32 и report.json; оригинальные reference WAV — в предыдущих artifacts.

Создан самостоятельный `ios/SileroIOSPoC.xcodeproj`, shared scheme, отдельный bundle id `ai.research.SileroIOSPoC`; SPM dependency, bridging header и FFT sources относятся только к нему. Fixtures лежат в папке `Fixtures`, поскольку имя bundle-папки `Resources` приводило к ошибке установки Simulator. Исправлены C linkage bridge и Swift concurrency warnings. Финальная сборка — BUILD SUCCEEDED; приложение установлено и запущено.

Production targets, SpeechReaderManager, SpeechTextProcessor, Apple TTS, BookView, HTML, background modes и Now Playing этим этапом не изменены. В production project до начала этапа уже были локальные изменения DEVELOPMENT_TEAM; они сохранены. GitHub push/commit не выполнялся. Большие модели, binary fixtures, build и Packages исключены из git.

## Вывод и следующий шаг

**Да: существующий numerical synthesizer переносим в iOS/Swift на подготовленных inputs.** Успех подтверждён всеми 8 fixtures, пятью ORT sessions, точными durations/shapes/lengths, independent waveform audit и AVFoundation playback. Доказательство ограничено CPU float32, xenia48k, baseline tensors и Simulator. Нельзя по нему утверждать полноценный raw-Russian-text TTS на iPhone, универсальную поддержку SSML или performance/качество на физическом устройстве.

Перед end-to-end остаются русский normalization/tokenization, stress/ё, homograph WordPiece и auxiliary model, AccentorNgram, question handling и словари. Ничего из этого здесь не упрощалось и не переносилось. Следующий самостоятельный эксперимент: получить в Swift идентичные prepared tensors из golden raw text, проверяя каждый preprocessing этап. Отдельно — тот же fixture harness на реальном iPhone с parity, прослушиванием, repeated timings и peak memory. Интеграция в читалку остаётся отдельной задачей.

Машиночитаемые доказательства: `reports/ios/simulator-report.json`, `resources-manifest.json`, `independent-audit.json`, `playback.json`. Код проверок: `prepare_ios_fixtures.py`, `audit_ios.py`, Swift Sources, два ios shell scripts.
