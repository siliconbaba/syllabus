# TechnicalSpeechNormalizer: технический текст перед Silero

2026-09-25. **60/60 regression cases, 60/60 whitelist checks, 20/20 аудиопримеров.**

Добавлен отдельный opt-in слой: visible textbook text → TechnicalSpeechNormalizer → существующий SileroPreprocessor → существующие ONNX models/DSP → waveform. Исходный текст учебника не изменяется. Production-аудиочиталка и Apple TTS не изменены; публикации в GitHub нет.

## Архитектура и переиспользование

`TechnicalLexicon.swift` содержит только дополнительные термины. `TechnicalNumbers.swift` преобразует числа и согласует поддержанные единицы. `TechnicalSpeechNormalizer.swift` задаёт порядок правил, границы терминов, fallback и проверку выходного алфавита. `TechnicalHarness.swift` проверяет product corpus и синтезирует выбранные примеры.

Изучен `InteractiveBook/Audio/SpeechTextProcessor.swift`: в нём **23 произношения**, longest-match и case-insensitive boundary matching, удаление URL, свёртка пробелов, sentence splitting и block-dependent pauses. Числа/неизвестная латиница не преобразуются — остаются для системного Apple TTS.

Исследовательский target компилирует тот же production Swift-файл по ссылке и **только читает** `SpeechTextProcessor.pronunciations`. Файл не редактируется, его normalize/fragments не вызываются. Словарь не продублирован. Переиспользованы pronunciation values и принцип longest match с границами слова; перед case-insensitive lookup выполняется exact-key lookup. Добавлено **82 записи**, всего **105**.

URL deletion — политика существующей читалки, не обязательное свойство Apple TTS; в новый слой не перенесена, чтобы не терять адреса. Разбиение блоков, паузы и Apple delivery остаются вне normalizer. Для будущего shared layer достаточно вынести исходный pronunciation dictionary в общий модуль и оставить engine-specific numbers/unsupported-character policy отдельно. Сейчас такой production-рефакторинг не выполнялся.

Доказанные `SileroTextRules.swift`, `SileroAuxiliary.swift`, `SileroPreprocessor.swift` не изменены. Из research FixtureHarness выделен существующий код вычисления в общий `synthesize(prepared:)`, без изменения duration/pitch/FFT математики, чтобы не копировать synthesis pipeline для технических фраз. После этого повторно прошли 25/25 старых preprocessing cases и 8/8 waveforms; waveforms побитово совпали с прежним fixture-only результатом.

## Правила

- Известные словосочетания и сокращения обрабатываются целиком: CI/CD, Docker Compose, go/no-go, Lead time, merge request. Не читается slash внутри CI/CD.
- Все запрошенные abbreviations/technology names покрыты словарём и regression corpus. PostgreSQL → «постгрес», SQL → «эс кью эль», Kafka → «кафка» наследуются из production.
- Неизвестный ASCII Latin token читается по английским буквам русскими названиями. `XQZ` → «экс кью зед»; `myAPI` не заменяется как отдельный API и полностью читается буквами. ML-транслитерации и сети нет.
- Целые числа до 999999999999999 читаются группами тысяч/миллионов/миллиардов/триллионов. Более длинные числа и leading-zero IDs читаются по цифрам, без усечения.
- Десятичные числа с точкой/запятой: целые и десятые/сотые/.../миллионные, до 6 fractional digits. Более длинная дробная часть читается через «точка» с сохранением цифр. Это не локализованный parser всех финансовых форматов.
- Проценты согласуются: один процент, два процента, одиннадцать процентов; дробные — процента. Для `с/до/от` реализован родительный падеж: «с двенадцати целых пяти десятых процента до четырнадцати процентов».
- Годы с год/года/году читаются составным порядковым числительным: «две тысячи двадцать шестой/шестого/шестом». Последняя ordinal-компонента поддержана для 1000–2999; большие и специальные формы не гарантированы.
- `v2`, `v2.3`, версии после PostgreSQL/Postgres/iOS/Java/Python/Kotlin/Swift/Kubernetes/Docker/версия/версии обрабатываются до decimals. «Версия v2» не даёт двойного слова «версия». Три и более dot-separated numeric components читаются через «точка».
- Поддержаны минуты/секунды, мс, KB/MB/GB/TB, RAM, CPU, RPS, TPS. Числа и склонение: «двести миллисекунд», «два процессора», «пятьсот запросов в секунду», «четыре гигабайта оперативной памяти». Обработан и формат 2GB без пробела.
- Числовой минус/отрицательные значения, плюс, равно, процент, умножение, стрелка; slash вне словаря читается «слэш», & → «и», @ → «собака», # → «номер». Дефис внутри слова остаётся дефисом, тире сохраняет паузу. Готовый русский stress marker, например з+амок, сохраняется; новые ударения не добавляются.
- Кавычки снимаются, скобки превращаются в паузы; это форматирование speech copy. Русские слова, ё и punctuation сохраняются; question classification/омографы/ударения остаются в Silero.
- Неподдержанный выходной glyph вызывает явную ошибку вместо молчаливого удаления. В тестируемых случаях выход полностью состоит из символов штатной whitelist.

Порядок семейств преобразований: версии → словарь → минус/плюс → годы → проценты → единицы/время → составные numeric versions → остальные числа → неизвестная латиница → symbols/spacing → проверка алфавита. 105 словарных записей — отдельные декларативные правила; указанные семейства задают контекстную обработку.

## Проверки и производительность

Expected speakable strings написаны отдельно в `technical-corpus.json`; тест не генерирует ожидания из normalizer. Есть API/integration, delivery, DevOps, databases, product, reliability, numbers/units/versions, symbols, fallback, русский текст, boundaries и case variants.

Все **60 строк exact-equal expected**. Для каждой отдельно выполнено `SileroNormalizer.normalize(output) == output.lowercased()`: **60/60**, то есть ничего кроме ожидаемого lowercase не исчезает. Проверяется отсутствие ASCII Latin/digits в output. Русский контрольный пример «Ёжик ждёт: всё ещё хорошо? Да!» остаётся неизменным.

Native Swift tests и iOS Simulator tests проходят. Independent Python audit сверяет JSON с authored corpus, waveform size/finite/non-silence, PCM16 WAV bytes и hashes старых synthesis/auxiliary models/golden. Новых моделей, весов, network dependencies нет.

Технические timings iPhone17Pro Simulator на Apple Silicon, один прогон, не прогноз физического iPhone:

- Одна строка: median **1.003 ms**, min 0.803, max 1.827.
- Тема из 2044 символов: median **12.005 ms** за 5 прогонов; измеряется только string processing.

## Аудиопримеры и интерфейс

В SileroIOSPoC добавлены кнопка «Технические примеры» и список с исходной и произносимой строкой. Выбор строки запускает WAV через AVAudioPlayer. `--technical` открывает этот режим сразу; без аргумента по-прежнему запускается original-compatible preprocessing, `--fixtures-only` сохраняет прежний numerical baseline. Кнопка Raw text → waveform позволяет вернуться к parity-проверке.

Синтез начинается только после text/whitelist pass. Созданы 20 float32 waveform и WAV mono48k PCM16, суммарно около 60 секунд; finite/non-silent, длина 600×frames, клиппированных samples нет. Это product audio, поэтому сравнение с прежним raw-Silero waveform было бы некорректно: pronounceable text намеренно изменён.

Проверены UI и запуск Play для API/HTTP и Debezium/CDC/Kafka; AVAudioPlayer вернул true и isPlaying=true (proof JSON в reports/technical). **Субъективная оценка естественности всех 20 записей не заявляется**: они подготовлены для ручного прослушивания пользователем.

| ID | Исходная фраза | WAV |
|---|---|---|
| tech_01 | API вернул HTTP 500. | [слушать](artifacts/technical/ios-results/tech_01.wav) |
| tech_02 | REST API использует JSON. | [слушать](artifacts/technical/ios-results/tech_02.wav) |
| tech_03 | Запрос завершился по таймауту через 30 секунд. | [слушать](artifacts/technical/ios-results/tech_03.wav) |
| tech_04 | Перед релизом проводится go/no-go. | [слушать](artifacts/technical/ios-results/tech_04.wav) |
| tech_05 | Lead time снизился на 15%. | [слушать](artifacts/technical/ios-results/tech_05.wav) |
| tech_06 | Команда отслеживает DORA-метрики. | [слушать](artifacts/technical/ios-results/tech_06.wav) |
| tech_07 | CI/CD pipeline запускается после merge request. | [слушать](artifacts/technical/ios-results/tech_07.wav) |
| tech_08 | Docker-контейнер работает в Kubernetes. | [слушать](artifacts/technical/ios-results/tech_08.wav) |
| tech_09 | PostgreSQL 16 используется как основная OLTP база. | [слушать](artifacts/technical/ios-results/tech_09.wav) |
| tech_10 | Debezium читает WAL и публикует CDC-события в Kafka. | [слушать](artifacts/technical/ios-results/tech_10.wav) |
| tech_11 | Conversion вырос с 12.5% до 14%. | [слушать](artifacts/technical/ios-results/tech_11.wav) |
| tech_12 | MAU составляет 500000 пользователей. | [слушать](artifacts/technical/ios-results/tech_12.wav) |
| tech_13 | SLA составляет 99.95%. | [слушать](artifacts/technical/ios-results/tech_13.wav) |
| tech_14 | RTO — 15 минут, RPO — 5 минут. | [слушать](artifacts/technical/ios-results/tech_14.wav) |
| tech_15 | Java 21 использует 4 GB RAM. | [слушать](artifacts/technical/ios-results/tech_15.wav) |
| tech_16 | Сервис обрабатывает 500 RPS. | [слушать](artifacts/technical/ios-results/tech_16.wav) |
| tech_17 | iOS 26 использует API версии 2.3. | [слушать](artifacts/technical/ios-results/tech_17.wav) |
| tech_18 | Задержка составляет 200 мс. | [слушать](artifacts/technical/ios-results/tech_18.wav) |
| tech_19 | Доступность равна 99.9%. | [слушать](artifacts/technical/ios-results/tech_19.wav) |
| tech_20 | Версия v2 использует HTTPS. | [слушать](artifacts/technical/ios-results/tech_20.wav) |

## Произношения для ручного выбора

Приняты единообразные варианты, но в IT-командах встречаются другие: SQL «эс кью эль»/«сиквел»; PostgreSQL «постгрес»/полное название; Python «пайтон»/«питон»; OAuth «оу аут»/другие варианты; IAM «ай эм»/побуквенно; Kubernetes «кубернетес»; nginx «энджин икс»; Debezium «дебезиум»; Prometheus «прометеус». Словарь не добавляет brand-specific ударения — их назначает неизменённый Silero, поэтому прослушивание названий особенно важно. Для DORA, CI/CD и SLA также полезно подтвердить привычный для пользователя вариант.

## Known limitations и готовность к production

- Это не полноценный русский morphological engine. Помимо явно поддержанных годов/единиц/процентов, падежи чисел в произвольной фразе не вычисляются. Русское окружение не редактируется: например исходное «Conversion вырос» станет «конверсия вырос», а не автоматически «выросла».
- Нет универсального parser дат, диапазонов, телефонов, научной записи, валют, кодовых блоков, URL/IP semantics и группированных пробелами чисел. URL сохраняется как произносимая последовательность, но может звучать длинно и с паузами на точках. Дефис между цифрами интерпретируется как минус, а не диапазон.
- MB/GB — bytes; различение битовых Mb/Gb и binary MiB/GiB не реализовано. Словарный case-insensitive fallback не подходит как полная спецификация единиц.
- Fallback spelling сохраняет ASCII letters, но не их регистр; латиница с диакритикой и прочие неподдержанные glyphs приводят к явной ошибке. Emoji/математическая запись вне покрытых правил требуют будущей политики, а не silent deletion.
- Plain text baseline Silero сохраняет прежние ограничения и ошибки ударений/омографов. Naturalness не следует автоматически из exact expected-string equality.

**Готов для исследовательского прослушивания и дальнейшей интеграционной работы, но production-подключение пока не выполнено и не одобрено этим тестом.** Следующий шаг по качеству текста — прослушать 20 записей, согласовать спорные pronunciation variants и добавить реальные непокрытые фрагменты учебника в regression corpus. Production integration — отдельная задача после этого; physical-device benchmark здесь не выполнялся.

## Воспроизведение

Из `experiments/silero-ios-feasibility/` с готовыми artifacts предыдущих этапов:

```sh
bash ios/test_technical_text.sh
bash ios/run_technical.sh "$SIMULATOR_ID"
# После Текст: 60/60; аудио: 20/20 выбрать записи для прослушивания.
bash ios/collect_technical.sh "$SIMULATOR_ID"
```

Подставить UUID своего Simulator. run_technical использует существующий сборочный script, копирует отдельный technical-corpus.json, не меняет golden. Итоговые данные: `reports/technical/simulator-report.json`, `independent-audit.json`, `playback-api.json`, `playback-debezium.json`. Полные audio artifacts — `artifacts/technical/ios-results/`. WAV/модели/build остаются ignored.

Производственные файлы, deps и основной UI не менялись. Старые локальные две строки DEVELOPMENT_TEAM в production project, существовавшие до исследования, сохранены. Изменения в GitHub не отправлялись.

## Все expected speakable strings

| ID | Категория | Source | Expected |
|---|---|---|---|
| tech_01 | api | API вернул HTTP 500. | эй пи ай вернул эйч ти ти пи пятьсот. |
| tech_02 | api | REST API использует JSON. | рэст эй пи ай использует джейсон. |
| tech_03 | api | Запрос завершился по таймауту через 30 секунд. | Запрос завершился по таймауту через тридцать секунд. |
| tech_04 | delivery | Перед релизом проводится go/no-go. | Перед релизом проводится гоу ноу гоу. |
| tech_05 | delivery | Lead time снизился на 15%. | лид тайм снизился на пятнадцать процентов. |
| tech_06 | delivery | Команда отслеживает DORA-метрики. | Команда отслеживает дора-метрики. |
| tech_07 | devops | CI/CD pipeline запускается после merge request. | си ай си ди пайплайн запускается после мёрдж реквест. |
| tech_08 | devops | Docker-контейнер работает в Kubernetes. | докер-контейнер работает в кубернетес. |
| tech_09 | database | PostgreSQL 16 используется как основная OLTP база. | постгрес шестнадцать используется как основная оу эл ти пи база. |
| tech_10 | database | Debezium читает WAL и публикует CDC-события в Kafka. | дебезиум читает вал и публикует си ди си-события в кафка. |
| tech_11 | product | Conversion вырос с 12.5% до 14%. | конверсия вырос с двенадцати целых пяти десятых процента до четырнадцати процентов. |
| tech_12 | product | MAU составляет 500000 пользователей. | эм эй ю составляет пятьсот тысяч пользователей. |
| tech_13 | reliability | SLA составляет 99.95%. | эс эл эй составляет девяносто девять целых девяносто пять сотых процента. |
| tech_14 | reliability | RTO — 15 минут, RPO — 5 минут. | ар ти оу – пятнадцать минут, ар пи оу – пять минут. |
| tech_15 | version | Java 21 использует 4 GB RAM. | джава двадцать один использует четыре гигабайта оперативной памяти. |
| tech_16 | units | Сервис обрабатывает 500 RPS. | Сервис обрабатывает пятьсот запросов в секунду. |
| tech_17 | version | iOS 26 использует API версии 2.3. | ай оу эс двадцать шесть использует эй пи ай версии два точка три. |
| tech_18 | units | Задержка составляет 200 мс. | Задержка составляет двести миллисекунд. |
| tech_19 | percent | Доступность равна 99.9%. | Доступность равна девяносто девять целых девять десятых процента. |
| tech_20 | version | Версия v2 использует HTTPS. | Версия два использует эйч ти ти пи эс. |
| tech_21 | api | TCP и IP используют URL и URI. | ти си пи и ай пи используют ю ар эл и ю ар ай. |
| tech_22 | api | XML и YAML отличаются от JSON. | икс эм эль и ямл отличаются от джейсон. |
| tech_23 | product | UI и UX влияют на KPI и OKR. | ю ай и ю икс влияют на кей пи ай и оу кей ар. |
| tech_24 | product | MVP проверяет A/B гипотезу для B2B и B2C. | эм ви пи проверяет эй би гипотезу для би ту би и би ту си. |
| tech_25 | api | CRM и ERP используют IAM, SSO и OAuth. | си ар эм и и ар пи используют ай эм, эс эс оу и оу аут. |
| tech_26 | api | JWT проверяется через SDK, CLI и IDE. | джей дабл ю ти проверяется через эс ди кей, си эл ай и ай ди и. |
| tech_27 | database | JVM читает DB через DBMS, ETL и ELT. | джей ви эм читает ди би через ди би эм эс, и ти эл и и эл ти. |
| tech_28 | database | NoSQL и OLAP дополняют SQL. | ноу эс кью эль и олап дополняют эс кью эль. |
| tech_29 | reliability | QA, DevOps и SRE отслеживают SLO и SLI. | кью эй, девопс и эс ар и отслеживают эс эл оу и эс эл ай. |
| tech_30 | devops | CI готовит сборку, CD выполняет deploy. | си ай готовит сборку, си ди выполняет деплой. |
| tech_31 | devops | Docker Compose работает с OpenShift. | докер компоуз работает с оупен шифт. |
| tech_32 | devops | Git, GitLab и GitHub хранят commit. | гит, гитлаб и гитхаб хранят коммит. |
| tech_33 | technology | Kotlin, Swift и Python доступны команде. | котлин, свифт и пайтон доступны команде. |
| tech_34 | technology | JavaScript и TypeScript используются с React. | джаваскрипт и тайпскрипт используются с реакт. |
| tech_35 | database | Redis, MongoDB и Oracle дополняют Postgres. | редис, монго ди би и оракл дополняют постгрес. |
| tech_36 | technology | Linux и nginx передают данные в Grafana и Prometheus. | линукс и энджин икс передают данные в графана и прометеус. |
| tech_37 | technology | Jira, Confluence и Jenkins связаны с RabbitMQ. | джира, конфлюенс и дженкинс связаны с рэббит эм кью. |
| tech_38 | units | Файлы занимают 10 MB, 2 GB и 512 KB. | Файлы занимают десять мегабайт, два гигабайта и пятьсот двенадцать килобайт. |
| tech_39 | units | Нужны 2 CPU и 16 GB RAM. | Нужны два процессора и шестнадцать гигабайт оперативной памяти. |
| tech_40 | units | Нагрузка составляет 100 RPS и 500 TPS. | Нагрузка составляет сто запросов в секунду и пятьсот транзакций в секунду. |
| tech_41 | decimal | Коэффициенты равны 1.5 и 0.95. | Коэффициенты равны одна целая пять десятых и ноль целых девяносто пять сотых. |
| tech_42 | year | 2026 год станет важным. | две тысячи двадцать шестой год станет важным. |
| tech_43 | year | В 2026 году завершится проект. | В две тысячи двадцать шестом году завершится проект. |
| tech_44 | year | До 2026 года план не меняется. | До две тысячи двадцать шестого года план не меняется. |
| tech_45 | symbols | 5+2=7, а 5-2=3. | пять плюс два равно семь, а пять минус два равно три. |
| tech_46 | symbols | 2 × 3 → 6. | два умножить на три переходит в шесть. |
| tech_47 | symbols | QA & DevOps проверяют #42 и @team. | кью эй и девопс проверяют номер сорок два и собака ти и эй эм. |
| tech_48 | fallback | XQZ и frobnicate требуют проверки. | экс кью зед и эф ар оу би эн ай си эй ти и требуют проверки. |
| tech_49 | symbols | Вариант чтение/запись остаётся. | Вариант чтение слэш запись остаётся. |
| tech_50 | russian | Ёжик ждёт: всё ещё хорошо? Да! | Ёжик ждёт: всё ещё хорошо? Да! |
| tech_51 | version | Python 3.12 и версия 2.3 совместимы. | пайтон три точка двенадцать и версия два точка три совместимы. |
| tech_52 | units | Буфер занимает 2GB и 1.5 MB. | Буфер занимает два гигабайта и одна целая пять десятых мегабайта. |
| tech_53 | number | Ошибки 001 и 1000000 различаются. | Ошибки ноль ноль один и один миллион различаются. |
| tech_54 | percent | Значения составляют 1%, 2% и 11%. | Значения составляют один процент, два процента и одиннадцать процентов. |
| tech_55 | negative | Изменение равно -5%. | Изменение равно минус пять процентов. |
| tech_56 | url | Адрес https://example.com/v2 содержит путь. | Адрес эйч ти ти пи эс: слэш слэш и экс эй эм пи эл и.си оу эм слэш версия два содержит путь. |
| tech_57 | units | Ожидание: 1 минута, 2 секунды и 1 мс. | Ожидание: одна минута, две секунды и одна миллисекунда. |
| tech_58 | case | api, Api и API работают одинаково. | эй пи ай, эй пи ай и эй пи ай работают одинаково. |
| tech_59 | boundaries | myAPI не равно API. | эм уай эй пи ай не равно эй пи ай. |
| tech_60 | stress | Слово з+амок уже содержит ударение. | Слово з+амок уже содержит ударение. |
