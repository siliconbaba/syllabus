# Surgical manifest candidate v2.2.4

**Candidate only — NOT FROZEN, NOT IMPORTED. Full cases: 0.**

Baseline: `v2.2.3/production_manifest_masterplan_v2_2_3.json`, SHA-256 `a6b51ec3f9a3c2dbf4546c3d457b67b0fe5b3ed62602bdc09817191fb3164db1`. Production: TC-001…TC-100, SHA-256 `6becf4f8ccdb914e9ebd51ca780902174ecdd7914824408139b40477cd25c6a3`. Source and context-pack hashes PASS.

Original preflight: NO CLOSE ANALOG 3 / ALLOWED REINFORCEMENT 11 / NEAR DUPLICATE 5 / DUPLICATE 6. Принят без reclassification; полного повторного preflight 25 строк не проводилось.

## Scope объявлен до редактирования

- Direct blocker rows: TC-103, TC-105, TC-108, TC-111, TC-113, TC-115, TC-118, TC-119, TC-120, TC-122, TC-125
- Additional required siblings: TC-101, TC-102, TC-104, TC-109
- Allowed family contracts: F-TD-T01, F-PM-P01, F-PA-P02
- Changed: 15 rows / 3 families. Unchanged: 260 rows / 40 families. Unexpected changes: 0 / 0.

Соседи TC-101/102, TC-104 и TC-109 включены потому, что смена диагностической оси TC-103, TC-105 и TC-108 требует общего base situation, strategy space и одной mutation у всей семьи. Простая замена только blocked member разрушила бы controlled contrast.

## Разрешение 11 blockers

Полный исходный verdict и четыре оси различия: `original-blocker-resolution.json`. Exact source excerpts, операционализация и why lower-level reasoning is insufficient: `source-and-level-evidence.json`.

### TC-103 / TC-010 / DUPLICATE

Production analog tests: Новые записи не читаются старым кодом, обратная миграция слишком долгая. Expand-contract перед включением. Обратимость состояния после релиза.

Old planned row tested: Сначала переделать миграцию в expand-contract, и только потом включать новое поведение.

New planned row tests: Отказаться от непосредственного shadow и перенести замену: сначала отделить вычисление от внешних эффектов архитектурно; один флаг скрытия результата не делает двойное выполнение безопасным.

Different decisive fact: Новые записи не читаются старым кодом, обратная миграция слишком долгая. → Внешние эффекты shadow обходят изолируемую границу; миграции данных нет.

Different candidate mistake: Считать флаг достаточным возвратом данных. → Считать скрытый вывод доказательством отсутствия внешнего эффекта.

Different actual decision: Expand-contract перед включением. → Архитектурно отделить side effects перед shadow и перенести замену.

Different strongest reasoning: Обратимость состояния после релиза. → Безопасность параллельного выполнения до пользовательского включения.

### TC-105 / TC-006 / DUPLICATE

Production analog tests: Официальный trigger уже наступил. Активировать contingency и вести issue. Режим управления определяется фактом события.

Old planned row tested: Управлять уже возникшей проблемой, активировать response plan и обновить последствия/остаточные риски.

New planned row tests: Перенести trigger подготовки на 7-дневный индикатор: 3 дня не покрывают 5 дней response; ждать позднего подтверждения уже слишком поздно.

Different decisive fact: Официальный trigger уже наступил. → Событие ещё не наступило, response занимает 5 дней при позднем сигнале за 3.

Different candidate mistake: Продолжать обсуждать вероятность факта. → Выбрать достоверный, но слишком поздний сигнал подготовки.

Different actual decision: Активировать contingency и вести issue. → Перенести подготовку на ранний 7-дневный индикатор.

Different strongest reasoning: Режим управления определяется фактом события. → Trigger должен оставлять время для исполнения response.

### TC-108 / TC-044 / NEAR DUPLICATE

Production analog tests: Есть нелокализованная деградация и дорогой rollback. Сначала локализовать причину. Качество причинного сигнала ограничивает вмешательство.

Old planned row tested: Сначала расширить диагностику и локализовать источник.

New planned row tests: Хранить каждый сотый экземпляр с полным счётчиком: 100 000 примеров сохраняют диагностический минимум, а полный поток около 10 ГБ нарушает лимит.

Different decisive fact: Есть нелокализованная деградация и дорогой rollback. → Нет решения об инциденте; известны поток 10 млн, 1 КБ, лимит 1 ГБ и минимум примеров.

Different candidate mistake: Выбрать вмешательство по агрегату. → Хранить каждый пример, игнорируя ограниченное хранение.

Different actual decision: Сначала локализовать причину. → Сэмплировать подробности, сохранив счётчик и достаточный набор примеров.

Different strongest reasoning: Качество причинного сигнала ограничивает вмешательство. → Одновременно соблюсти диагностическую достаточность и ресурсный лимит.

### TC-111 / TC-040 / NEAR DUPLICATE

Production analog tests: Конфликт KPI/вето повторяется при имеющемся мандате на постоянные права. Закрепить критерии, владельца решения и veto. Постоянный механизм разрешает повторяемый конфликт.

Old planned row tested: Больше координации поверх прежних incentives ↔ изменить governance и decision rights.

New planned row tests: Не финансировать немедленное масштабирование LeSS при невыполненной бюджетной предпосылке: разделить инвестицию на продуктовый бюджет/мандат PO и последующий переход, сохранив временную координацию до выполнения условия.

Different decisive fact: Конфликт KPI/вето повторяется при имеющемся мандате на постоянные права. → Бюджеты департаментов делают единый PO нереализуемым до решения CFO.

Different candidate mistake: Повторять двусторонние согласования вместо постоянных правил. → Инвестировать в LeSS до появления структурной предпосылки.

Different actual decision: Закрепить критерии, владельца решения и veto. → Разнести бюджетную реформу и инвестицию в rollout фреймворка по этапам.

Different strongest reasoning: Постоянный механизм разрешает повторяемый конфликт. → Порядок институциональных инвестиций определяется бюджетной реализуемостью, а не брендом.

### TC-113 / TC-081 / DUPLICATE

Production analog tests: Причина желания уйти не установлена, доступен рост автономии. Диагностический разговор. Сначала найти драйвер.

Old planned row tested: Деньги как универсальная мотивация ↔ диагностика автономии, мастерства и смысла.

New planned row tests: Поддержать переход с ограниченной передачей обязательств вместо контроффера и обещания недоступного роста; согласовать владельцев текущей работы, не удерживать человека до неопределённой замены.

Different decisive fact: Причина желания уйти не установлена, доступен рост автономии. → Потолок и готовность подтверждены; внутри scope нет, принимающая команда есть.

Different candidate mistake: Прописать мотивационное средство до диагноза. → Удерживать любой ценой обещанием недоступной карьеры.

Different actual decision: Диагностический разговор. → Поддержать переход с ограниченным handover.

Different strongest reasoning: Сначала найти драйвер. → Удовлетворить уже известную потребность без ложного обещания и потери текущих обязательств.

### TC-115 / TC-023 / DUPLICATE

Production analog tests: Несогласованные prod changes и нет IC. Назначить IC, роли, change control. Управляемость реагирования предшествует вмешательствам.

Old planned row tested: Сразу искать root cause ↔ сначала установить command, роли и контроль изменений.

New planned row tests: Выбрать 18-минутное восстановление без потерь: оно соблюдает и RTO, и RPO; самый быстрый подъём сервиса не является допустимым восстановлением при превышении потери данных.

Different decisive fact: Несогласованные prod changes и нет IC. → Командование организовано; два проверенных recovery пути различаются потерей данных и временем.

Different candidate mistake: Продолжать технические действия без единого управления. → Считать минимальный простой единственной мерой восстановления.

Different actual decision: Назначить IC, роли, change control. → Выбрать более медленный путь, выполняющий одновременно RPO и RTO.

Different strongest reasoning: Управляемость реагирования предшествует вмешательствам. → Допустимость recovery — пересечение независимых ограничений, не минимум одной метрики.

### TC-118 / TC-025 / NEAR DUPLICATE

Production analog tests: Ключевой спрос неизвестен, дешёвый behavioral test доступен. Купить дешёвое поведенческое свидетельство. Ценность информации до инвестиции.

Old planned row tested: Формула как окончательное решение ↔ использовать framework как вход и отдельно уменьшать ключевую uncertainty.

New planned row tests: Переразбить инициативу на самостоятельно ценные вертикали, включив общий prerequisite в первую, и пересчитать WSJF/стоимость вытеснения; не повышать ранг фиктивным дроблением технических слоёв.

Different decisive fact: Ключевой спрос неизвестен, дешёвый behavioral test доступен. → Спрос подтверждён; монолитный scope теряет ранг, технические куски не имеют самостоятельной ценности.

Different candidate mistake: Коммитить полную разработку до проверки гипотезы. → Повысить WSJF искусственным дроблением технических слоёв.

Different actual decision: Купить дешёвое поведенческое свидетельство. → Выделить настоящую ценностную вертикаль с prerequisite и пересчитать портфельный trade-off.

Different strongest reasoning: Ценность информации до инвестиции. → Изменение единицы инвестиции должно сохранять реальную самостоятельную ценность и зависимости.

### TC-119 / TC-009 / DUPLICATE

Production analog tests: Команды имеют неодинаковую readiness автоматизации. Progressive blocking по readiness. Темп внедрения соответствует способности пройти проверку.

Old planned row tested: Единый big-bang enforcement ↔ progressive blocking по измеримой readiness.

New planned row tests: Привязать passed к конкретной паре provider/consumer и при изменении используемого контракта инвалидировать затронутое свидетельство с повторным targeted прогоном; не сохранять старую зелёную отметку и не запускать весь регресс без различения зависимостей.

Different decisive fact: Команды имеют неодинаковую readiness автоматизации. → Все готовы проходить gate, но API изменяется после зелёного результата.

Different candidate mistake: Включить blocking всем в один день. → Считать passed бессрочным свойством consumer без версии provider.

Different actual decision: Progressive blocking по readiness. → Version-bound evidence с invalidation и targeted rerun затронутых связок.

Different strongest reasoning: Темп внедрения соответствует способности пройти проверку. → Срок жизни свидетельства связан с тем артефактом и контрактом, которые реально проверены.

### TC-120 / TC-039 / NEAR DUPLICATE

Production analog tests: Слабые межпродуктовые зависимости, лишняя общая координация. Уменьшить координацию по границам value flow. Координация должна окупать реальные зависимости.

Old planned row tested: Масштабировать framework по числу команд ↔ платить coordination cost только там, где есть общий product flow.

New planned row tests: Исключить защищённую IP-capacity из продуктовых обязательств и согласовать показатели лидов с результатами обучения/интеграции; перенос feature scope сделать явным портфельным решением вместо скрытого расходования IP на доделки.

Different decisive fact: Слабые межпродуктовые зависимости, лишняя общая координация. → ART обоснован и зависимости отслеживаются; IP уже зарезервирована на бумаге, но дважды включена в feature capacity.

Different candidate mistake: Масштабировать framework по числу команд. → Обещать всю номинальную capacity, одновременно называя IP защищённой.

Different actual decision: Уменьшить координацию по границам value flow. → Исправить базу commitment capacity и показатели лидов; явно переобещать feature scope.

Different strongest reasoning: Координация должна окупать реальные зависимости. → Календарный резерв не существует, если та же мощность уже обещана другому результату.

### TC-122 / TC-017 / DUPLICATE

Production analog tests: Новая просадка до диагностики. Диагностика перед PIP. Лечение следует диагнозу.

Old planned row tested: Формальный performance process по симптомам ↔ сначала честный диагностический разговор.

New planned row tests: Закрыть выполненный PIP по согласованному правилу и вернуть обычный ритм управления, сохранив стандартные safeguards релиза; не менять критерий выхода задним числом ради тревоги руководителя.

Different decisive fact: Новая просадка до диагностики. → Согласованный PIP успешно выполнен, новых нарушений нет.

Different candidate mistake: Формализовать до выяснения причины. → Переносить согласованный критерий выхода после успеха.

Different actual decision: Диагностика перед PIP. → Закрыть PIP и управлять риском релиза обычными controls.

Different strongest reasoning: Лечение следует диагнозу. → Заранее обещанный успешный исход обязателен; новый delivery риск не продлевает персональный процесс.

### TC-125 / TC-013 / NEAR DUPLICATE

Production analog tests: Типовой низкорисковый спрос застрял в центральной очереди. Self-service типовых операций с guardrails. Устранить класс зависимости.

Old planned row tested: Централизованное approval для всего ↔ risk-tiered delegated controls с обязательными guardrails.

New planned row tests: Сохранить embedded помощь и автоматизацию, но закрепить независимое подтверждение high-risk, защищённую capacity и линию отчётности assurance с ИБ; не лечить конфликт интересов дополнительным обучением champions или тотальной централизацией.

Different decisive fact: Типовой низкорисковый спрос застрял в центральной очереди. → Типовой спрос уже автоматизирован; high-risk авторы контролируют себя под KPI delivery.

Different candidate mistake: Масштабировать ручную очередь вместо снятия зависимости. → Считать embedded компетентность заменой независимости assurance.

Different actual decision: Self-service типовых операций с guardrails. → Разделить embedded помощь и независимый high-risk контроль с защищённым бюджетом/отчётностью.

Different strongest reasoning: Устранить класс зависимости. → Компетенция проверяющего не устраняет конфликт интересов; сохраняется независимость без тотального ручного контроля.

## Validation scope and limits

Cross-bank: 15 changed rows, 133 scoped comparisons; 13 ALLOWED REINFORCEMENT / 2 NO CLOSE ANALOG / 0 NEAR DUPLICATE / 0 DUPLICATE. Обязательно включены исходные analogs, все same-topic и same-primary cases плюс дополнительные подозреваемые пересечения. Shortlist — retrieval, не verdict. Остальные 10 строк Batch 04 наследуют исходный hash-bound preflight.

Internal: 255 пар с хотя бы одной изменённой строкой; blocking collisions 0. Остальные пары не переоткрывались. Все три изменённых family contracts проверены; неизменённая F-PR-P01 сохранена буквально. Triplet содержит три стратегии и две границы, перечисленные в family-contract-validation.json.

Future sanity: просмотрены boundary TC-126…TC-300, для близких тем расширены concepts/facts; 0 obvious collisions. Это не полный future QA. Важные различия с TC-161/185/198/199/211/278/279 зафиксированы в future-manifest-sanity.json; при authoring их нельзя размывать до общих формулировок.

## Runtime и уровни

Vocabulary получен исполнением текущего Swift mapping: 19 domains / 94 patterns; unknown 0. Source/reference hashes совпали. Primary 1.0, secondary 0.5, max per case/category, normalization по max(1,sum), context evidence=0. Weighted coverage пересчитан; прошлое заявление об all-300 impulse tests не переносилось на эту редакцию. Полные synthetic cases не создавались.

Все topic/domain/level/structure/eligibility/batch/member IDs и позиции сохранены. Level feasibility обоснована по каждой новой boundary; это авторская самооценка перед независимым QA.

| Pool | Junior | Middle | Senior | Head |
|---|---:|---:|---:|---:|
| new | 42 | 122 | 76 | 35 |
| all300 | 44 | 143 | 78 | 35 |
| assessment200 | 32 | 99 | 46 | 23 |

Итоговые уровни не компенсировались. Target/actual/gap находятся в runtime coverage. Head breadth capacity: PASS; eligible Senior+Head domains с ≥3 cases: finance, people, portfolio, processes, product, project, stakeholders, technical. Это наличие материала, не оценка пользователя.

275 planned = 181 standalone + 94 linked; 35 pairs + 8 triplets; 11×25. Batch 04: 16 standalone / 9 linked / 4 families; J3/M13/S6/H3. Projected pools: training 300, ordinary assessment 200, families 46, max independent units 246.

Current production уже содержит assessmentEligible=false у шести linked gold; historical task сохранена в provenance, новые flags не менялись. ManifestVersion в исходном master/pack исторически остался 2.2.2-frozen; authoritative baseline определён заданным v2.2.3 path и проверенным SHA. Candidate имеет собственный явный version/status; исходные файлы не исправлялись.

## Handoff

Production, v2.2.3, preflight, context pack, runtime, schema и учебник остались неизменными по input-hashes. Candidate hashes перечислены в artifact-hashes.json. CSV списки/объекты сериализованы JSON, booleans — true/false.

**READY FOR INDEPENDENT MANIFEST QA: YES**

Самооценка не означает freeze, разрешение authoring или import. Full cases TC-101…TC-125 не создавались; Batch 05, application, scoring, commit/push не выполнялись.
