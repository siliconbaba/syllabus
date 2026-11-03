# Wave 7 substantive redesign — PARTIAL

Единственная база v2.3-wave6-candidate, SHA `538a06b8daaeea8c17a1de2573269c170a9dee185de61a41d14df4bb163321bd`. Plan immutable: `08cc861b8d48620b1170bfccffe79a710b2a92be5c810158e69da41bb674f37e`.

Scope13:8Middle/3Senior/2Head;6 standalone и7 linked в3 семьях. Один доказанный redesign TC-248; остальные12 unchanged UNRESOLVED. Target не превращён в квоту.

Все54 принятые Wave1–5 и9 redesigned Wave6 сохранены. Wave6 independent QA ещё не выполнен.

## TC-248 — senior / t-13-3

Senior TPM должен перепроектировать проверку функции распределения заказов: пользовательский A/B показывает выигрыш, но участники двух групп конкурируют за одну исполняющую мощность.

Decisive facts:
- Пользователи рандомизированы корректно, события и группы проверены. Функция ускоряет подбор свободного исполнителя; во время теста эксперимент получает больше завершённых заказов, контроль дольше ждёт. Исполнители могут брать заказы обеих групп, их число за период не меняется.
- Исполнители перемещаются через административные границы районов; заказы и занятость после назначения продолжаются несколько часов. Данных пока недостаточно, чтобы считать каждый район независимым или выбрать длительность временного блока без проверки переноса эффекта.
- TPM вместе с аналитиком может изменить единицу распределения воздействия и провести ограниченную проверку. Нужен прирост завершений всего обслуживаемого рынка без ухудшения ожидания, а не перераспределение доступных исполнителей между группами. Полный rollout до проверки не обязателен.

Decision boundary: Проверить гипотезу перетока общей мощности и строить эксперимент по фактически связанным пулам исполнителей: по журналам перемещений определить границы взаимодействия, с аналитиком оценить перенос занятости и выбрать блоки/период очистки. Оценивать суммарные завершения и ожидание пула, а не относительную победу пользователей; не считать районы независимыми по названию и не переключать режим каждый час без проверки carryover.

Specific reasoning: Senior обнаруживает нарушение независимости воздействия при корректной пользовательской рандомизации, меняет единицу причинного сравнения и проверяет вторичные последствия конкуренции за общий ресурс и временного переноса эффекта.

Why lower-level reasoning is insufficient: Сильный Middle может сравнить готовые эффекты и guardrails, но здесь сами сравниваемые группы влияют друг на друга. Нужно вывести новую границу эксперимента из механизма взаимодействия, а не выбрать лучший готовый сегмент.

Specific Senior reasoning: Senior обнаруживает нарушение независимости воздействия при корректной пользовательской рандомизации, меняет единицу причинного сравнения и проверяет вторичные последствия конкуренции за общий ресурс и временного переноса эффекта.

Why strong Middle reasoning is insufficient: Сильный Middle может сравнить готовые эффекты и guardrails, но здесь сами сравниваемые группы влияют друг на друга. Нужно вывести новую границу эксперимента из механизма взаимодействия, а не выбрать лучший готовый сегмент.

Source: сетевые эффекты; полный topic/excerpt в source-grounding-wave7.json. Числа, роли и ограничения сценария авторские.

Semantic distinction: TC-195 исправляет единицу пользователь/сессия при независимых пользователях; здесь пользователи влияют друг на друга через исполнителей. TC-295 касается post-hoc сегментов, TC-261 — внешней кампании, а не интерференции внутри теста.

Runtime evidence:
- hypothesis: Переформулировать проверку как дополнительную ценность всего пула, а не выигрыш одной группы за счёт другой.
- root-cause: Связать противоположные результаты с общей мощностью и проверить механизм интерференции и carryover.

Pairwise self-QA:
- Rollout пользовательского победителя: Относительный выигрыш может быть перераспределением общей мощности; он не оценивает прирост всего рынка.
- Больше наблюдений при прежней единице: Увеличение выборки уменьшает случайный шум, но не устраняет влияние treatment на control через общих исполнителей.
- Готовая сетка район × час: Исполнители пересекают районы, а занятость длится несколько часов: обе выбранные границы допускают перенос. Их надо вывести из фактического взаимодействия, а не принять по удобству отчёта.

## Unresolved
- TC-151: Проверен costed redesign очереди / своего вклада / эскалации по float. Несмотря на operational trade-off, сохраняется близость к production TC-026/027/028: та же временная ось переключает те же классы стратегий. Вся тройка и contract оставлены unchanged.
- TC-152: Проверен costed redesign очереди / своего вклада / эскалации по float. Несмотря на operational trade-off, сохраняется близость к production TC-026/027/028: та же временная ось переключает те же классы стратегий. Вся тройка и contract оставлены unchanged.
- TC-153: Проверен costed redesign очереди / своего вклада / эскалации по float. Несмотря на operational trade-off, сохраняется близость к production TC-026/027/028: та же временная ось переключает те же классы стратегий. Вся тройка и contract оставлены unchanged.
- TC-206: Добавление раннего threat modeling улучшает общий процесс обоих sibling, но не делает контраст допуска исключения Senior: при frozen оси чувствительности среды выбор остаётся готовой классификацией риска. Атомарная пара сохранена.
- TC-207: Системный secure-SDLC redesign не создаёт самостоятельной Senior границы между состояниями без изменения нескольких переменных. Сibling206 и contract сохранены вместе.
- TC-212: Проверен вариант concierge с ограниченной ручной мощностью. Выбор мощности превращает blueprint в обычную закупку, а диагностическая граница MVP остаётся близка TC-025/060. Уникальная содержательная реализация Middle пока не доказана.
- TC-221: Вариант выбора стоимости реализации после завершённого A/B даёт operational trade-off, но эксперимент становится декорацией к process economics. Вариант резервирования до результата повторяет TC-211. Новый source-specific Middle не доказан.
- TC-239: Пилот перед lock-in повторяет TC-033/034; добавление цены информации сближается с принятой TC-218. Конструкция с новой самостоятельной границей не доказана.
- TC-259: Добавление портфельного бюджета и владельцев метрик к исходной границе прямое поведение/proxy не доказало Head strongest shift: фактический выбор остаётся проверкой гипотезы. Атомарная пара сохранена.
- TC-260: Проверена идея разделить бюджет learning и scale, но она добавляет общую governance-обвязку обоим состояниям без доказанной Head границы. Пара259/260 и contract неизменны.
- TC-263: Осознанная ставка после inconclusive test требует дополнительного предпочтения по риску; без него strongest не уникален, с готовым порогом возвращается rule application. Не форсировать Middle.
- TC-275: Выбор покрытия SLA versus development capacity даёт арифметический trade-off, но повторяет TC-194; иной вариант смешанного контракта близок текущим строкам темы8.4. Уникальный blueprint не доказан.

## Regression

Wave6 → Wave7: 1 changed / 274 unchanged rows, 0 changed /43 unchanged families. Unexpected0. Wave6 unresolved159/230/231/296 unchanged.

v2.2.3 cumulative: {'changedRows': 87, 'unchangedRows': 188, 'changedFamilies': 11, 'unexpectedTC026TC100Changes': 0}.

Semantic screen: 299 comparisons; 24 expanded dossiers; top6 + all same topic/primary + manual causal analog expansion. TC-248 ALLOWED REINFORCEMENT; NEAR/DUP0 only for changed row. Within-wave comparison N/A: one change.

Families:0/0 changed; all3 selected families unresolved and byte-semantic unchanged. Original contracts not repaired opportunistically.

Runtime: fresh compiled Swift mapping, matching source/reference hashes; engine source read; primary1/secondary0.5,alias max,normalization max(1,sum),context0 verified by rational recomputation.

Structural PASS:275 IDs;181standalone/94linked;35pairs+8triplets;11×25;eligibility and identity preserved;no split. Coverage/head breadth recomputed; full-case loader NOT_APPLICABLE.

Remaining global unresolved 78. Source/level/runtime/uniqueness PASS applies only to actual changed row; no acceptance for rejected drafts.

**READY FOR COMBINED WAVE6+7 INDEPENDENT QA: YES** — scoped review of actual changes; two separate verdicts required. Independent QA not run.

No Wave8,full cases,production/app/schema/scoring changes,freeze,import,commit or push.
