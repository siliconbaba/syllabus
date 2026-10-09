# TC-075 surgical hotfix v2.2.1 / Batch 02 r3

READY FOR FOCUSED QA. Это авторская проверка, не независимый QA и не разрешение импорта.

Причина доказана буквальным сравнением: TC-024 production и прежние blueprint/реализация TC-075 содержат 14 дней, день 9, p=0,03, отсутствие early-stop success rule и strongest «продолжить». Старый TC-075 был диагностическим дублем.

Новый TC-075: запланированный горизонт не завершён, заранее выбранная guardrail существенно и устойчиво нарушена, реальные отмены подтверждены. Strongest B — выключить воздействие, не выдавая защитную остановку за доказательство эффективности. Junior сохранён из v2.2: нужно распознать явное исключение, а не проектировать эксперимент.

Primary precommitted-stop-criteria сохранён: ordinary completion и защитное исключение — разные основания остановки. Secondary p-value/peeking удалены, выбран существующий guardrails. Runtime: evidence + risk, нормализованные веса 2/3 и 1/3 вместо evidence=1. UI domain «Аналитика» неизменен. Coverage пересчитан с компиляцией authoritative mapping/engine и проверкой всех 300 вкладов. Gold здесь только TC-001…025: импортированный Batch 01 уже входит в new275. Domain/level/Head feasibility/pools не изменились.

Manifest: одна изменённая строка, 274 неизменны; 275 new, 181 standalone, 94 linked, 35 pairs, 8 triplets, 11×25. Семьи и batch plan неизменны. CSV остальных 274 строк совпадает по всем полям. Linked family и Head audit скопированы байт-в-байт. Baseline v2.2 не изменён; historical targetedRevision внутри копии сохранён, текущая проверка — validation-result.json и surgicalHotfix.

Batch r3: изменён только TC-075, revision 1→2. TC-051…074 перенесены байт-в-байт. Сохранены F-DM-T01, Senior 051/052/053/068, quality TC-053 и отличие TC-074 от TC-012. Ключ TC-075 B; позиции A6/B6/C6/D7. Strict schema loader PASS. Все 74 сравнения записаны в duplication-audit-r3.csv; TC-024 — ALLOWED REINFORCEMENT, NEAR DUPLICATE/DUPLICATE не обнаружены.

Unique strongest TC-075: A продолжает подтверждённый вред ради срока; C оставляет вред части участников; D откладывает остановку ради уже выполненной проверки. B прекращает воздействие безопасно сейчас и оставляет основной эффект неопределённым. Self-check выполнен тем же автором и не называется независимым blind QA.

Surface: те же 78 правил независимого QA, сравнение с r2: combined 11/25 (baseline 11), single 9/25 (baseline 9). Нет ухудшения по этому набору; это не доказательство отсутствия любой возможной эвристики. Полный повторный QA не проводился.

Remaining blockers: нет по авторской проверке. Требуется focused QA. Production cases.json, runtime, исходный manifest и r2 не изменены; импорт и Batch 03 не запускались.
