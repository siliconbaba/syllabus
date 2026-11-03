# Независимый финальный QA manifest v2.1

**NOT READY. Можно начинать Batch 01: NO.**

Проверены файлы candidate непосредственно из `agent-artifacts/manifests/v2.1/`. Production manifest не изменён; новые кейсы не создавались. Единственный содержательный источник — текущий `InteractiveBook/WebContent/index.html`. Runtime-контракт сверялся с фактическими Swift mapping/engine/store и `docs/TRAINER-CONTENT-SCHEMA.md`.

Причина остановки — повторяющаяся некорректная калибровка уровней и недоказанные границы части linked-конструкций, в том числе первой семьи Batch 01. Неравномерность coverage, отсутствие полных options и литературная форма концептов дефектами не считались.

**Счётчики:** 2 системных blocker-вывода; 38 конкретных major-записей (34 уникальные строки и 4 семьи); 0 minor. Major-записи детализируют системные выводы и отдельные ошибки metadata, поэтому эти числа не следует складывать как количество независимых первопричин. Один ID с несколькими замечаниями занимает одну строку CSV.

## 1. Structural gate — PASS

Независимый программный пересчёт, а не принятие авторских счётчиков:

- 275 новых: 181 standalone и 94 linked instances.
- 35 pair families и 8 triplets; всего 43 семьи.
- 11 batches по 25; семьи не разрезаны между batches.
- Новые уровни: Junior 43 / Middle 99 / Senior 88 / Head 45.
- Совместно с существующими gold: 300 cases = 200 standalone + 100 linked instances.
- TC-026…TC-300 идут без пропусков и дублей; membership однократный и полный; topic/domain/level внутри каждой семьи одинаковы.
- partId/topicId существуют и связаны правильно по HTML учебника. Это структурная валидность, а не подтверждение семантической уместности каждой темы.
- Все новые trainingEligible=true; standalone assessmentEligible=true, linked assessmentEligible=false.
- CSV и JSON совпадают по всем экспортированным полям после декодирования JSON/списков/boolean.
- Все 7 SHA-256 из artifact-hashes.json подтверждены. Хэши фактических Swift mapping/engine совпадают с runtime contract.

Полные воспроизводимые результаты: `independent-checks.json`. Содержательная корректность не следует из отсутствия schema errors.

## 2. Standalone audit — FIX

Прочитаны все 181 standalone: scenario, decisiveFactsConcept, boundary и metadata. Концепты содержат действующих лиц, конкретные конфликты и 1–3 факта; массовых пустых placeholders или универсальных лозунгов вместо ситуации не обнаружено. Полный вопрос и четыре варианта на manifest-стадии не требовались.

У 23 standalone есть обязательные замечания в row-fixes-final.csv; у остальных 158 содержательных исправлений в рамках этого аудита не зарегистрировано. Это допуск концепта к авторингу, а не гарантия единственного strongest в ещё не написанных options.

Главная проблема — не отсутствие фабулы, а несовпадение измеряемого рассуждения с заявленным уровнем или pattern. Например:

- TC-075: не останавливать тест на девятый день при precommitted 14 днях и отсутствии early-stop rule — Junior в §13.3, а не Senior.
- TC-072, TC-122, TC-217: диагностика, формальный performance process и своевременный HR описаны в Middle §7.6. В данных ситуациях нет Senior-задачи по менеджеру/лиду и последствий управления этой ролью.
- TC-092 и TC-100: чтение хвоста распределения/выбор actionable alert не превращаются в Senior из-за названия роли; §10.4 отдельно описывает межкомандные требования наблюдаемости.
- TC-300 воспроизводит прямо описанную в §8.2 ошибку: судить по оплате без законтрактованных обязательств. Никакого нового Senior trade-off условие не требует.

Рекомендуемые уровни и минимальные правки даны по каждому ID. Не требуется сохранять исходные пропорции уровней ценой искусственного усложнения. Предпочтительна честная переклассификация существующей задачи.

Диагностические повторы: TC-144/273 оба проверяют защиту денежной операции от повторной обработки; различие producer retry и повторной доставки consumer пока не задаёт иной управленческой boundary. У F-PR-P01 и F-TD-P03 совпадает сам диагностический контраст временной/устойчивой очереди; одновременно уровни Junior и Senior расходятся без содержательного основания.

## 3. Source-semantic audit и vocabulary — FIX

Сопоставлялась цепочка topic → scenario → decisive facts → boundary → domain → patterns → level для 275 строк. Большинство решений связаны с учебником; механического требования расширять coverage нет. Но остались точные случаи маскировки одной компетенции узким кодом другой:

| ID | Несоответствие |
|---|---|
| TC-144, TC-273 | rollback-data-awareness поставлен на идемпотентность повторной обработки; возврата версии/данных нет |
| TC-145 | risk-to-issue-transition поставлен на критерии expedite-класса |
| TC-214 | risk-based-hotfix поставлен на cache invalidation, hotfix отсутствует |
| TC-116, TC-216, TC-194 | decision-at-right-level использован для PII safeguards, коммуникационного режима или eligibility поставщика, хотя полномочия не являются boundary |
| TC-112, TC-224 | early-bad-news используется при согласовании ожиданий/фиксации решения без плохого прогноза |
| TC-288 | blameless и тема 7.10 поставлены на устойчивую перегрузку; основной источник — 7.9 |

Это содержательные замечания: например, decision-at-right-level начисляет organizational thinking за решение, не проверяющее authority. Дедупликация runtime не исправляет неверную классификацию. Минимальные замены существующими подходящими кодами указаны в CSV; не нужно придумывать инцидент или rollback, чтобы оправдать metadata.

**Negotiation vocabulary:** новые коды реально присутствуют в authoritative mapping и различаются в schema. TC-064, TC-168, TC-255/256 действительно содержат BATNA/цену несоглашения, а TC-121/192 — интересы и пакетирование обмена. Их больше не маскируют contract model или escalation. TC-121/192 замечаний по этому основанию не требуют. Однако правильный код не исправляет Head-калибровку TC-064/168 и недоказанный flip TC-255/256: см. ниже. Не расширять negotiation-batna до любых переговоров или до integrative trade как взаимозаменяемого alias.

## 4. Linked families — 43 проверены, 4 требуют правок

Construction PASS означает достаточную manifest-level логическую развилку; level FIX учитывается отдельно. Из 8 triplets две требуют уточнения конструкции. Для остальных разрешено превратить уже заданные состояния в полные условия при авторинге; полные options от manifest не требовались.

### Обязательные family FIX

1. **F-PM-T01 (TC-026…028).** Буфер 5 и сдвиги 1/4/8 не определяют обе заявленные границы. Для 4 не указано, почему обычного контроля уже недостаточно; для 8 не известен предел одинаковых доступных mitigation. Превышение буфера ещё не доказывает невозможность ускорения. Нужны общие trigger, цена/предел ускорения и максимальное восстановление; только сдвиг меняется. Это непосредственно блокирует авторинг первой семьи Batch 01 без допроектирования её автором.
2. **F-PE-T01 (TC-176…178).** В первом состоянии дополнительно заканчивается пик; следующие различаются возможностью переноса/достаточностью локальных мер. Проценты 5/25/50 сами не дают границ. Зафиксировать одинаковый горизонт нагрузки и одинаковые пределы доступного переноса/восстановления, варьировать только demand. Учебник §7.9 поддерживает управление нагрузкой, но не устанавливает универсальные thresholds 5/25/50.
3. **F-ST-P03 (TC-255/256).** Защита reservation point и поиск взаимовыгодных уступок не противоположны. Слабая BATNA понижает нижнюю границу, но не отменяет её; сильная BATNA не отменяет интересы сторон. Нужна единая конкретная сделка/момент решения, выгодная относительно одной BATNA и невыгодная относительно другой; остальные возможности обмена неизменны. Это реальный flip, а не смена тона объяснения.
4. **F-TD-P03 (TC-253/254).** Сама mutation работоспособна, но диагностически повторяет F-PR-P01 (TC-106/107), с необоснованным разрывом Junior/Senior. Развести предмет выбора, сохранив ID и одну mutation; одна смена слов не создаёт новую диагностическую задачу.

### Все triplets

| Family | Construction | Основание |
|---|---|---|
| F-PM-T01 | FIX | Не задана мощность mitigation и первая граница |
| F-DM-T01 | PASS | Defer / next slot / preempt — разные решения при двух экономических границах; числовой авторинг должен использовать общий горизонт сравнения |
| F-DR-T01 | PASS | Warning / частичный blocking / полный blocking по готовности проверок; общий exception process не должен стать дополнительной mutation |
| F-TD-T01 | PASS | Code rollback / проверенное recovery в окне / переделка compatibility до релиза — три состояния восстановимости |
| F-PR-T01 | PASS | Единый процесс / общий каркас с адаптацией / общие принципы при различной однородности работы |
| F-ST-T01 | PASS | Рабочее разрешение / подготовленный trigger / немедленная эскалация по доступному float |
| F-PE-T01 | FIX | Временность пика и пределы переноса не удержаны как общие условия |
| F-PO-T01 | PASS, level FIX | Два заранее заданных policy thresholds работают; их применение не является Head-design |

Ниже полный реестр конструкций; PASS не отменяет row-level metadata/level FIX.

| Family | Members | Construction |
|---|---|---|
| F-PM-T01 | TC-026, TC-027, TC-028 | FIX |
| F-BV-P01 | TC-029, TC-030 | PASS |
| F-PA-P01 | TC-031, TC-032 | PASS |
| F-DM-P01 | TC-033, TC-034 | PASS |
| F-DM-T01 | TC-051, TC-052, TC-053 | PASS |
| F-DR-P01 | TC-054, TC-055 | PASS |
| F-ST-P01 | TC-056, TC-057 | PASS |
| F-PO-P01 | TC-058, TC-059 | PASS |
| F-DR-T01 | TC-076, TC-077, TC-078 | PASS |
| F-TD-P01 | TC-079, TC-080 | PASS |
| F-PE-P01 | TC-081, TC-082 | PASS |
| F-BV-P02 | TC-083, TC-084 | PASS |
| F-TD-T01 | TC-101, TC-102, TC-103 | PASS |
| F-PM-P01 | TC-104, TC-105 | PASS |
| F-PR-P01 | TC-106, TC-107 | PASS |
| F-PA-P02 | TC-108, TC-109 | PASS |
| F-PR-T01 | TC-126, TC-127, TC-128 | PASS |
| F-DM-P02 | TC-129, TC-130 | PASS |
| F-DR-P02 | TC-131, TC-132 | PASS |
| F-PO-P02 | TC-133, TC-134 | PASS |
| F-ST-T01 | TC-151, TC-152, TC-153 | PASS |
| F-TD-P02 | TC-154, TC-155 | PASS |
| F-ST-P02 | TC-156, TC-157 | PASS |
| F-PE-T01 | TC-176, TC-177, TC-178 | FIX |
| F-PE-P02 | TC-179, TC-180 | PASS |
| F-BV-P03 | TC-181, TC-182 | PASS |
| F-PO-T01 | TC-201, TC-202, TC-203 | PASS |
| F-PM-P02 | TC-204, TC-205 | PASS |
| F-PA-P03 | TC-206, TC-207 | PASS |
| F-DM-P03 | TC-226, TC-227 | PASS |
| F-DR-P03 | TC-228, TC-229 | PASS |
| F-PR-P02 | TC-230, TC-231 | PASS |
| F-BV-P04 | TC-232, TC-233 | PASS |
| F-PO-P03 | TC-234, TC-235 | PASS |
| F-PM-P03 | TC-251, TC-252 | PASS |
| F-TD-P03 | TC-253, TC-254 | FIX |
| F-ST-P03 | TC-255, TC-256 | FIX |
| F-PE-P03 | TC-257, TC-258 | PASS |
| F-PA-P04 | TC-259, TC-260 | PASS |
| F-DM-P04 | TC-276, TC-277 | PASS |
| F-DR-P04 | TC-278, TC-279 | PASS |
| F-PR-P03 | TC-280, TC-281 | PASS |
| F-PO-P04 | TC-282, TC-283 | PASS |

## 5. Head calibration — FIX

Проверены все 45 Head, включая whyHead, authorityScope и secondaryEffect. Для 10 строк уровень Head не подтверждён ситуацией: **TC-064, TC-168, TC-194, TC-201/202/203, TC-255/256, TC-282/283**. У остальных 35 обязательного Head-fix в этом аудите нет.

- 064/168 и 255/256: подготовка/использование BATNA без необходимого организационного решения. §6.6 относит подготовку BATNA и обмен вариантами уже к Middle; должность директора сама по себе уровень не поднимает.
- 194: hard-constraint при выборе поставщика. whyHead утверждает изменение sourcing-архитектуры, которого в предмете выбора нет.
- 201…203: в baseSituation буквально «применяет заранее согласованную error-budget policy». whyHead утверждает, что нужно «задать governance/operating model» — другое действие. §10.5 различает использование бюджета командой, разработку policy и Head SRE/portfolio-модель.
- 282/283: определение границы command structure во время инцидента; §10.6 относит cross-team incident management к Senior. Head-работа с культурой/инвестициями/топ-коммуникацией не требуется выбором.

Для согласованности linked-уровень меняется всей семье: F-PO-T01 → Middle, F-PO-P04 → Senior, F-ST-P03 после исправления развилки → Middle. Не добавлять декоративную «системность» только в whyHead.

## 6. Runtime/scoring — технический PASS

Перечитаны фактические TrainerScoringMapping.swift, TrainerScoringEngine.swift и eligibility в TrainerStore.swift. Вне формальной сверки metadata содержательные ошибки перечислены выше.

- unknown domain = 0; unknown pattern = 0; provisional rows = 0.
- derivedRuntimeUiDomain, derivedRuntimePrimaryThinking и весь ordered массив derivedRuntimeSecondaryThinking совпадают с mapping для всех 275 строк.
- Primary raw weight = 1; secondary = 0.5; одна категория внутри case объединяется через max; деление на max(1, сумму весов) ограничивает влияние case единицей.
- Confidence использует число distinct cases: first clean assessment дедуплицирован по case ID; category count увеличивается один раз после слияния aliases.
- Context category явно исключена из scored thinking. **Context sensitivity scored evidence = 0.** futureContextSensitivityCandidate не превращается в runtime score.
- Алиасы не удваивают вес категории. Это свойство engine; оно не означает, что все выбранные authorship patterns семантически верны.

## 7. Coverage и assessment feasibility — формальный PASS

| Runtime area | Все 300 | Planned assessment 200 | Senior+Head evidence в pool |
|---|---:|---:|---:|
| Управление проектами | 29 | 18 | 6 |
| Delivery и релизы | 27 | 12 | 2 |
| Процессы | 44 | 30 | 14 |
| Стейкхолдеры | 29 | 20 | 9 |
| Люди | 36 | 23 | 11 |
| Финансы и подрядчики | 25 | 19 | 8 |
| Портфель и стратегия | 30 | 17 | 7 |
| Технический TPM | 49 | 38 | 20 |
| Аналитика | 16 | 12 | 3 |
| Продукт | 15 | 11 | 4 |

Planned pool: **J31 / M85 / S58 / H26**. Каждая level bucket содержит больше minimumLevelEvidence=5. Все UI areas имеют не менее 11 cases; evidence для отображаемого профиля возможно. Равенство числа cases не требуется; предметной дыры только из различия счётчиков не следует.

Фактический Head breadth gate: ≥3 Senior/Head cases в ≥5 областях, среди них people или stakeholders и portfolio или finance. Проходят **9 областей**, все кроме Delivery; необходимые группы присутствуют. Это проверка способности пула дать evidence, а не гарантия конкретной сессии или квалификации пользователя. Accuracy thresholds уровней остаются отдельным условием.

После только перечисленных переклассификаций формальная breadth-feasibility сохраняется (8 областей). Следовательно, блокер — смысл level evidence, а не нехватка количества. Не нужно искусственно возвращать неверные Head/Senior ради исходной симметрии.

## 8. Eligibility и зависимость siblings — PASS для planned policy

Новые standalone: training=true / assessment=true. Новые linked: training=true / assessment=false. Store отбирает assessmentEligible и unseen; при исключении всех linked siblings не попадают в обычную диагностику. Сам engine дедуплицирует ID, но не заменяет эту policy family-aware логикой.

В текущем gold JSON шесть linked TC-001/002, TC-003/004, TC-017/018 ещё имеют assessmentEligible=true. Поэтому 200 — **планируемый** пул после заявленной миграции; с текущими gold-флагами и новыми standalone было бы 206. Это подтверждённая зависимость deployment, не новый manifest-дефект: пользователь явно задал planned exclusion. До обычного diagnostic expansion миграцию шести флагов нужно выполнить. Существующие snapshots нельзя переписывать. Slice 5 не проектировался.

## 9. Validation-result и WebKit

Сверены validation-result.json, check.log, remaining-checks.log, порядок scripts/check.sh и timeout в Tests/WebKitSmoke.swift.

- В check.log есть PASS trainer/scoring/schema/snapshot, runtime reference sync и **BUILD SUCCEEDED**.
- Единственная строка failing check — **FAIL: timeout**, после **Loaded test phase 0**.
- Первая WebKit invocation по scripts/check.sh — **390×760**; в smoke-test задан таймер **180 секунд**. Из-за set -e дальнейшие WebKit 320×568 и 1280×900 не подтверждены этим запуском.
- remaining-checks.log подтверждает отдельные PASS speech/engine/saved/pronunciation targeted checks. Диагностический список uncovered pronunciation tokens не является failed check.
- Полный check.sh повторно не запускался. Подтверждён состав сохранённых результатов, а не новое успешное прохождение всего pipeline. Причина самого зависания не диагностировалась; доказанного functional regression manifest/scoring в этих логах нет.

**NON-BLOCKING FOR MANIFEST**  
**SEPARATE WORK ENGINEERING ISSUE**

WebKit timeout не является причиной NOT READY.

## 10. Что требуется до авторинга

1. Исполнить точные row-fixes: согласовать уровни с реальной сложностью, убрать неподдержанные узкие patterns/темы. Не добирать Senior/Head искусственно ради квот.
2. Уточнить две triplet-конструкции и BATNA flip; развести повтор F-PR-P01/F-TD-P03 по реальному предмету решения.
3. Пересчитать производные coverage/Head audit после содержательных правок; проверить согласованность CSV/JSON и новые hashes.
4. Провести повторный QA изменённых строк, слепой mutation-check четырёх семей и общий level/runtime/assessment regression gate. Полностью переписывать или повторно литературно проверять остальные концепты не требуется.

Здесь не подходит READY WITH LOCAL FIXES: неверные уровни повторяются в нескольких предметных областях и затрагивают функцию scoring, а первая triplet уже требует допроектирования границ. Новый candidate оправдан этими blocker-дефектами, не косметикой. Текущий blueprint не следует фиксировать как production baseline для Batch 01.

**Можно начинать Batch 01: NO.**
