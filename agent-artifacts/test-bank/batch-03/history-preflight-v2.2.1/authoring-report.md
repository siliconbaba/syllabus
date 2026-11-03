# Batch 03 — preflight blocked

Создано production cases: **0/25**. READY FOR INDEPENDENT QA: **NO**.

Production содержит ровно TC-001…TC-075. Blueprint извлечён только из authoritative v2.2.1: 16 standalone, 9 linked, 3 pairs + 1 triplet; J5/M12/S5/H3. Vocabulary, topic/part и eligibility manifest прошли проверку.

Обязательный semantic preflight завершён до создания options/explanations. Классификация ближайших совпадений: {'NEAR DUPLICATE': 2, 'ALLOWED REINFORCEMENT': 17, 'DUPLICATE': 4, 'NO CLOSE ANALOG': 2}. Полные исходные concepts/facts/boundaries, production context/strongest, обоснования и поля для решения — duplication-preflight.csv. Дополнительная матрица охватывает 1875 пар; текстовая близость не используется как доказательство semantic uniqueness.

## Manifest blockers

- **MANIFEST BLOCKER: TC-076 vs TC-047 — NEAR DUPLICATE**. Ненадёжный/шумный gate и частые ложные блокировки → warning до проверки сигнала. TC-047 уже требует именно этого, сохраняя обязательный ручной контроль. Множественное число gates и новый primary pattern не создают новой границы. Требует решения: oneSentenceScenarioConcept; decisiveFactsConcept; oneSentenceDecisionBoundary; F-DR-T01 stateByMember/decisionBoundaryByState для TC-076.
- **MANIFEST BLOCKER: TC-079 vs TC-011 — DUPLICATE**. Оба: изменение обязательного поля публичного API, семь независимых клиентов, разные cadence, дешёвое сосуществование контрактов. Оба требуют постепенной versioned migration и удаления старой версии после подтверждения перехода. Junior вместо Middle не меняет проверяемое решение. Требует решения: oneSentenceScenarioConcept; decisiveFactsConcept; oneSentenceDecisionBoundary; F-TD-P01 baseSituation/stateByMember/decisionBoundaryByState.
- **MANIFEST BLOCKER: TC-087 vs TC-019 — DUPLICATE**. Оба: конфигурационная ошибка человека, процесс разрешал одиночное критичное изменение без валидации. Оба противопоставляют human error как конец анализа поиску системных условий и защит. Совпадают reasoning и Middle. Требует решения: oneSentenceScenarioConcept; decisiveFactsConcept; oneSentenceDecisionBoundary.
- **MANIFEST BLOCKER: TC-088 vs TC-016 — NEAR DUPLICATE**. Тот же security review и та же готовность эскалации: без impact/critical-path/decision ask эскалировать рано. Required date и прямой разговор здесь уже выполнены, но оставшийся пробел — подмножество диагностики TC-016; новое управленческое решение blueprint не задаёт. Требует решения: oneSentenceScenarioConcept; decisiveFactsConcept; oneSentenceDecisionBoundary.
- **MANIFEST BLOCKER: TC-091 vs TC-013 — DUPLICATE**. Постоянная очередь к общему сервису, большинство операций типовые (70% вместо 60%), coordination сохраняет зависимость, strongest — platform/self-service граница. Количество команд и Senior label не меняют решение TC-013. Требует решения: oneSentenceScenarioConcept; decisiveFactsConcept; oneSentenceDecisionBoundary.
- **MANIFEST BLOCKER: TC-093 vs TC-006 — DUPLICATE**. Официальное подтверждение внешней задержки переводит событие из риска в проблему; contingency уже задан. Замена сертификационного окна оборудованием сохраняет все решающие факты и strongest TC-006. Middle label не добавляет reasoning. Требует решения: oneSentenceScenarioConcept; decisiveFactsConcept; oneSentenceDecisionBoundary.

Заблокированы также siblings TC-077, TC-078, TC-080 для целостности F-DR-T01/F-TD-P01. Это не дополнительные duplicate verdicts: их собственные preflight-классификации остаются ALLOWED REINFORCEMENT. Семьи и manifest не изменены.

## Почему авторинг остановлен

Повторы затрагивают несколько независимых дизайнов и две связанные семьи; полный frozen batch не может пройти gate. Возможность продолжить отдельные незаблокированные IDs не использована: частичный production candidate не выдаётся за партию из 25. Для продолжения нужен точечный пересмотр указанных manifest-полей владельцем blueprint; менять их в этой задаче прямо запрещено. Иные 19 строк не предлагаются к перепроектированию; три из них удержаны только как siblings.

Не создавался cases_TC076_TC100.json: пустой банк, заглушки и повторяющие production кейсы не являются schema-valid production candidate. Остальные обязательные отчёты явно отмечают NOT RUN там, где нужны написанные кейсы. Source trace пока содержит только IDs/anchors со статусом NOT AUTHORED — не заявляет source-grounded авторинг.

## Ограничения для допустимых повторений

TC-085: достаточный impact-based targeted набор против лишнего полного регресса, не повтор hotfix/rollback выбора TC-004. TC-090: обязательна реализация knowledge-risk и скрытой стоимости сокращения, иначе повтор TC-066. TC-094: финальный success/rollout при uplift и нарушении guardrail, не незавершённый эксперимент TC-075. TC-096: полноценный trade-off влияния и workaround, не одна эскалация authority как в TC-012. F-BV-P02: Senior должен быть в общей сложности предпосылок, не в арифметическом знаке NPV. Это authoring guardrails, не разрешение менять blueprint.

## Lessons learned

Учтены QA batch-01, batch-01-r2, batch-02, batch-02-r3: не прятать различающие факты в explanation; условный вариант не должен вырождаться в strongest sibling; level проверять по необходимому рассуждению; quality gap обосновывать; whenItWouldBeBest должен оправдывать весь вариант; проверять совокупные surface cues; ловить manifest duplicate до options, как прежний TC-075. Предыдущие QA отчёты использованы только для метода, не как источник текущего blueprint.

Production, v2.2.1, schema и Swift не изменены; контрольные суммы входов перепроверены. Импорт, TC-101+, commit/push не выполнялись.
