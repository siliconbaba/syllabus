# Batch 02 r2 — targeted revision

**NOT READY. READY FOR FOCUSED QA: NO.** Сохраняется B02-01: **TC-075 — UNRESOLVED: manifest-level duplicate**. Остальные четыре MAJOR исправлены по авторскому self-check; независимый focused QA должен подтвердить эти выводы.

Изменены **5** кейсов: TC-051/052/053/068/074. Не изменены **20**: все 19 frozen и TC-075. Это явное отклонение от ожидаемых 6/19: разрешённый unresolved не маскируется косметической шестой правкой. TC-075 сохранён побайтово, включая revision=1. У пяти содержательно изменённых revision=2. Исходные batch-02, QA, manifest, production 001–050, schema, учебник и Swift не изменены.

## Закрытие замечаний

| Issue | Severity | Result |
|---|---|---|
| B02-01, TC-075/024 | BLOCKER | UNRESOLVED — frozen диагностическая граница совпадает |
| B02-02, TC-074/012 | MAJOR | FIXED — выбирается предельная ценность общего слота по двум цепочкам |
| B02-03, F-DM-T01 Senior | MAJOR | FIXED — общая приёмка, пересекающиеся потери, неизвестный объём заказов |
| B02-04, TC-068 Senior | MAJOR | FIXED — риск пропуска входа против шума малой выборки |
| B02-05, TC-053 quality | MAJOR | FIXED — новое различие A/B объяснено фактами всех siblings |

Family issue ссылается на те же B02-03/B02-05 и не увеличивает счётчик.

## F-DM-T01: что изменилось в рассуждении

Старая задача давала готовые полные цены и требовала только min. Теперь внешняя разработка за 3 млн ₽ выглядит дешевле четырёх недель ожидания при низком CoD, но не даёт собственной приёмки: принятый результат появится в шестую неделю. Нужно найти общее ограничение, а не принять обещание локальной скорости. Дополнительно Р и К дают один результат и содержат одни ID заказов: простое суммирование карточек дважды считает клиентскую потерю. Неизвестный объём заказов нельзя заменять произвольной средней вероятностью.

После восстановления зависимостей выводятся, а не выдаются готовыми, диапазоны полных потерь:

| State | A | B | C | D | Strongest |
|---|---|---|---|---|---|
| TC-051, x=1 | 7–9 | 7 | 4 | 18–20 | C |
| TC-052, x=4 | 13–15 | 19 | 16 | 18–20 | A |
| TC-053, x=10 | 25–27 | 43 | 40 | 18–20 | D |

Новая единица обязательства — принятый результат вместе с зависимыми работами, а не завершение карточки разработки. Прямые затраты переключения 6 млн ₽, размер Н, стратегия, окна приёмки и интервалы последствий одинаковы в siblings. Единственная mutation — CoD Н 1/4/10. Все ключи устойчивы на полном диапазоне оценок. Около границ существуют зоны неопределённого ранга, но ни один case в них не расположен. Контракт и family positions 1/2/3 сохранены.

TC-053: **A=0.70, B=0.35, D=1.0**. Требование равных scores относилось к прежним равноценным A/B. После общей содержательной правки A даёт 25–27, B — 43; B не учитывает общий bottleneck. Это основание указано в context всех трёх siblings, не добавлено задним числом в explanation. Новый разрыв требует независимой проверки, но больше не приписывает разное качество двум одинаковым планам.

## Why TC-068 now requires Senior reasoning

Senior: требуется распознать дефект наблюдаемости в отборе событий, одновременно удержать риск пропуска полного отказа и шум малой выборки, спроектировать сочетание сигналов для разных режимов трафика и проверить путь обнаружения. Понижение severity CPU само по себе оставляет скрытый отказ; это не готовое operational rule.

Нормальные текущие SLI, CPU 90% и запас autoscaling сохранены. Решение касается именно интерпретации сигнала в контексте пользовательского пути и capacity. Само понижение CPU до warning есть в трёх вариантах и не определяет ключ.

## Cross-bank различия

**TC-012 tests:** Where to bring the allocation conflict: recognize the authority of the shared portfolio owner and bring comparable consequences. Alternatives differ in local protection, proportional split, sponsor arbitration and authorized portfolio decision.

**TC-074 now tests:** Which concrete shared schedule is valuable when one program has an independent later prerequisite. Program A has higher CoD, but first platform slot does not advance its launch. All proposed decisions explicitly involve the same owner.

**Why no longer diagnostically equivalent:** Knowing the right escalation owner cannot discriminate A/C/D in r2. The decisive inference is zero marginal benefit of A-first given gateway readiness; B-first saves its month without delaying A.

Общая authority и итоговый cross-program plan сохранены. Frozen concept конкретизируется через влияние общей зависимости на конечные даты; выбирать отдельный местный P0 нельзя. Внешний шлюз А к концу второго месяца делает первый слот А бесполезным для его запуска; Б сейчас сохраняет обе даты.

Для всех шести scoped ID выполнен screen с production 50 (300 сравнений) и содержательное сравнение ближайших аналогов; классификации — `duplication-audit-r2.csv`. Новые family cases не повторяют budget-cut TC-021, authority TC-012 или перепроектирование приёмки одного запуска TC-045. TC-068 не повторяет release freeze, сегментный rollback или trace ID: это выбор наблюдения при исчезающих событиях и неоднородном потоке.

## Почему TC-075 оставлен unresolved

Manifest фиксирует не только topic/pattern, но и конкретные p=0.03 на дне 9 из 14, отсутствие ранней победы и boundary «первая значимость ↔ соблюдение заранее утверждённого протокола». Это тот же решающий вывод TC-024. Иные числа, distractors и объяснения не меняют его. Новое раннее правило нарушит frozen факт; guardrail/ошибка рандомизации/множественные сравнения заменят диагностическую задачу; отдельный rollout уже проверяется TC-024.

Поэтому **TC-024 strongest reasoning = TC-075 strongest reasoning** в разрешённых границах. Нужна отдельная авторизация MAIN на локальное изменение concept/boundary TC-075 в manifest. Сам manifest и candidate TC-075 здесь не менялись. Полное доказательство и отклонённые варианты — `manifest-duplicate-blocker.json`.

## Проверки

- Ключи: A6/B6/C6/D7, strongest-key changes: 0.
- Metadata changes: 0; unexpected frozen regression: 0.
- 19 frozen и дополнительно TC-075 — побайтово прежние; весь новый файл воспроизводится заменой только пяти разрешённых case-фрагментов.
- Unique strongest: 25/25 — все шесть scoped ID прочитаны повторно, 19 прочих наследуют независимый PASS. Автор знал прежние ключи: это не независимый blind test.
- F-DM-T01 и три untouched семьи: PASS. Только одна family изменена.
- Штатный `TrainerBank.load(url:)`, свежая сборка текущих production sources: PASS.
- Тот же независимый набор 78 эвристик воспроизвёл baseline: combined 11/25, single 9/25.
- После правки: combined **11/25**, single **9/25**, максимум ожидаемых random-tie попаданий **10.500/25**. Surface regression: PASS. Это проверенный exploratory набор, не доказательство отсутствия любых cues.
- Resulting75: 28/75; production не записывался.
- Изменений decisionQuality: 12; точные before/after — `change-log.csv` и `regression.json`.

У каждого изменённого option пересмотрены explanations и WHEN для полного действия, включая дату результата/приёмки. `whatToNotice` и `thinkingModel` представлены schema-полями `decisiveFacts` и `mentalModel`. Source grounding остаётся внутри учебника: §9.3/9.4, §10.4, для критического пути §2.4. Доказательство невозможности TC-075 опирается на §13.3 и финальный manifest, не на старый rationale.

Состав: 25 cases, 16 standalone / 9 linked, 4 families, J5/M11/S6/H3. Eligibility неизменна. Импорт, Batch 03 и изменение blueprint не выполнялись.

**Итог: BLOCKER fixed 0/1; MAJOR fixed 4/4 (self-check). Remaining unresolved IDs: [TC-075]. READY FOR FOCUSED QA: NO.**
