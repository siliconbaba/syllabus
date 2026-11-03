# Batch 03 r3 — только TC-085

**READY FOR FOCUSED QA: YES — авторская самопроверка. Не READY FOR IMPORT.**

Manifest-level blocker TC-085↔TC-004 закрыт новой candidate boundary в ../manifests/v2.2.3-candidate. Изменены ровно1 planned row и1 authored case; family contracts не изменены. Frozen v2.2.2 остаётся исходным authoritative baseline; v2.2.3 не frozen.

## Новое решение

TC-004 добавляет недостающее targeted evidence перед hotfix. Новый085 выбирает повторяемую подготовку расходуемых согласованных данных при фиксированном достаточном наборе проверок. Ошибка — ускорять тесты либо добавлять стенд, оставляя повторное восстановление данных; не ошибка выбора полного/целевого регресса. Классификация ALLOWED REINFORCEMENT, near/duplicate0.

Middle требует сопоставить разовые/повторные затраты, готовность первого запуска и полную ёмкость шести циклов при сохранении согласованных данных. Проверки и их покрытие не сокращаются. Источник только§3.9, данные/время синтетические.

| Option | До первого старта | Весь горизонт | Решающий факт |
|---|---:|---:|---|
| A: автоматизация проверок |20ч|43ч|Ручное восстановление4ч остаётся; превышены16/30ч.|
| B: дополнительная среда |8ч|40ч|Очереди нет; те же данные требуют того же восстановления.|
| C: сценарий восстановления |12,5ч|27ч|Снимает повторную подготовку, сохраняет проверки и помещается в16/30ч.|
| D: ручные независимые наборы |4ч|36ч|Не требует разработки, но повторный труд превышает30ч.|

Strongest C. D — сильная профессиональная альтернатива при меньшем числе циклов/нестабильной схеме; score0.82, A0.65, B0.45, C1. WHEN каждого варианта оправдывает весь план в соответствующих условиях. Pairwise check C противA/B/D основан на фактах context; post-hoc факты не добавлены. Key-masked input создан без explanations/scores, но автор знает дизайн: это не независимый blind QA. Доказательства — tc085-pairwise-self-check.json и source-trace-TC085.json.

## Regression

r2→r3: changed1, unchanged24 byte-identical, unexpected0. Проверены raw UTF-8 spans целых case objects. Все исправления r2, включая090 и уровни083/084/094/100, сохранены без переоткрытия. Это сохранение предыдущих результатов, а не новый independent PASS.

25 кейсов,16standalone,9linked,4families;J5/M12/S5/H3;A6/B6/C6/D7. Metadata24/24 соответствует frozen2.2.2, новый085 — candidate2.2.3. Families4/4 — все sibling bytes unchanged, r2 literal proofs сохранены в family-diff-analysis-r3.json. Whole batch unique strongest/source25/25 по новой self-check085 и сохранённым r2 доказательствам.

Cross-bank batch: NO CLOSE ANALOG2, ALLOWED REINFORCEMENT23, NEAR DUPLICATE0, DUPLICATE0. Полный blueprint/full-wording scan085 против299 IDs в manifest candidate; production75 — обязательная часть. Внутри batch сравнены новые24 пары с085; остальные276 пар сохранены; accidental near/duplicates0.

## Surface и validator

Те же78 правил/19 признаков: r3 best10/25, r2 best10/25. Combined100 best33/100, r2 combined33/100. Позиции100:A24/B24/C25/D27. Surface PASS в пределах exploratory набора; это не доказательство отсутствия любой подсказки. После первичного скана формулировка C явно называет оба действия — восстановить данные и выполнить тот же набор; новые действия/обязательства ради длины не добавлялись.

TrainerBank.load strict schema2.0 PASS; runtime codes PASS, unknown0. Part/topic, eligibility, levels, IDs и соответствие metadata проверены. Protected input hashes подтвердили неизменность production, исходных manifest/r2/QA, schema и Swift.

Unresolved IDs: []. Candidate и manifest candidate готовы к одному focused independent QA. Импорта, freeze, Batch04, commit/push нет.

Candidate SHA-256: `77e465c3b9a5e0ac26eb7bdf756d20d2416d18fb57cd74f225575d0e6f202f21`.
Manifest candidate SHA-256: `84cfcf2e9e3a86b3f259421869e092bad969bbcbbb851b50cb44b59af29a3546`.
