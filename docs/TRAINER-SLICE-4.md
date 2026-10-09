# Slice 4 — профиль управленческого мышления

## Реализация

`TrainerScoringEngine.profile(history:)` — чистая функция. Вход: immutable `DiagnosticHistory`; выход: `TrainerProfile`, `scoringModelVersion = 1`. Профиль вычисляется при открытии экрана, не сохраняется как отдельная истина. Persistence schema остаётся v3; миграция не нужна. Текущий bundled bank не является входом scoring.

Новые production-файлы: `TrainerScoringEngine.swift`, `TrainerScoringMapping.swift`, `TrainerProfileView.swift` в `InteractiveBook/Trainer/`. `TrainerView.swift` добавляет вход в профиль внутри существующего нативного тренажёра. WebView, TTS и bridge в этом slice не меняются. Новые файлы включены в Xcode target.

## Scoring model v1

Учитывается только `cleanFirstAssessment` из завершённых диагностик. Дедупликация по testId: первая eligible диагностика по completedAt, затем startedAt и UUID для стабильного порядка. Training, mistakes, previouslyConfirmed, review и незавершённая диагностика не входят. Используются requiredLevel, domain, patterns и выбранный decisionQuality из snapshot. Неподдерживаемые уровни/ненумерические quality исключаются с видимым счётчиком; они не превращаются в ноль.

Score уровня/области = `sum(decisionQuality) / count * 100`. Частичный ответ 0.8 даёт 80%, независимо от isBest. Для каждого необходимого уровня минимум 5 разных eligible cases. Сравнения используют исходные числа, UI округляет проценты.

| Подтверждаемый уровень | Последовательные требования |
| --- | --- |
| Junior | Junior ≥78% |
| Middle | Junior ≥80%, Middle ≥72% |
| Senior | Junior ≥80%, Middle ≥75%, Senior ≥66% |
| Head | Junior ≥80%, Middle ≥75%, Senior ≥70%, Head ≥60% и breadth |

Проверки идут последовательно; сильный следующий bucket не заменяет провал предыдущего.

Confidence для отдельного bucket/domain/pattern: <5 — недостаточно данных, 5–9 — низкая, 10–14 — средняя, 15+ — высокая. Для общего уровня берётся **минимальное** количество среди необходимых buckets, а не сумма: 15 Junior не компенсируют 5 Senior. Если уровень не подтверждён, используется Junior bucket. Общее число eligible cases показано отдельно. Это консервативная конкретизация объёма «релевантных» данных.

`+`: база подтверждена, следующий bucket содержит ≥5 cases, его score в интервале `[основной threshold − 0.10, основной threshold)`. Недостаток breadth/предыдущего порога при уже пройденном основном threshold сам по себе плюс не создаёт. При <5 следующий bucket вообще не интерпретируется, включая плюс. Дополнительного порога confidence для перехода нет: минимум 5 уже установлен моделью.

Breadth Head: ≥5 агрегированных областей, в каждой ≥3 Senior/Head cases. Среди них обязательны People **или** Stakeholders и Portfolio & Strategy **или** Finance & Vendors. Число 3 — выбранная конкретизация неуказанного в задании «достаточно на область», вынесена в `headDomainEvidence`. Отсутствие ≥5 Head cases блокирует Head независимо от breadth.

## Области и мышление

Полный явный mapping находится в [TrainerScoringMapping.swift](../InteractiveBook/Trainer/TrainerScoringMapping.swift), вне SwiftUI; тест покрывает все metadata текущих 25 cases и отсутствие неоднозначных aliases. Неизвестные domain/pattern не угадываются и не добавляются в эти категории, но валидный ответ продолжает участвовать в уровне.

| UI-область | Metadata domain |
| --- | --- |
| Управление проектами | planning_and_dependencies, risk_management, uncertainty_and_external_dependencies |
| Delivery и релизы | release_and_quality, mobile_delivery, release_engineering |
| Процессы | delivery_quality, organizational_design |
| Стейкхолдеры | stakeholder_communication |
| Люди | people_management, incident_and_culture |
| Финансы и подрядчики | vendors_and_finance |
| Портфель и стратегия | program_and_portfolio, portfolio_management |
| Технический TPM | technical_delivery, reliability, incident_management |
| Аналитика | experimentation |
| Продукт | product_and_uncertainty |

В мышлении 10 категорий: контекстная чувствительность, риск, неопределённость, зависимости, приоритизация, доказательность, соразмерность, системное мышление, стейкхолдеры, организация. Например dependency-decoupling → зависимости, evidence-before-release → доказательность, blameless-system-thinking → системное мышление. Полные списки — в mapping-файле.

Вес primary = 1, secondary = 0.5. Aliases одной категории внутри кейса объединяются с максимальным весом. Затем веса кейса делятся на `max(1, sum(weights))`: суммарное влияние одного многотегового кейса не превышает 1. Итог категории = `sum(normalizedWeight * quality) / sum(normalizedWeight)`. Evidence count — число разных кейсов, не сумма весов. Топ-3 и нижние-3 без пересечения выводятся только для категорий с ≥5 cases; это относительные наблюдения, не сертификация.

Контекстная чувствительность не рассчитывается. `PairEvidence` переносит testId/revision/familyId/mutation/selectedOptionId для будущего анализа, не выводя фиктивную оценку.

## Проверки

`bash scripts/check.sh` выполняет новый `Tests/ScoringTests.swift` вместе с существующими Trainer, WebKit, TTS/engine, Saved, pronunciation и content checks; собирает iOS Simulator target.

Scoring tests: пороги и границы, последовательность, недостаток данных, плюс и его отсутствие, confidence 4/5/9/10/14/15, Head breadth и обязательные области, недостаток Head cases, частичный quality, eligibility, дедупликация, независимость snapshots от bank, domain averaging, мало данных, weighted patterns и aliases, отсутствие context score, версия модели. Store-интеграция: training/mistakes не меняют непустой профиль, незавершённый assessment исключён, restart воспроизводит профиль, full reset очищает его и после перезапуска.

`Tests/ScoringFixtures.swift` генерирует test-only v3 state files в игнорируемый `build/scoring-fixtures/`. Эти fixtures не входят в приложение/production bank.

Ручная приёмка 03.10.2026, iPhone 17 Pro Simulator iOS 26.3:

- Проверены empty state, недостаток данных (4 Junior), Junior, Junior+, Middle, Middle+, Senior.
- Проверены низкая/средняя/высокая confidence, до следующего уровня, Head без достаточных данных.
- Проверены область с одним кейсом и «мало данных», 3 сильных и 3 слабых паттерна, раскрытие всех наблюдений, длинный ScrollView.
- Сохранённая диагностика и её разбор открылись из snapshot; отдельный уровень диагностике не присваивается.
- Смешанная тренировка запущена, ответ подтверждён, подробный разбор открылся. Ошибка появилась в повторении; режим ошибок запущен с той же ситуацией.
- Повторная приёмка после разблокировки Mac завершена: неверный учебный ответ → работа над ошибками → верный ответ → итог «Исправлено: 1», «Осталось: 0». Профиль Middle и 10 чистых диагностических ситуаций не изменились. Отмена reset сохранила профиль; подтверждение reset очистило историю и показало пустой профиль.
- Возврат кнопкой «В учебник» проверен после reset: тема 10.8 и прежняя позиция прокрутки сохранены; screenshot до/после совпадает по позиции контента.

## Ограничения перед Slice 5

Текущий банк: Junior 1, Middle 10, Senior 12, Head 2. Он не позволяет подтвердить даже Junior при минимуме 5, а повторное прохождение не увеличит clean evidence. UI честно показывает недостаток данных; для проверки всех уровней использованы синтетические fixtures. Для реальной оценки нужен более сбалансированный банк.

Не добавлены paired-case UI, context-sensitivity score, adaptive testing, автоматический выбор учебных рекомендаций, перенос assessment mistakes, TTS, сервер или sync. Для Slice 5 нужно согласовать парную assessment-выборку и её интерпретацию. Mapping/thresholds v1 не являются валидированной психометрической моделью.

Финальный статус: полный повторный `bash scripts/check.sh` завершился с кодом 0, включая WebKit smoke 390×760, 320×568 и 1280×900, Trainer/Scoring, TTS/engine, Saved, pronunciation/content и Xcode build. Ручная приёмка завершена. Исходное состояние Simulator восстановлено из копии перед повторной приёмкой; `state.json` проверен побайтово через `cmp`. Production bank не изменён; синтетические данные удалены восстановлением исходного состояния. Изменения в GitHub не отправлялись. Лог проверки: `build/trainer-slice4-final-check.log` (ignored).
