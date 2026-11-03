# Batch 01 — production candidate TC-026…TC-050

Создано 25/25. Авторская self-QA PASS; независимый Batch QA не проведён. READY не заявляется. Неразрешённых кейсов по self-QA нет.

## Состав

16 standalone (training=true, assessment=true), 9 linked (training=true, assessment=false): F-PM-T01 — triplet; F-BV-P01, F-PA-P01, F-DM-P01 — pairs. J4 / M9 / S8 / H4. Ровно TC-026…050; TC-051+ отсутствуют. Revision всех новых cases = 1.

Manifest v2.2 принят по focused verdict READY FOR BATCH 01; SHA-256 blueprint совпадает с QA-verdict. Все part/topic/domain/level/patterns/eligibility и family/mutation перенесены без изменений. plannedId представлен production id; family position и structure сохранены в source-trace.csv, поскольку schema 2.0 не объявляет их полями Case. whatToNotice реализован как decisiveFacts; thinkingModel — mentalModel; strongest обозначен isBest=true и decisionQuality=1.0.

## Контролируемые семьи

Во всех четырёх семьях вопросы, тексты и порядок вариантов совпадают побайтово. После удаления единственного state fragment contexts совпадают. В PM-triplet меняется только сдвиг 1/4/8; trigger 3, буфер 5, ускорение 2 за 100 тыс. и authority сохранены. В BV-pair меняется только формализуемость scope: коммерческая формула, cap, поставщик и приёмка одинаковы. В PA-pair меняется эффект относительно заранее заданного порога при одинаковом p-value, guardrails и дизайне. В DM-pair меняются утверждённые цена/обратимость первого пилота при одинаковой недельной проверке. Все strongest меняются согласно family boundary.

Конкретизирующие константы BV (цена пакета без премии, премия за неопределённость) и DM (цена и срок исследования/пилота) явно включены в оба context: они не скрыты в explanations и не являются дополнительной mutation. Пороговые числа описывают эти проекты, а не универсальные методологические нормы.

## Surface checks

Strongest positions: A6 / B6 / C6 / D7. Последовательность: C A D B D A C B A D B C A D B C D A C B D A C D B. Порядок siblings не менялся ради баланса.

Длина в Unicode-символах: strongest mean 131.48, median 130; distractors mean 130.24, median 130. Strongest — единственный самый длинный в 7/25; самый длинный с учётом равенств в 10/25. Полные распределения слов/символов, чисел и латинских токенов по options — в batch-statistics.json. Близость длин — эвристический контроль, не доказательство отсутствия leakage. Автор отдельно проверил сходство числа действий, конкретности и категоричности.

Повторы questions и option texts присутствуют только внутри linked families и необходимы для controlled mutation. Точных повторов contexts и option explanations нет. Точных совпадений context/option/explanation с gold нет. Тематические пересечения с gold у API, рисков, uncertainty и observability следуют обязательному blueprint; тексты и конкретные рабочие ситуации написаны заново.

## Validation

Строгая загрузка текущим TrainerBank.load(url:) schema 2.0 — PASS; рядом лежит read-only по смыслу копия текущего topics.json для загрузчика. Проверены vocabulary текущим Swift mapping, ровно один isBest/quality=1.0, все metadata и eligibility, IDs, полнота семей и единственная mutation. Самодельная структурная проверка не заменяла production loader. Результат — schema-validation.log.

Авторская содержательная self-QA содержит 14 пунктов для каждого case, четыре дополнительных linked-пункта и конкретное сравнение strongest с каждым distractor. Это self-review, не независимое или слепое QA. Независимой проверке предстоит оценить правдоподобность distractors и однозначность strongest, в том числе два thresholds PM-triplet.

TC-001…025, production cases.json, manifest, учебник, schema и Swift не редактировались. Hash gold совпал с ранее сохранённым runtime coverage v2.1; hashes manifest/учебника/Swift совпали с focused QA. Кандидат не интегрирован в приложение. Полный app suite не запускался, поскольку приложение не менялось.

## Артефакты

- cases_TC026_TC050.json — candidate schema 2.0.
- source-trace.csv — 25 source/manifest traces, anchors и номера строк учебника.
- self-qa.json — авторские оценки, сравнения и результаты автоматических проверок.
- batch-statistics.json — composition, positions, lengths, repeats.
- authoring-report.md — этот отчёт.

Дополнительно сохранены скрипты воспроизведения, Swift harness, каталог для strict loader и hashes. Все рабочие файлы находятся в этой папке; production bank не затрагивается.
