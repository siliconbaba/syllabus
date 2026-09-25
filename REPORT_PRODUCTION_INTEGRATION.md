# Production integration: Silero v5_5_ru

Проверено 25 сентября 2026, Xcode 26.2, iPhone 17 Pro Simulator iOS 26.3, CPU. Изменения локальные, в GitHub не отправлялись. Это готовая сборка для следующего теста на физическом iPhone, не подтверждение приемлемой памяти/качества на всех устройствах.

## Реализация

1. `SpeechEngine.swift` задаёт общий prepare/speak/pause/resume/stop/shutdown API и события с UUID запроса. `SpeechReaderManager` остаётся единственным владельцем темы, блоков, текущей позиции, подсветки, аудиосессии, Now Playing и настроек.
2. `AppleSpeechEngine.swift` содержит прежний AVSpeechSynthesizer: ручной ru-RU voice, автоматический Premium > Enhanced > Standard, rate 0.46 × multiplier, pitch 1.0, прежние задержки и возобновление. Совместимые delegate entry points менеджера оставлены для старых тестов.
3. `SileroSpeechEngine.swift` использует worker actor вне main thread, TechnicalSpeechNormalizer → SileroPreprocessor → 2 auxiliary + 5 synthesis ONNX → прежнюю Swift orchestration → KissFFT DSP → mono float32 PCM 48 kHz. Speaker Xenia. Нет сети/Python в приложении.
4. В `Audio/Silero/` перенесены доказанные правила, словари, bridge, DSP и runtime. Математика FFT/window/hop, веса, opset и float32 не менялись. Исследовательский harness и fixtures не включены в production.
5. Модели загружаются только при выборе/запуске нейросетевого режима. SHA256 проверяются до создания sessions. Ошибки подготовки/синтеза приводят к видимому сообщению и системному чтению с начала того же логического блока. Повреждённый JSON manifest также обрабатывается ошибкой.
6. Очередь хранит текущий PCM и максимум один следующий. Пока N звучит, worker готовит N+1. По завершении playback готовый буфер используется без повторного синтеза. Нет генерации всей темы. Логи содержат 30 стартов, из них 26 использовали буфер, подготовленный во время предыдущего фрагмента (остальные — начальные старты/ручные переходы). Есть серии длиннее пяти подряд. `aheadReady=false` при старте в старом диагностическом сообщении относится уже к N+2, а не к потреблённому N+1; независимая проверка основана на UUID ready/start.
7. Stop, переходы, смена темы/фильтра/движка отменяют задачи и меняют epoch/request UUID. Устаревшие результаты не начинают playback. ORT Run нельзя прервать посреди операции: cancellation проверяется между стадиями, результат старой операции отбрасывается.
8. Pause останавливает playhead без потери PCM; Resume продолжает его. Завершение, пришедшее одновременно с паузой, удерживается до Resume. Speed — AVAudioUnitTimePitch.rate, pitch=0; neural duration predictor не меняется. Субъективное качество 2× ещё требует прослушивания на телефоне.
9. Background audio, spokenAudio session и MPRemoteCommandCenter остаются общими в менеджере. Очередь загружена в Swift; фон не требует JavaScript. Прерывание ставит на паузу, разрешённое системой продолжение учитывает последующую остановку пользователем. Смена маршрута при отключении наушников приостанавливает чтение.
10. При смене движка сохраняется logical block, новый движок начинает его сначала. Выбор сохраняется в speech.engine, default — system. Нейросетевые ресурсы освобождаются при переключении на Apple и memory warning; обычный Stop оставляет sessions warm.
11. `SpeechTextProcessor` сохраняет старую Apple-нормализацию. Neural получает исходный видимый текст для отдельного TechnicalSpeechNormalizer. Разбиение преимущественно по предложениям, аварийный лимит 600 символов для neural / прежние 1200 для Apple; block ID сохраняется. Паузы PCM: 0.10 с внутри абзаца, 0.30 конец абзаца, 0.45 заголовок, 0.20 список, без изменения текста.

## Размер и измерения

Логические суммы файлов, Debug arm64 Simulator, не App Store download size:

| Измерение | Значение |
|---|---:|
| Исходный .app до ORT/Silero | 6 099 779 байт |
| Проверенные Silero файлы | 220 189 054 байта |
| Resource folder вместе с manifest | 220 191 157 байт |
| Финальный .app | 258 257 230 байт |
| Первая загрузка моделей | 0.863 с |
| Footprint после первой загрузки | 329 616 672 байта |
| 34 генерации: время | 0.015–0.388 с |
| RTF min / median / max | 0.008 / 0.0125 / 0.029 |
| Максимальный наблюдаемый phys_footprint | 842 469 096 байт |

Крупнейшие ресурсы: homograph 117.11 МБ, spectral 58.29 МБ, encoder 14.20 МБ, decoder 11.56 МБ, accent 8.25 МБ, data.json 6.21 МБ. App executable с ORT около 32.93 МБ. Память — footprint процесса с WebView, не сумма только весов и не аппаратный high-water measurement. Она заметная и должна быть главным критерием проверки на телефоне. Симуляторные RTF нельзя переносить на iPhone.

В bundle ровно семь ONNX, один data.json и window.bin; hashes всех девяти файлов совпали. Нет .wav/.f32/.pt. Доказательства: `reports/production-integration/measurements.json`, `simulator.log`, `prebuffer.json`.

## Проверки

- `bash scripts/check.sh`: сборка, два WebKit smoke размера 390/320, все прежние Apple tests, новые EngineTests — PASS (65 строк PASS суммарно).
- Новые тесты: persistence/default, lazy prepare, оба направления switch, stale start/finish, Stop/Next во время generation, Pause/Resume, отсутствие повторного Play, ordering next buffer, end-of-topic, смена темы/фильтра, fallback на том же блоке, interruption/resume policy, memory pressure. Используют управляемый fake engine; реальный ORT/playback дополнительно проверен в Simulator.
- Финальная пересборка после защиты manifest — BUILD SUCCEEDED; установлена и запущена в Simulator.
- Повторные `audit_ios.py`, `audit_preprocessing.py`, `audit_technical.py` — PASS: 8 waveform cases, 25 preprocessing cases, 8 exact original tensor sets, 60 technical expectations/whitelist, 20 WAV. Это независимый повторный аудит сохранённых research captures, не новый прогон всего corpus через production engine. Исследовательские тесты сохранены, модели не переэкспортированы.
- Simulator: сначала Apple, затем Neural; тема 0.2 и техническая 10.1 (API, REST/gRPC, SQL/NoSQL, числа, метрики). Более пяти последовательных neural fragments, UI pause/resume, next/previous/stop, смена темы, возврат на Apple и повторное включение Neural — проверены. После блокировки экрана neural queue продолжала продвигаться; после разблокировки приложение показывало дальнейший блок. Дополнительно тема 10.5 с SLA/SLO/SLI, error budget/on-call/SRE в финальной сборке дошла до 11-го фрагмента, затем поставлена на паузу.
- Отдельная карточка Now Playing на lock screen этого Simulator не отобразилась; живые remote commands через карточку не подтверждены. Общая реализация и state transitions сохранены/проверены, но это остаётся явным пунктом физического теста, вместе с звонком/Siri/Bluetooth. Не считаем эти проверки выполненными на реальном устройстве.

## Файлы и воспроизведение

Изменены manager, processor, controls, Xcode project, scripts/check.sh, .gitignore, README, docs/AUDIO.md. Добавлены SpeechEngine/AppleSpeechEngine/SileroSpeechEngine, Audio/Silero (runtime/bridge/vendor), Tests/EngineTests.swift, Config/SileroResources.json, prep scripts, docs/SILERO_BUILD.md, этот отчёт и небольшие измерения. BookView, audio-reader.js и HTML curriculum не изменялись.

```sh
bash scripts/prepare_silero_models.sh
bash scripts/check.sh
open InteractiveBook.xcodeproj
```

Подготовка работает офлайн, сначала проверяет все SHA256/размеры, затем копирует canonical resource set; missing/hash mismatch — ошибка. Веса/словари в Git не включены. Новый clone без ранее полученных проверенных artifacts не может сам подготовить neural mode: канал распространения весов ещё не настроен. См. docs/SILERO_BUILD.md.

## Следующий этап

Сборка готова к установке через Xcode на физический iPhone. До признания её готовой для широкого использования нужны: память/thermal/RTF на целевом устройстве, 10–15 минут непрерывного чтения, качество темпа 0.8–2× на слух, lock screen/Now Playing remote controls, звонок/Siri и отключение Bluetooth. Нейросетевой звук субъективно не оценивался как «без потерь» в этом этапе: доказательства waveform parity относятся к сохранённым research captures. Оптимизация памяти и квантование не выполнялись.

Примечание к публикации исходников: упомянутые `reports/production-integration/` и simulator captures оставлены локально и исключены из Git. Измерения приведены в этом отчёте. Личная Team перенесена в игнорируемый `Config/Local.xcconfig`.
