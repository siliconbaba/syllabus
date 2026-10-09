# Trainer Content Schema 2.0

Контракт для TEST BANK и TEST QA. Версия контентного банка — строка `"2.0"`. Это **не** версия сохранений: trainer persistence остаётся schema 3. Банк офлайн, `InteractiveBook/TrainerContent/cases.json`; каталог — соседний `topics.json`.

## Root

| Поле | JSON-тип | Назначение |
| --- | --- | --- |
| schemaVersion | string, обязательно `"2.0"` | Формат контентного банка |
| source | string, optional | Название источника/учебника |
| cases | непустой array Case | Кейсы в редакторском порядке |

## Case

Поля обязательны, если не указано optional. Строки непустые после trim. Новые партии не должны содержать `difficulty` или case-level `mode`.

| Поле | Тип | Назначение / видимость |
| --- | --- | --- |
| id | string | Стабильный уникальный ID, например TC-026. Сервисное поле; не переиспользовать для другой ситуации |
| revision | positive integer | Редакция **конкретного кейса**, а не всего банка |
| type | string `single-best` | Формат выбора одного решения; сервисное |
| partId | string | Существующий section ID из каталога, например `part-2`; editorial/service |
| topicId | string | ID существующей темы, например `t-2-4`; topic.sectionID обязан равняться partId |
| title | string, optional/null | Непустое редакторское название, ориентир 3–8 слов, без ответа или подсказки; пока не показывается |
| sourceTopicExplanation | string | 1–3 предложения о конкретном положении соответствующей темы учебника. Только source/editorial metadata; не показывать в вопросе и не использовать в scoring |
| trainingEligible | boolean | Допуск в mixed, section/topic, mistakes и будущую учебную практику; service |
| assessmentEligible | boolean | Допуск в диагностический пул; дополнительно требуется unseen; service |
| domain | string | Предметная область; отображается через существующий mapping |
| requiredLevel | string | junior / middle / senior / head; сложность требуемого мышления, вход scoring, не статистическая difficulty |
| primaryPattern | string | Основной metadata-pattern; вход mapping мышления |
| secondaryPatterns | array string | Дополнительные patterns; без пустых строк; вход mapping |
| context | string | Ситуация, user-facing до ответа |
| question | string | Вопрос, user-facing до ответа |
| options | array Option, ровно 4 | Варианты в фиксированном авторском порядке |
| keyInsight | string | Главный вывод; user-facing в разборе |
| mentalModel | string | Модель мышления; user-facing в разборе |
| decisiveFacts | непустой array string | Существенные факты; user-facing в разборе |
| scenarioFamilyId | string, optional/null | ID семьи связанных ситуаций; metadata для будущей проверки пар |
| decisiveMutation | string, optional/null | Существенное изменение условия; редакторское описание, не отдельный экран |
| authorRationale | string | Авторское обоснование; редакторское поле, текущий UI не показывает |

Новые domain/pattern значения должны быть согласованы с `TrainerScoringMapping.swift`; автоматические mapping-тесты проверяют покрытие всех значений текущего банка. Самовольно подгонять metadata под существующий scoring нельзя.

### Negotiation vocabulary

Разрешённый runtime pattern `negotiation-batna` → **Stakeholder maturity** (`TrainerThinking.stakeholders`, UI «Работа со стейкхолдерами»).

Использовать, когда проверяется переговорное решение с учётом BATNA / reservation point, цены отсутствия соглашения и пространства обмена уступками. Сам факт переговоров недостаточен. Код не обозначает выбор fixed-price / T&M, эскалацию, полномочия или общую коммуникацию со стейкхолдерами; существующие codes для этих смыслов не меняются.

Разрешённый runtime pattern `interest-based-negotiation` → **Stakeholder maturity** (`TrainerThinking.stakeholders`). Он обозначает выявление интересов сторон, взаимовыгодный обмен и пакетирование условий вместо позиционного торга по одному параметру. В отличие от него, `negotiation-batna` обозначает альтернативу соглашению, reservation point и цену несоглашения. Общая категория мышления не делает эти codes взаимозаменяемыми.

Авторитетный vocabulary — исходный `InteractiveBook/Trainer/TrainerScoringMapping.swift`. Доступные TEST BANK / TEST QA reference-копии mapping и engine с SHA-256: [`agent-artifacts/runtime-contract/`](../agent-artifacts/runtime-contract/README.md). Копии генерируются из Swift-файлов, не редактируются вручную. Неизвестный pattern по-прежнему возвращает nil в mapping; coverage-тест банка требует известных codes. Никакие manifest-строки этой задачей не изменяются.

## Option

| Поле | Тип | Назначение |
| --- | --- | --- |
| id | string | A/B/C/D, уникальны внутри кейса; identity ответа и ссылка из snapshot |
| text | string | Текст решения до подтверждения |
| decisionQuality | number 0…1 | Частичный вклад решения в scoring; не заменять бинарным isBest |
| isBest | boolean | Ровно один true в кейсе |
| reasoningPattern | string | Паттерн выбранного рассуждения, metadata; не подменяет case-level primaryPattern |
| failurePattern | string, optional/null | Непустой код ошибки рассуждения, если применим |
| explanation | string | Объяснение решения после подтверждения / в итоговом разборе |
| whyTempting | string | Почему вариант привлекателен, в разборе |
| whyNotBest | string | Что упускает вариант, в разборе |
| whenItWouldBeBest | string | В каких условиях вариант уместен, в разборе |

Все обязательные строки Option непустые, включая explanation-поля лучшего варианта: если ограничение неприменимо, это объясняется текстом. Option ordering не перемешивается этой схемой или миграцией.

## Eligibility и revisions

Eligibility — допуск к **новой** сессии, не вес ответа и не оценка качества кейса. Возможны training-only или assessment-only кейсы. Training selection фильтрует `trainingEligible`; diagnostic selection — `assessmentEligible && unseen`. Подтверждённая учебная встреча по-прежнему исключает чистую диагностическую встречу. Флаги не заменяют encounter logic.

Уже начатая сессия продолжает собственный snapshot, даже если текущая редакция банка изменила flags. Старые диагностики и профиль рассчитываются по immutable snapshots; текущие flags банка не исключают старую историю задним числом. ScoringModel v1 и thresholds не изменены.

Revision относится к кейсу: смешанные revisions в одном банке корректны. При миграции gold-standard в schema 2.0 revisions не увеличивались: TC-011/020 — 4, остальные 23 — 3. Последующие содержательные редакции одного кейса увеличивают его revision; изменение root schemaVersion само по себе не выравнивает revisions.

## Scenario families

Оба поля scenarioFamilyId/decisiveMutation либо отсутствуют/null вместе, либо оба непустые. В полном production bank семья содержит минимум два кейса одной темы с разными decisiveMutation. Это варианты общей ситуации с существенным изменением условия, а не дубликаты. Не менять ID семьи для косметической редакции.

Текущие семьи: TC-001/002, TC-003/004, TC-017/018. Ни paired-case UI, ни context-sensitivity score схема не вводит.

## Строгая загрузка и совместимость

Production entry point — `TrainerBank.load(url:)`: принимает только schemaVersion `"2.0"`, включает строгий decoder, читает соседний каталог и валидирует банк. Отсутствие/null partId, sourceTopicExplanation или любого eligibility — ошибка; пустое обязательное metadata, неизвестные topic/part или несовпадение принадлежности также ошибка. Title можно не передавать, но переданная строка должна быть непустой. Число вариантов, ID A/B/C/D, isBest, quality и согласованность семей проверяются дополнительно.

Старые snapshots декодируются отдельно, без проверки по **текущему** каталогу или банку. Если новых полей нет: partId = `""` (legacy fallback без догадок), title = nil, sourceTopicExplanation = `""`, оба eligibility = true. Неверный JSON-тип существующего поля не заменяется default. Старые поля и их semantics не изменяются. Открытие сохранений schema 3 не вызывает их перезапись или новую миграцию; последующее штатное сохранение может сериализовать совместимые defaults, сохраняя исходное содержание snapshot.

`load(url:allowLegacy:true)` предназначен для архивных v1 fixtures; production UI его не использует. `TrainerBank.validate(cases)` — совместимая проверка snapshots, а не замена строгой production-загрузки. Новые партии необходимо проверять через production entry point.

## Источник metadata и контроль gold-standard

partId заполнен из `topics.json` через topic.sectionID. Source explanations составлены по тексту соответствующих тем `InteractiveBook/WebContent/index.html`: планирование, риски, релизы и качество, API, зависимости, управление командами, неопределённость, коммуникации, performance, подрядчики, портфель, SLO, инциденты и эксперименты. Это краткий пересказ конкретных положений, а не новый набор правил. При конфликте с источником кейс не исправляется автоматически: требуется редакторское решение.

Эталон до миграции: `Tests/Fixtures/trainer-gold-v1.json`, SHA-256:
`363e16f4f6dcd4f50f7b09fd6b55e9c4018c69a4d3671bd61e812ca031b43f51`.

`Tests/TrainerSchemaTests.swift` удаляет только пять добавленных полей, возвращает root schemaVersion к 1.0 и сравнивает **весь** JSON с этим эталоном, включая массивы и порядок вариантов. Новые разрешённые партии потребуют осознанного обновления проверки эталонных кейсов; не обновлять fixture только ради прохождения теста.

Проверки: `bash scripts/check.sh`. Включены строгая загрузка v2, обязательные поля, связи каталога, eligibility всех режимов, legacy Attempt/DiagnosticHistory, review/profile, отсутствие переписывания сохранений при загрузке, неизменность старого контента, обе eligibility=true у текущих 25. `build_trainer_catalog.py --check` сверяет каталог с реальным оглавлением и принадлежность каждого case.
