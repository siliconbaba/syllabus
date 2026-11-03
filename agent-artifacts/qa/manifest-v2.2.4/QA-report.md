# Independent focused QA — manifest v2.2.4-candidate

**NOT READY — 0 BLOCKER, 2 MAJOR, 0 MINOR.**

Исходные 11 semantic collisions устранены. Freeze останавливают только два оставшихся дефекта уровня: **TC-115 и TC-122**. Ни содержание источника, ни семейная логика, ни runtime не требуют общего перепроектирования. Исправить эти две standalone строки и провести локальный retest; 260 unchanged rows повторно не аудировать. Статус NOT READY выбран по п.16 задания для substantive level problems.

## Scope, independence and integrity

Прочитаны PIPELINE-CONTRACT.md, TEST-QA-RUNBOOK.md и схема. Машинный diff masterplan/CSV выполнен до авторских классификаций. Все15 changed rows и3 changed family contracts прочитаны напрямую. Прочитаны полные10 релевантных тем, заново извлечённых из authoritative index.html. Авторские результаты не использовались как решение QA: future tooling задаёт только список сравнений; первичный preflight — перечень проверяемых исходных коллизий.

Содержательный источник единственный: `InteractiveBook/WebContent/index.html`, SHA-256 `f525fbb22c62688ae4a7c7b07f5f12b4bbd9c8044daf32a0f229ba70438e2b4f`. Production100 SHA-256 `6becf4f8ccdb914e9ebd51ca780902174ecdd7914824408139b40477cd25c6a3` совпал до и после проверки. Candidate SHA-256: `ffb6486e5f6c34b2cf291b02f98d9ae703d35639f287d2df45a7eebd48176eec`.

Контекст-пак использован как baseline shortlist и вспомогательный source inventory. Его sources-хеши и artifact hashes проверены. Текстовый manifestVersion в batch-contract содержит старую метку2.2.2-frozen, но source path/hash привязан к фактическому baseline v2.2.3 и совпадает. Для candidate использованы его собственные строки и заново расширенные same-topic/same-primary comparisons. Устаревшая подпись пакета не принята за подтверждение candidate и не блокирует этот hotfix.

## Manifest diff / structural gate — PASS

- Changed planned rows **15/15**: TC-101, TC-102, TC-103, TC-104, TC-105, TC-108, TC-109, TC-111, TC-113, TC-115, TC-118, TC-119, TC-120, TC-122, TC-125.
- Unchanged rows **260/260**, semantic identity. Approval наследуется от пользовательского authoritative v2.2.3; нового content QA этих260 не проводилось.
- Changed families **3/3**: F-TD-T01, F-PM-P01, F-PA-P02. Остальные40 family contracts идентичны.
- Unexpected changed rows **0**, unexpected families **0**, unexpected auxiliary semantic changes **0**.
- Masterplan и CSV дают одинаковый scope. Дополнительные изменения headAudit относятся только111/120/125; changedFamilyDesigns — только трём разрешённым семьям. Version/provenance отмечают candidate как NOT_FROZEN; coverage пересчитан независимо.
- **275 rows =181 standalone +94 linked;35 pairs +8 triplets;11×25 batches**. ID026…300 без пропусков и дублей; topic/part проверены по production catalog. Family membership, batch и уровень внутри семьи согласованы; split families нет.
- Batch04: **TC-101…125,25rows,16standalone,9linked,4families,J3/M13/S6/H3**. Structure, levels, membership, eligibility не изменены hotfix. Текущие275levels J42/M122/S76/H35 совпадают с baseline; исторические targets ранних версий не навязывались.
- Training=true всем; assessment=true standalone, false linked.

## Remaining defects

### L-115 — TC-115 — MAJOR

**Проблема.** Middle заявлен, но все решения о допустимости уже зафиксированы: 6/20 нарушает RPO5;18/0 удовлетворяет30/5. Сценарий проверяет чтение двух порогов, а не operational trade-off.

**Минимальное исправление.** Согласованно перекалибровать standalone строку в Junior и обновить derived aggregates/whyLevel; либо сохранить Middle, но задать реальный выбор восстановления с отличающимися затратами/этапами/ограничением исполнения, который требует сопоставления последствий, не отменяя RPO/RTO. Не поручать автору незаметно менять frozen boundary.

**Повторная проверка.** Focused TC-115 source/level/uniqueness + semantic diff и runtime/coverage; без повторного QA260строк.

### L-122 — TC-122 — MAJOR

**Проблема.** Выполненность, достаточность критериев, правило закрытия, отсутствие нового основания и возможность сохранить safeguards уже даны. Выбор сводится к правилу «выполнен→закрыт»; заявленное разграничение рисков уже сделано в условии.

**Минимальное исправление.** Согласованно перекалибровать standalone строку в Junior; либо сохранить Middle и разработать реальную развилку обычной поддержки/передачи ответственности после закрытия с ограничением ресурса, сохранив честное завершение PIP. Одного усиления whyLevel/терминологии недостаточно.

**Повторная проверка.** Focused TC-122 source/level/uniqueness + semantic diff и runtime/coverage; без полного QAmanifest.

Оба решения содержательно поддержаны учебником и отличны от production-аналогов. Дефект относится к измеряемой сложности: число терминов, роль DM и важность последствия не повышают уровень готового правила. Это не требование сделать варианты двусмысленными или скрыть decisive facts; для Middle нужен самостоятельный operational choice. Нельзя исправить уровень только более длинным whyLevel.

## Original11 blockers — fixed11/11

Для каждого ниже новый blueprint сопоставлен с исходной строкой и фактическим production context/options. Classification относится к новой задаче; старые совпадения не оправдываются новым wording.

### TC-103 → TC-010

**Old collision:** Сначала переделать миграцию в expand-contract, и только потом включать новое поведение. Production: Сначала сделать совместимый формат и промежуточный релиз, затем включить новый код и удалить старый формат позже.

**New diagnostic task:** Lead TPM выбирает доказательную схему замены движка комиссий: редкие тарифы не набираются в малой canary за доступное окно, а неверные списания недопустимы; скрытый результат сам по себе не блокирует публикацию платёжных команд. Состояние границы эффектов: Часть внешних эффектов идёт в обход доступного интерфейса; их нельзя изолировать конфигурацией или существующим адаптером, сначала нужен новый архитектурный шов.

**Different decisive fact:** Нет миграции данных; часть внешних эффектов обходит периметр изоляции.

**Different candidate mistake:** Принимать флаг скрытия результата за запрет внешнего действия.

**Different actual decision:** Архитектурно отделить эффекты перед shadow с переносом.

**Different strongest reasoning:** Безопасность двойного исполнения, не совместимость форматов для старого кода.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-105 → TC-006

**Old collision:** Управлять уже возникшей проблемой, активировать response plan и обновить последствия/остаточные риски. Production: Зафиксировать реализованное событие и его влияние, запустить план реакции и отдельно вести новые риски после перепланирования.

**New diagnostic task:** Junior PM обновляет запись риска отказа внешнего канала до следующего запуска: сигнал резервирования появляется за 3 рабочих дня до возможного отказа, ранний проверенный индикатор — за 7; владелец просит проверить, успеет ли подготовленный fallback. Подготовка fallback занимает 5 рабочих дней.

**Different decisive fact:** Событие не произошло; response5д длиннее позднего сигнала3д, но укладывается в7д.

**Different candidate mistake:** Ждать более позднее подтверждение, после которого уже нельзя успеть.

**Different actual decision:** Перенести trigger подготовки на ранний индикатор.

**Different strongest reasoning:** Предвосхитить событие по времени реакции, а не перевести уже случившийся риск в issue.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-108 → TC-044

**Old collision:** Сначала расширить диагностику и локализовать источник. Production: За 15 минут локализовать ошибки по версии, региону и endpoint; выбрать меру для сегмента и сохранить аварийный trigger.

**New diagnostic task:** Delivery Manager с SRE выбирает режим хранения диагностических записей одного класса за неделю при лимите 1 ГБ: нужен не только счётчик, но и не менее 100 полных примеров для разбора, если события произошли; остальные потоки уже оптимизированы. За неделю возникает 10 000 000 событий этого класса.

**Different decisive fact:** Решается объём сохранения подробных логов, не локализация текущей деградации; счётчик остаётся точным.

**Different candidate mistake:** Приравнять полноту всех логов к достаточности расследования, игнорируя storage cap.

**Different actual decision:** Сохранять каждый сотый экземпляр.

**Different strongest reasoning:** Сопоставить стоимость подробностей и достаточность выборки, не покупать ещё диагностику перед rollback.

**Classification:** NO CLOSE ANALOG. Original collision: FIXED.

### TC-111 → TC-040

**Old collision:** Больше координации поверх прежних incentives ↔ изменить governance и decision rights. Production: Закрепить критерии выбора, владельца решения и границы veto для каждого класса конфликтов; включить их в регулярное планирование.

**New diagnostic task:** Head выбирает последовательность перехода трёх продуктов на LeSS: бюджеты принадлежат шести департаментам, полномочный единый PO не может появиться без решения CFO; ограниченная координация ART уже позволяет выполнить ближайшие квартальные обязательства.

**Different decisive fact:** Текущая ART-координация обеспечивает обязательства, но LeSS невозможен до реформы отдельных бюджетов.

**Different candidate mistake:** Оплатить framework rollout до появления бюджетных предпосылок власти PO.

**Different actual decision:** Сначала финансировать/согласовать предпосылку; обучение LeSS позже.

**Different strongest reasoning:** Последовательность инвестиции по организационной зависимости, не арбитраж повторяемого спора CPO/CTO/compliance.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-113 → TC-081

**Old collision:** Деньги как универсальная мотивация ↔ диагностика автономии, мастерства и смысла. Production: Провести отдельный разговор о причинах желания уйти; сначала определить ведущий мотив, затем согласовать подходящее изменение работы.

**New diagnostic task:** Руководитель команды согласует удержание сильного PM после stay interview: человек доказал готовность к следующему масштабу, но в команде год не будет ни позиции, ни подходящей программы; соседний продукт предлагает такой scope и готов дать четыре недели на передачу.

**Different decisive fact:** Мотив и готовность доказаны, роста внутри год нет, принимающий продукт и handover доступны.

**Different candidate mistake:** Повторять диагноз/покупать удержание деньгами вместо честной мобильности.

**Different actual decision:** Поддержать переход с передачей.

**Different strongest reasoning:** Не удерживать в недоступном scope, сохраняя непрерывность работы; не выбирать интервенцию при неизвестном мотиве.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-115 → TC-023

**Old collision:** Сразу искать root cause ↔ сначала установить command, роли и контроль изменений. Production: Назначить единое управление инцидентом и остановить несогласованные изменения, затем вести технические действия и коммуникацию через назначенные роли.

**New diagnostic task:** DM на проверке плана аварийного восстановления выбирает один из двух испытанных путей: быстрый резерв поднимает сервис за 6 минут с потерей последних 20 минут записей; восстановление согласованной копии и журнала занимает 18 минут без потерь.

**Different decisive fact:** Сравниваются испытанные пути восстановления с разными RPO и RTO; инцидентные роли уже есть.

**Different candidate mistake:** Оптимизировать только скорость поднятия сервиса.

**Different actual decision:** Выбрать18 минут без потери данных.

**Different strongest reasoning:** Проверить две характеристики восстановления, не preventive insurance против обязательного downtime cap и не установить IC.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-118 → TC-025

**Old collision:** Формула как окончательное решение ↔ использовать framework как вход и отдельно уменьшать ключевую uncertainty. Production: Провести дешёвый поведенческий тест и проверить заранее заданные пороги, откладывая промышленную разработку и отдельно оставляя гипотезу регулярного использования.

**New diagnostic task:** Lead TPM пересобирает scope крупной партнёрской интеграции, которая третий квартал не проходит WSJF по размеру: деление на UI/API/данные создаёт маленькие карточки без самостоятельной ценности, но каталог с существующей оплатой уже позволяет реальные продажи.

**Different decisive fact:** Есть реально самостоятельная продающая вертикаль с общим prerequisite; спрос уже доказан.

**Different candidate mistake:** Уменьшать размер карточек техническим дроблением без независимой ценности.

**Different actual decision:** Пересобрать инвестиционные вертикали и пересчитать портфель.

**Different strongest reasoning:** Создать самостоятельную единицу ценности, не переставлять уже неделимый связанный результат Р–К и не проверять спрос.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-119 → TC-009

**Old collision:** Единый big-bang enforcement ↔ progressive blocking по измеримой readiness. Production: Запустить всем режим предупреждения по категориям риска, затем включать блокировку и поддержку по фактической готовности каждой команды.

**New diagnostic task:** Lead TPM проектирует межкомандный contract gate: проверки приложения зелёные, но backend после них изменил API; бессрочный статус passed позволяет выпустить непроверенную пару версий, а полный регресс всех продуктов на каждое изменение слишком дорог.

**Different decisive fact:** Provider изменился после теста; нужна устойчивая invalidation evidence по затронутым consumers.

**Different candidate mistake:** Считать passed бессрочным или лечить повторение единичным ручным прогоном.

**Different actual decision:** Версионировать свидетельство и автоматически повторять targeted тест при смене релевантного контракта.

**Different strongest reasoning:** Жизненный цикл межкомандного evidence, не разовый recovery test и не rollout gate по зрелости команд.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-120 → TC-039

**Old collision:** Масштабировать framework по числу команд ↔ платить coordination cost только там, где есть общий product flow. Production: Пересобрать роли и границы по карте продуктовых и платформенных зависимостей; оставить общую координацию там, где она сокращает ожидание.

**New diagnostic task:** Head пересматривает operating model ART после трёх PI: в продуктовые обязательства каждый раз включают 100% номинальной capacity, а IP-итерация уходит на доделки; обучение и интеграционные улучшения вытесняются, хотя связи между командами уже выявляются вовремя.

**Different decisive fact:** IP уже в календаре, но feature commitments используют её второй раз; KPI закрепляет механизм.

**Different candidate mistake:** Добавить ещё церемонию/контроль вместо исправления denominator capacity и стимулов.

**Different actual decision:** Исключить защищённое время из обещаний, сменить KPI и явно пересогласовать scope.

**Different strongest reasoning:** Исправить double booking и incentives; не централизовать денежный management reserve под неизвестные риски и не выбирать ширину ART.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-122 → TC-017

**Old collision:** Формальный performance process по симптомам ↔ сначала честный диагностический разговор. Production: Провести диагностический разговор по фактам и обсудить причины, зафиксировав ожидания и поддержку до новой контрольной даты.

**New diagnostic task:** DM завершает восьминедельный PIP: заранее согласованные наблюдаемые цели полностью выполнены, поддержка оказана, новые нарушения не появились; перед сложным релизом руководитель хочет продлить формальный статус ещё на месяц для подстраховки.

**Different decisive fact:** PIP уже завершён успешно; критерии выполнены, оснований продления нет.

**Different candidate mistake:** Держать формальный статус после успеха ради риска обычной поставки.

**Different actual decision:** Закрыть PIP, сохранить обычную защиту релиза.

**Different strongest reasoning:** Честный выход из выполненного процесса, не диагностика просадки или запуск PIP после безуспешной поддержки.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

### TC-125 → TC-013

**Old collision:** Централизованное approval для всего ↔ risk-tiered delegated controls с обязательными guardrails. Production: Перевести типовые операции в самообслуживание и оставить платформе сложные изменения, измеряя ожидание и качество после перехода на новую модель.

**New diagnostic task:** Head согласует с руководителем ИБ новую модель assurance: security champions уже встроены в команды, низкорисковые изменения автоматизированы, но авторы высокорисковых изменений сами подтверждают соблюдение требований под давлением продуктовых KPI; выборочный независимый аудит обнаружил пропуски.

**Different decisive fact:** Типовой спрос уже автоматизирован; high-risk авторы сами подтверждают контроль под delivery KPI.

**Different candidate mistake:** Расширять самообслуживание/обучение, оставляя конфликт интересов оценщика.

**Different actual decision:** Закрепить независимое high-risk assurance с бюджетом и отчётностью.

**Different strongest reasoning:** Разделение обязанностей в смешанной модели; не устранение очереди типовых запросов.

**Classification:** ALLOWED REINFORCEMENT. Original collision: FIXED.

## Cross-bank redesigned rows

Проверены127 comparison edges с58 обязательными уникальными production cases плюс семантическими расширениями. Минимальный набор: context-pack shortlist + original blocker + все same-topic + все same-primary. Дополнительно119 сравнен с037/038/054/055/062,120 с071/098,125 с019/047. Retrieval score не использовался для содержательного вердикта.

| Row | Nearest comparison | Classification |
|---|---|---|
|TC-101|TC-061|ALLOWED REINFORCEMENT|
|TC-102|TC-055|ALLOWED REINFORCEMENT|
|TC-103|TC-010|ALLOWED REINFORCEMENT|
|TC-104|TC-007|ALLOWED REINFORCEMENT|
|TC-105|TC-006|ALLOWED REINFORCEMENT|
|TC-108|TC-044|NO CLOSE ANALOG|
|TC-109|TC-092|NO CLOSE ANALOG|
|TC-111|TC-040|ALLOWED REINFORCEMENT|
|TC-113|TC-081|ALLOWED REINFORCEMENT|
|TC-115|TC-093|ALLOWED REINFORCEMENT|
|TC-118|TC-051|ALLOWED REINFORCEMENT|
|TC-119|TC-037|ALLOWED REINFORCEMENT|
|TC-120|TC-098|ALLOWED REINFORCEMENT|
|TC-122|TC-072|ALLOWED REINFORCEMENT|
|TC-125|TC-013|ALLOWED REINFORCEMENT|

**Row-level total: NO CLOSE ANALOG2; ALLOWED REINFORCEMENT13; NEAR DUPLICATE0; DUPLICATE0.** Это максимум близости для каждой redesigned row, не число пар в CSV. Все13 подтверждены различием decisive condition, действия и проверяемой ошибки; совпадение счётчиков с self-QA не являлось основанием.

Особо проверены возможные новые совпадения:118 против051…053 — вертикальная декомпозиция создаёт самостоятельную ценность вместо перестановки уже заданного неделимого результата;119 против037/055 — механизм срока действия evidence между независимыми релизами вместо разовой репетиции восстановления;120 против098 — capacity denominator и KPI вместо централизации management reserve;125 против019/047 — независимость assurance вместо root-cause review или ремонта ненадёжного scanner.

## Source grounding — SUPPORTED15/15

Source proposition→facts→boundary проверены отдельно от существования runtime codes. Числа, бюджетные сроки,100примеров, готовность человека, технические интерфейсы и проведённые пробы — явно заданные факты сценариев; они не приписываются учебнику как универсальные нормы.

| IDs | Source | Grounded proposition |
|---|---|---|
|TC-101/102/103|t-3-3: таблица Dark launch, примеры ответов, Senior|Редкие тарифы не видны в малой canary; dark launch сравнивает расчёты без пользовательского эффекта, но побочные эффекты и двойная нагрузка требуют отдельной защиты.|
|TC-104/105|t-2-6: реестр, EWI, таблица рисков, уточняющие вопросы|Trigger/EWI должны давать время исполнить response; сигналы и разрешённая политика выбора здесь заданы как факты ситуации.|
|TC-108/109|t-10-4: логи/метрики/трейсы, практическая деталь, кейс3|Логи содержат детали отдельного запроса, метрики — агрегат; sampling экономит хранение. Достаточность100 и отсутствие смещения — явные условия сценария, не универсальная норма учебника.|
|TC-111|t-4-3: LeSS, Head, кейс2|Без полномочного PO и единого продуктового бюджета LeSS не реализуется; временная ART-координация и последующая бюджетная реформа — разные этапы инвестиции.|
|TC-113|t-7-4: удержание сильных, отдельный случай потолка, Middle|Если человек перерос роль, а следующей нет, честное отпускание/переход сохраняет отношения; деньги не устраняют карьерный потолок. Handover и заместитель — явные факты.|
|TC-115|t-10-6: RPO и RTO|RTO — длительность восстановления, RPO — допустимая потеря данных во времени. Проверенный план должен удовлетворять обоим; числа6/20 и18/0 — условия, а не нормы источника.|
|TC-118|t-9-3: таблица WSJF, Senior, кейс1|Крупную ценную инициативу следует разбить на полезные части, а не вечно откладывать; каталог с существующим шлюзом даёт продажи. Зависимости и стоимость вытеснения остаются в сравнении.|
|TC-119|t-3-2: контрактный gate, кейс1|Контрактные тесты должны проходить на актуальной версии API; изменение контракта уведомляет потребителей. Привязка evidence к версии и targeted invalidation — реализация этого требования, не внешняя норма.|
|TC-120|t-4-3: SAFe/ART/IP, Head, антипаттерны|ART — единица планирования ёмкости; IP, съеденная доделками, — провал. В сценарии прямо дан механизм двойного бронирования и KPI; политика capacity устраняет его, не отменяя координацию.|
|TC-122|t-7-6: таблица PIP / последствия|Выполнен — PIP закрыт, обычный ритм; критерии и последствия известны заранее. Успех не обосновывает бессрочное продление формального статуса.|
|TC-125|t-10-7: разделение обязанностей, Head, кейс3|Разделение авторства и контроля; Head выбирает embedded партнёрство либо независимый контроль. Champions и автоматизация не отменяют независимую high-risk оценку.|

## Level feasibility — PASS13/15

Требуемые операции и why-lower-insufficient для всех15 строк приведены в level-audit.csv. Пять Senior101/102/103/118/119 проходят: архитектурные предпосылки безопасного двойного исполнения; либо изменение единицы инвестиции/учёт общих prerequisites; либо механизм жизни versioned evidence. Три Head111/120/125 проходят: бюджетные полномочия PO и этапы трансформации; модель общих обещаний/стимулов; независимость контроля с бюджетом и отчётностью. Это конкретные полномочия и последствия, не численность или должность.

Junior104/105: явное сравнение времени готового response. Middle108/109: цена хранения и сохранение расследуемого evidence, при этом точный счётчик не заменяет подробные примеры; sampling на высокой/низкой частоте приводит к разным диагностическим последствиям. Middle113: управляемая передача delivery при честном карьерном переходе. Эти blueprint допускают предметные competing alternatives без нового проектирования темы.

FAIL115 и122: уже готовое правило допустимости/выхода полностью задаёт ответ. Рекомендуемый уровень текущей конструкции Junior; сохранение Middle требует добавить содержательную развилку внутри той же темы. Не менять уровни ради распределения.

## Sibling integrity and changed families — PASS3/3

101/102 необходимы из-за замены общей triplet-задачи миграции на изоляцию shadow;104 — из-за перехода от risk/issue к response lead time;109 — из-за перехода от причинного сигнала к частоте сохраняемых логов. Сохранить прежние siblings означало бы разные base situations/strategy spaces. Лишняя независимая mutation не добавлена; cross-bank и source/level всех четырёх siblings проверены.

### F-TD-T01

Изоляция уже доказана→использовать; весь периметр на существующем интерфейсе→адаптер за2недели; эффекты обходят интерфейс→новый шов6недель и перенос. Две границы: готовность изоляции и полнота доступного периметра. Это одна ordered logical variable; duration — фиксированная стоимость разных стратегий, не дополнительная мутация.

Same topic/domain/level, actor/objective/base, strategy space и constants: **PASS**. Hidden independent mutation: **NONE**.
### F-PM-P01

Response1д<=3д: поздний сигнал;3<response5д<=7: ранний. Меняется только длительность подготовки, оба источника и цена раннего резервирования постоянны. Разные сигналы — не разные исходные вероятности.

Same topic/domain/level, actor/objective/base, strategy space и constants: **PASS**. Hidden independent mutation: **NONE**.
### F-PA-P02

10млн×1КБ≈10ГБ>1ГБ;1%даёт100000примеров и≈0.1ГБ.500×1КБ≈0.5МБ;1%даёт5<100примеров. Меняется только частота; объём/число сохранённых примеров — вычисляемые следствия. Отсутствие sampling bias закреплено в constants.

Same topic/domain/level, actor/objective/base, strategy space и constants: **PASS**. Hidden independent mutation: **NONE**.

F-TD-T01: в101 готовая изоляция уже доказана; в102 её можно построить на имеющейся полной границе; в103 сама граница неполна. Два перехода не просто переименовывают объяснение: меняется работа, срок и возможность shadow сейчас. Шесть недель архитектурной работы и две недели адаптера закреплены одинаковыми условными затратами стратегий для всей семьи. У103 отсутствие реальных списаний — нормативное ограничение, не утверждение, что текущая реализация уже его обеспечивает.

F-PA-P02: репрезентативность100примеров и отсутствие смещения обязательны при authoring в context; исключение их сделает выбор unsupported. Это сохранение имеющегося family contract, не новая правка. Literal question/options нельзя проверить до создания кейсов; здесь проверена blueprint-feasibility.

## Internal and future sanity

Internal: **255 уникальных пар**, в которых хотя бы одна строка redesigned (15×10 + C(15,2)); unchanged↔unchanged не пересматривались. Пять sibling contrasts среди changed rows — намеренные family comparisons. **NEAR DUPLICATE0, DUPLICATE0**. Внутри batch:104/105 про срок готового response,117 про дорогую реакцию на EWI;108/109 про объём подробных логов,116 про минимизацию ПДн;115 про допустимость recovery,124 про mitigation до root cause;111 про предпосылку инвестиции в LeSS,120 про double-booking IP,125 про независимость assurance.

Future: проверены только74 указанных tooling связей с будущими строками; **obvious collisions0**. Это не approval диапазона126…300. В частности:120/185 отличаются двойным обещанием уже обозначенной IP-capacity и исполнением postmortem actions без мощности/обзора;119/199 — invalidation release evidence после изменения артефакта против ранней проработки контрактов до планирования;118/198 — инвестиционные вертикали против этапов технической миграции.

## Runtime and coverage — PASS

Текущий TrainerScoringMapping.swift заново скомпилирован штатным RuntimeProbe. Unknown codes **0**. Все derivedRuntime поля changed rows совпадают с реальным mapping. Семантика patterns проверена по задаче: risk-based-testing/safeguards для shadow evidence; risk-register/early-warning-response для lead time; process-economics/quality-metrics для sampling; team-topologies/change-management/resource-conflict для бюджетной предпосылки LeSS; expectation-management/one-on-one/support для мобильности; risk-differentiation/reliability/safeguards для двух измерений recovery; portfolio-reprioritization/dependency-management/cost-of-delay для вертикалей; api-contracts/versioning/evidence-before-release для актуальности gate; resource-conflict/change-management/process-economics для IP; formal-performance-management/performance/expectation-management для честного закрытия; roles/accountability/safeguards для assurance.

Остатков старой boundary, маскирующихся валидным runtime alias, не обнаружено. Веса по engine:primary1,secondary0.5,max внутри категории,нормировка case≤1,context исключён. Независимо пересчитаны7 coverage pools, primary/secondary/union IDs, distinct counts и нормированные веса. Ошибок0; runtime_coverage равен masterplan coverage. Artifact hashes candidate и pack проверены.

Schema/options/DQ/surface leakage для новых полных кейсов: **NOT_APPLICABLE**, их в этой manifest-задаче не создавали. PASS runtime не является content approval. Уровневые дефекты остаются независимо от успешного mapping.

## Final decision and retest

**MANIFEST v2.2.4 READY TO FREEZE: NO.**

Минимальный набор: исправить calibration115/122 согласованным изменением уровня либо усилить их реальную decision boundary для Middle; обновить связанные whyLevel/coverage, сохранив остальные строки и family contracts. Затем focused QA этих двух строк, их новых ближайших аналогов и diff/runtime/coverage. Полный QA275rows не требуется.

Candidate, baseline, textbook, runtime и production не изменены. Freeze/import, создание cases, Batch04 authoring и commit/push не выполнялись.
