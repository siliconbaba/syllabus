# Focused QA manifest v2.2

**READY FOR BATCH 01**  
**Можно начинать Batch 01: YES.**

34 prior row issues: **34 FIXED / 0 remaining**.  
4 prior family issues: **4 FIXED / 0 remaining**.  
Frozen rows regression: **0**. Frozen families semantic regression: **0**.  
26 level changes: **PASS**. Head calibration: **PASS**.  
Assessment feasibility: **PASS**. Head breadth: **PASS, 8 areas**.  
Оставшиеся blocker / major / minor: **0 / 0 / 0** в проверенном scope.

Это focused closure замечаний QA v2.1 с regression gate; полный повторный аудит 275 концептов не проводился. Production candidate и baseline не изменены. Содержательный источник — текущий `InteractiveBook/WebContent/index.html`; runtime-источник — фактические Swift mapping/engine. Авторские validation-result и changelog не использовались как доказательство исправления.

## 1. Независимый diff и frozen gate

Первым проверочным действием после обнаружения файлов выведен diff JSON v2.1 → v2.2, до чтения авторского changelog.

- Изменены ровно **40** строк: все 34 ID из прежнего row-fix list и только TC-026/027/028, TC-176/177/178 сверх него.
- **235 строк полностью равны как JSON-объекты**, включая все запрошенные поля и derived runtime metadata. Это сильнее проверки только списка frozen fields. Проверялось равенство значений, не whitespace сериализации.
- Шесть дополнительных строк принадлежат двум исправляемым triplets. В них меняются только scenario, decisive facts, boundary и mutation; batch/domain/level/eligibility не затронуты. Во всех шести строках закреплены общие константы соответствующей семьи, поэтому это необходимое согласование siblings.
- Содержательно изменены ровно четыре разрешённые family constructions.
- Уточнение к фразе «39 families unchanged»: **36 records полностью неизменны**, ещё **3** изменены только по requiredLevel: F-PR-P01 → Middle, F-PO-T01 → Middle, F-PO-P04 → Senior. Это прямое следствие разрешённых row-level исправлений. У всех 39 сохранены baseSituation, variable, states, boundaries, constants и membership. Неожиданного semantic drift нет.
- ID, порядок строк, membership и batch assignment сохранены. Производные поля изменились только там, где изменились source patterns, и соответствуют текущему mapping.

Подробный diff и все 26 transitions сохранены в `diff-evidence.json`. Изменения уровня семей не считаются regression: их неизменность вопреки sibling-level исправлениям, наоборот, нарушила бы согласованность.

## 2. Закрытие 34 строковых замечаний

`row-fixes-focused.csv` содержит **все 34 прежних issues**, а не только оставшиеся: исходную категорию, статус, конкретное доказательство из v2.2, уровень и primaryPattern. PARTIALLY FIXED / NOT FIXED / REGRESSION отсутствуют.

Ключевые содержательные проверки:

- TC-144: Middle, safeguards, без rollback/api-contracts. TC-273 теперь не повторяет идемпотентность: она уже обеспечена атомарно; выбор касается retries/backoff/jitter при восстановлении до 10 минут и допустимой задержке 30 минут. Различие проверяемых решений реально. §10.1 описывает риски очередей и даёт связь с retry/backoff в §10.5; защита повторной денежной обработки раскрыта в §10.3.
- TC-145: risk-differentiation для expedite; TC-214: safeguards/reliability для cache. Исчезли ложные risk→issue и hotfix.
- TC-116/216/194: выбор safeguards или communications больше не начисляется как decision authority.
- TC-112: expectation-management, связь с §6.2, без early-bad-news. TC-224: §6.5 и communications для письменной фиксации распределённого решения.
- TC-288: §7.9, root-cause/support для известной причины перегрузки; blameless больше не подменяет проверяемую тему.
- Исправленные уровни соответствуют прежним конкретным замечаниям: остановка теста TC-075 — Junior; diagnosis/PIP/HR, dashboard interpretation, EAC и ведение подрядчика — Middle, а не Senior по должности героя.

Оставшийся повтор safeguards в primary/secondary TC-194 не удваивает scoring: engine объединяет категории через max. Это не основание открывать новый cosmetic issue. Полная повторная оптимизация неизменённых secondaryPatterns не входила в этот QA.

## 3. Четыре family issues — FIXED

Выбор стратегии проверен по состояниям и константам, до принятия авторского whyMutationIsControlled как объяснения. В строках siblings присутствуют все family constants, а decisionBoundary совпадает с соответствующим состоянием.

### F-PM-T01 — FIXED

1 день: 5−1=4 дня резерва, trigger 3 не достигнут. 4 дня: 5−4+2=3 дня, активировать меру. 8 дней: 5−8+2=−1 день, изменить обязательство. Мера/стоимость/полномочия постоянны.

### F-PE-T01 — FIXED

Общий горизонт 4 недели, capacity 40, одинаковые меры 2+8 часов. 42−2=40; 50−2−8=40; 60−2−8=50>40. Конец пика не меняется; третье состояние требует дополнительного решения.

### F-ST-P03 — FIXED

Одна финальная сделка 100; BATNA 120/80 на одинаковом горизонте после затрат и рисков. 120>100 → отклонить, 80<100 → принять. Пакетирование одинаково завершено, полномочия и сроки постоянны.

### F-TD-P03 — FIXED

В обеих версиях demand 12 и capacity 10 постоянны. Единственная переменная — цена отсрочки 40/160 против общей цены reviewer 100. Ограничить вход / купить мощность. Отличается от F-PR-P01 по предмету выбора.

У F-PM-T01 проверяются три заданных состояния 1/4/8, а не универсальная policy для всех промежуточных значений. Требуемый остаточный резерв и предел сохранения внешней даты различены. Числовые ограничения — общие факты конкретного сценария, а не выданные за правила учебника пороги.

У F-PE-T01 больше нет скрытого исчезновения пика только в первой версии. У F-ST-P03 защита reservation point не противопоставляется обмену интересами: одинаковое окончательное предложение сравнивается с разной реальной альтернативой. У F-TD-P03 устойчивость очереди одинакова в обеих версиях; меняется экономическая цена отсрочки, поэтому это больше не дубль F-PR-P01.

## 4. 26 level transitions — PASS

Проверялось необходимое рассуждение, а не титул героя или числовая квота. Распределение переходов подтверждено независимо:

- Senior → Middle: 13.
- Head → Middle: 8.
- Junior → Middle: 2.
- Head → Senior: 2.
- Senior → Junior: 1.

| ID | Было → стало | Проверяемое основание |
|---|---|---|
| TC-064 | head → middle | Сопоставить известную экономику сделки с проверенной альтернативой и определить допустимые уступки; governance не проектируется. |
| TC-072 | senior → middle | Сопоставить завершённую поддержку и отсутствие улучшения с условиями перехода к формальному PIP одного сотрудника. |
| TC-075 | senior → junior | Соблюсти явное ограничение протокола: ранняя значимость не разрешает остановку до 14 дней без early-stop rule. |
| TC-088 | senior → middle | Подготовить влияние проблемы и варианты решения для рабочей эскалации; уровень адресата не усложняет reasoning. |
| TC-092 | senior → middle | Сегментировать p95 и среднее, чтобы локализовать ухудшение пользовательского опыта по данным дашборда. |
| TC-100 | senior → middle | Отличить одиночный шум от устойчивого actionable-сигнала и выбрать рабочий порог реакции. |
| TC-106 | junior → middle | Сопоставить временность очереди с устойчивой пропускной способностью и выбрать управление потоком без лишней перестройки. |
| TC-107 | junior → middle | Сопоставить устойчивый входящий поток с capacity и выбрать рабочее изменение WIP или мощности. |
| TC-113 | senior → middle | Проверить неизвестную причину снижения мотивации через 1:1 до выбора бонуса или другой интервенции. |
| TC-122 | senior → middle | Выбрать диагностику и обратную связь до формального PIP, поскольку причина внезапной просадки ещё не установлена. |
| TC-144 | senior → middle | Сопоставить гарантии доставки и последствия повторного списания; потребовать защиту бизнес-обработки от дубликатов. |
| TC-168 | head → middle | Рассчитать экономику своей альтернативы до уступок и обещаний; организационная модель не меняется. |
| TC-194 | head → middle | Сначала применить обязательные security/audit ограничения, затем сравнить цену допущенных поставщиков. |
| TC-201 | head → middle | Сопоставить расход error budget с утверждённым warning-порогом и сохранить обычный темп в рамках policy. |
| TC-202 | head → middle | Применить утверждённый warning-порог и выделить предусмотренную policy capacity на стабилизацию. |
| TC-203 | head → middle | Применить утверждённый freeze-порог и остановить изменения согласно готовому правилу. |
| TC-217 | senior → middle | Согласовать работу с результативностью сотрудника с HR-процедурой до необратимых кадровых действий. |
| TC-253 | senior → middle | Сравнить измеренную цену отсрочки входящего потока со стоимостью дополнительной capacity на одном горизонте. |
| TC-254 | senior → middle | Выбрать между снижением входа и увеличением мощности по полным сопоставимым затратам, без перепроектирования нескольких потоков. |
| TC-255 | head → middle | Сопоставить конкретную сделку с более выгодной доступной BATNA и отказаться от уступки ниже reservation point. |
| TC-256 | head → middle | Сопоставить ту же сделку с менее выгодной BATNA и принять предложение, превышающее reservation point. |
| TC-261 | senior → middle | Распознать изменение цены только в B как смешение факторов и не приписывать весь эффект фиче. |
| TC-275 | senior → middle | Различить SLA поддержки и критерии приёмки разработки при ведении одного подрядчика. |
| TC-282 | head → senior | Оценить организационный blast radius и последствия расширения command structure; единый Senior семьи учитывает межкомандную альтернативу, локальная ветвь сама по себе не является самостоятельным Head evidence. |
| TC-283 | head → senior | Согласовать конфликтующие действия нескольких доменов, восстановление общего клиентского пути и коммуникации через единую incident command structure. |
| TC-300 | senior → middle | Сопоставить paid-to-date с законтрактованными обязательствами и прогнозом EAC, чтобы получить корректный план-факт. |

Разница между должностью персонажа и requiredLevel намеренна: оставшееся слово Head/Senior в scenario не означает такой же уровень задачи.

Все 10 прежних Head issues закрыты: 8 → Middle и 2 → Senior. TC-282/283 сохраняют единый Senior как семью выбора границы incident coordination; локальная ветвь TC-282 сама по себе не является самостоятельным Senior/Head assessment evidence, оба linked исключены из assessment. Это соответствует согласованной правке v2.1, а не новой Head-надстройке.

Оставшиеся **35 Head rows полностью frozen**; whyHead/authorityScope/secondaryEffect заполнены. Выборочно повторно проверены TC-039 (operating model), TC-137 (organizational incentives), TC-170 (многолетняя budget/sourcing architecture). Head-содержание и связь secondary effects с реальным выбором сохранены. Полного повторного аудита всех 35 не проводилось.

## 5. Структура и runtime — PASS

Независимый пересчёт подтвердил 275 new = 181 standalone + 94 linked; 35 pair families, 8 triplets, 11 × 25 batches. Пропусков/дублей ID нет; topic/part валидны; split family отсутствуют; domain/topic/level внутри семьи согласованы. CSV и JSON совпадают по экспортированным значениям. Все hashes из artifact-hashes.json подтверждены.

Eligibility новых строк: standalone training=true / assessment=true; linked training=true / assessment=false.

Unknown domains = **0**; unknown patterns = **0**; provisional mappings = **0**. Все derivedRuntimeUiDomain/PrimaryThinking/SecondaryThinking соответствуют фактическому Swift mapping. Mapping и engine имеют те же SHA-256, что при QA v2.1.

Фактический engine сохраняет primary weight 1, secondary 0.5, дедупликацию категории max, нормирование общей суммы до ≤1 и distinct-case count. **Context sensitivity scored evidence = 0**; futureContextSensitivityCandidate не является runtime score.

## 6. Новое распределение и assessment — PASS

| Пул | Junior | Middle | Senior | Head | Всего |
|---|---:|---:|---:|---:|---:|
| New | 42 | 122 | 76 | 35 | 275 |
| All | 44 | 143 | 78 | 35 | 300 |
| Planned standalone assessment | 32 | 99 | 46 | 23 | 200 |

Каждая level bucket существенно превышает minimumLevelEvidence=5. Старые квоты 45/120/90/45 не применялись. Снижение Head/Senior исправляет смысл evidence, а не ухудшает его по определению.

| Runtime domain | Standalone evidence | Senior+Head | Breadth ≥3 |
|---|---:|---:|---|
| Управление проектами | 18 | 6 | да |
| Delivery и релизы | 12 | 2 | нет |
| Процессы | 30 | 14 | да |
| Стейкхолдеры | 20 | 6 | да |
| Люди | 23 | 7 | да |
| Финансы и подрядчики | 19 | 5 | да |
| Портфель и стратегия | 17 | 7 | да |
| Технический TPM | 38 | 17 | да |
| Аналитика | 12 | 1 | нет |
| Продукт | 11 | 4 | да |

Все 10 UI-domains имеют потенциальное evidence; ни равного количества, ни Senior/Head в каждой области engine не требует. Head breadth: **8 областей** с ≥3 Senior/Head cases, нужные people/stakeholders и portfolio/finance присутствуют; gate ≥5 областей достижим.

Дополнительно собран и запущен независимый небольшой harness с **текущими production TrainerModels/Store/ScoringMapping/ScoringEngine** и существующим ScoringFixtures. На planned pool с синтетическими quality=1 получено:

- J-only, 32 evidence → Junior;
- J+M, 131 → Middle;
- J+M+S, 177 → Senior;
- все 200 → Head, breadth=true, 8 areas;
- excluded metadata=0; scored context отсутствует.

Результат: `engine-feasibility.json`. Это проверка достижимости и progression, не обещание результата пользователя или любой короткой сессии. Тестовые объекты создавались только в памяти harness; новых production кейсов нет. Первоначальная сборка через CommandLineTools упёрлась в cache/SDK окружение; повторная сборка через Xcode с cache в /tmp успешно завершилась, assertions прошли.

Assessment 200 по-прежнему предполагает запланированное исключение шести существующих linked gold (TC-001/002, 003/004, 017/018). Их текущие flags не менялись этим QA. Миграция нужна перед diagnostic expansion, но не блокирует авторинг Batch 01. Runtime не получил family-aware Slice в рамках этой работы.

## 7. Итог и граница разрешения

Оба системных blocker предыдущего QA закрыты в согласованном focused scope: адресно исправлена калибровка, восстановлены linked boundaries и устранены отмеченные дубли. Frozen regression отсутствует; scoring остаётся технически достижимым после честных downgrades.

**READY FOR BATCH 01. Можно начинать Batch 01: YES.**

v2.2 можно зафиксировать как blueprint. v2.3 и ещё один полный manifest QA не требуются. При авторинге все значимые family constants должны попасть в context до ответа; текущий PASS не заменяет последующий QA готовых question/options/explanations. WebKit timeout не переоткрывался и не является manifest-blocker.
