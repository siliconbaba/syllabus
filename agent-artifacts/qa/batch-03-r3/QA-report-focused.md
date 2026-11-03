# Final independent focused QA — Batch 03 r3 + manifest v2.2.3-candidate

**READY FOR FREEZE + IMPORT**. Blocker **0**, Major **0**, Minor **0**. Remaining IDs: **[]**.

## Scope and evidence

Независимо проверены новый manifest TC-085 и полный r3 TC-085, diff manifest и batch, metadata всего batch, schema/runtime, дубли TC-085 против всех 75 production cases и формальные признаки 25/100 кейсов. Авторские changelog/hotfix report/self-QA не использовались как основание вердикта.

Для остальных 24 кейсов применено прямо разрешённое в п.14 задания наследование результатов r2 после проверки побайтовой идентичности исходных JSON-объектов. Это не новый полный содержательный аудит этих кейсов. Отдельного independent QA каталога batch-03-r2 в workspace нет; исходный QA batch-03 относится к r1. Основание наследования — текущая инструкция пользователя о результатах r2, а не подмена авторского self-QA независимым отчётом.

## Manifest diff — PASS

Сравнение masterplan и CSV выполнено до чтения любых авторских отчётов. Изменена ровно **1 planned row: TC-085**; **274** строки идентичны. Все **43 family contracts**, family CSV, batchPlan, eligibility и structural totals неизменны. Вне строки085 изменены только manifestVersion и ожидаемые thinking aggregates. Сохранены topic t-3-9, domain release_and_quality, Middle, standalone, training/assessment=true.

Замена patterns: evidence-before-release + risk-based-testing/regression-evidence → process-economics + bottleneck. Runtime: Delivery и релизы; proportionality + dependencies. Нормированные веса старого кейса evidence2/3,risk1/3 заменяются proportionality2/3,dependencies1/3; оба старых risk aliases давали один вес. Независимая проверка всех aggregate deltas и membership: ошибок0. runtime_coverage совпадает с masterplan; все manifest artifact hashes сходятся. Unexpected semantic diff **0**.

## Необходимость hotfix и differentiation — PASS

- **TC-004 tests:** слабая автоматика не закрывает критичный/соседний regression risk; выбрать достаточный targeted manual regression и ограниченную раскатку вместо smoke/full wait.
- **Old TC-085 tested:** локализованный impact + достаточный targeted набор + дорогой full regression → выбрать targeted. Центральное решение уже реализовано в TC-004; отсутствие hotfix в сюжете не создавало честной новой диагностической границы.
- **New TC-085 tests:** покрытие фиксировано; выбрать вложение в подготовку расходуемых согласованных данных по полной стоимости шести циклов и готовности первого запуска.
- **Different decisive fact:** данные требуют4ч восстановления перед каждым прогоном; выполнение2ч; очередь среды отсутствует; восстановление как код стоит12ч и затем0.5ч.
- **Different candidate mistake:** инвестировать в видимое выполнение тестов/лишний стенд или экономить разовое вложение, игнорируя повторную подготовку. Это не недооценка regression evidence.
- **Different actual decision:** восстановление исходного состояния вместо изменения набора проверок и rollout.
- **Different strongest reasoning:** найти компонент затрат и проверить полную ёмкость на горизонте; не выбирать достаточную глубину regression по impact.

И manifest, и полный r3 TC-085 против TC-004: **ALLOWED REINFORCEMENT**, не near duplicate. Проверка остальных74 production cases не выявила нового collision; по75 сравнениям: 7 ALLOWED REINFORCEMENT,68 NO CLOSE ANALOG. Подробности — duplication-audit-focused.csv. Общие мотивы экономики/узкого места в008,013,042 не тождественны новой задаче.

## Source grounding — SUPPORTED

Прочитан непосредственно authoritative `InteractiveBook/WebContent/index.html`, topic **t-3-9**, а не авторский source-trace. Раздел «Тестовые данные» объясняет расходование состояния платежами, межсистемную согласованность и наборы данных как код с восстановлением перед регрессом. В «Примерах ответов» сильный ответ сначала разделяет полный цикл на выполнение, ожидание среды/данных, разбор и повторение; слабый сразу покупает автоматизацию. Раздел «Автоматизация» связывает выбор с частотой, стабильностью и экономикой.

Цепочка source → scenario → facts → decision: повторяемые проверки расходуют согласованные данные → шесть прогонов одного продукта → подготовка4ч, исполнение2ч, подтверждённая возможность восстановления0.5ч после12ч вложения → выбрать работу на действительном ограничителе, сохраняя coverage. Числа — конкретизация ситуации, не внешняя методология. Все технические предпосылки реализации даны в context, включая проверку трёх систем и стабильность схемы.

## TC-085 blind / pairwise — PASS

До explanation, DQ и metadata выбран **C**. Candidate key **C**. Agreement **YES**, uniquely strongest **1**.

| Option | Полный труд, ч | Подготовка к первому старту, ч | Ограничение |
|---|---:|---:|---|
| A |16+6×(4+0.5)=43|16+4=20|Превышает30 и16|
| B |4+6×(4+2)=40|4+4=8|Превышает30|
| C |12+6×(0.5+2)=27|12+0.5=12.5|Оба ограничения соблюдены|
| D |6×(4+2)=36|4|Превышает30|

C>A: автоматизация сокращает только выполнение, сохраняет повторную подготовку и не помещается в ресурсы. C>B: среды уже свободны, последовательные прогоны не ускоряются, ручное восстановление остаётся. C>D: подготовка заранее переносит труд, но не уменьшает36ч до30ч. Для каждого сравнения достаточно context; скрытое предположение не нужно.

Distractors профессионально узнаваемы: automation-first, environment-first, отказ от инженерного вложения в пользу надёжной ручной процедуры. D — сильная альтернатива, пока не учтён весь горизонт. Все options содержат конкретный способ подготовки/исполнения; correct не единственный профессионально конкретный и не самый длинный.

DQ C1 > D0.82 > A0.65 > B0.45 разумен: D сохраняет проверенный способ без вложений, A ускоряет реальную часть работы, B добавляет ресурс без существующей очереди. Шкала не обязана быть линейной функцией перерасхода часов; инверсии reasoning не обнаружены.

Explanations выводят механизм и арифметику из context. Все три decisiveFacts доступны до ответа. MentalModel переносим: разделить подготовку и выполнение, сравнить разовое и повторяющееся на заданном горизонте. Нет вывода причинности из корреляции.

whenItWouldBeBest покрывают целые варианты: A — выполнение доминирует, подготовка дешева, вся цена/срок лучше альтернатив; B — реальная очередь среды и оправданная настройка с ручным восстановлением; C — расходуемые согласованные данные и выгодная полная экономика; D — мало прогонов/нестабильные данные, ручные наборы дешевле и помещаются. Невыполнимых обещаний нет.

## Middle realization — PASS

Required **Middle**. Нужно разложить регресс на разные виды работ, сопоставить разовые вложения с шестью повторениями и проверить два ресурсных ограничения при фиксированном качестве. Junior-знания о пирамидах, средах или лозунга «автоматизируй» недостаточно. Senior redesign не требуется: один продукт, подтверждённые локальные решения, без проектирования общей quality platform. Количество чисел само по себе не основание уровня; основание — operational trade-off между competing investments.

## Batch regression / inherited fixes — PASS

r2→r3: changed cases **1: TC-085**; остальные **24 raw JSON objects byte-identical**. Сравнивались исходные фрагменты между границами JSON-объектов, не только заново сериализованные структуры. Для каждого сохранены SHA-256. Корневые поля кроме cases неизменны. Unexpected regression **0**.

Сохранились разрешённые к наследованию результаты: TC-090 unique/source PASS; TC-083/084/094/100 level PASS; остальные локальные исправления r2; **4/4 families PASS**. Девять linked instances имеют неизменные context/options/metadata; четыре family contracts не изменились, одинаковые question/options внутри семей сохранены. Повторного редакторского аудита семей не проводилось.

Collision fixes076/047,079/011,087/019,088/016,091/013,093/006 также сохранены: соответствующие authored cases и их manifest rows не изменились.

## Whole-batch gates

25 cases;100 options;16 standalone;9 linked;4 families; **J5/M12/S5/H3**. Unique strongest **25/25**, source grounded **25/25**: 24 наследованных результата + новый независимый TC-085 PASS. Manifest metadata **25/25** независимо сверены с candidate, который сохраняет остальные строки frozen v2.2.2. Eligibility соответствует standalone/linked policy. Один isBest=true и один decisionQuality1 на каждом кейсе; они совпадают. ID076…100 без дублей и пропусков.

Штатный `TrainerBank.load` собран из текущих production Swift-файлов и запущен на всём r3: **schema PASS, runtime PASS; unknown domain0, unknown patterns0**. Лог сохранён. Это targeted content validator, не утверждение о запуске полного UI/build regression suite.

## Surface leakage — PASS

Независимо пересчитаны option.text production75, baseline r2, r3 и hypothetical100: **19 features,78 min/max и combined rules**. Есть words/chars, longest/shortest, Latin fragments, numbers, «и», punctuation/clauses, infinitive-action heuristic, conditions/order, management noun endings, concrete prefixes и дополнительные символы. Метод и сырые features/rules сохранены в JSON и воспроизводимом скрипте; action count — явная приблизительная эвристика, не морфологическая разметка.

| Metric | r2 | r3 | production75+r3 |
|---|---:|---:|---:|
| Best rule, ties first A/B/C/D |10/25|10/25|33/100|
| Max expected hits, uniform ties |9.33|9.33|31.00|
| Max-statistic family-preserving permutation p |0.623|0.607|0.601|
| Longest words, first tie |3/25|3/25|21/100|
| Shortest words, first tie |6/25|6/25|26/100|

r3 correct имеет максимальную длину по словам9раз с учётом ничьих, строго единственный максимум2раз; random-tie ожидаемые попадания4.67/25. Средняя длина correct/distractors15.96/16.19слов и129.48/129.69символа. На100 —16.33/16.35слов. Позиции r3 **A6/B6/C6/D7**, global **A24/B24/C25/D27**.

Лучший batch-rule — минимальное число infinitive-action маркеров; максимум10/25 остался прежним. Global максимум33/100 дают сочетания specificityProxy/punctuation. Это найденные постфактум максимумы среди78 правил; permutation сохраняет общую перестановку ключей внутри каждой family и учитывает поиск максимума (2000 итераций). Результаты не показывают существенного системного cue в проверенном наборе. Они не доказывают невозможность всех будущих эвристик.

## Final

**BATCH 03: READY FOR FREEZE + IMPORT.** Remaining IDs **[]**. Candidate/manifest не изменены, freeze/import не выполнены, Batch04 не начат, commit/push не выполнялись.
