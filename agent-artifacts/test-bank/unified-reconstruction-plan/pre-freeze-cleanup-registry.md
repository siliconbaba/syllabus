# Pre-freeze cleanup registry — ничего не исправлено

## OPEN: HT1-261-M01 (один пункт)

TC-261 / whyLevel: убрать неподдержанное «необратимое». Рекомендованная QA формулировка: «близкое решение об оплате длительного сопровождения». Не добавлять необратимость в decisiveFacts ради rationale. Источник: agent-artifacts/qa/manifest-v2.3-hardtail-r1/issues.json; статус OPEN подтверждён verdict r2/B1/B2. Non-blocking для прежней приёмки; выполнить отдельным разрешённым локальным diff перед freeze и проверить неизменность других полей. В этом плане строка не редактируется.

## Historical minors, уже закрытые — не включать в pending count

- TC-042 / QA-10, WHEN A: FIXED подтверждён agent-artifacts/qa/batch-01-r2/case-fixes-focused.csv.
- TC-045 / R2-01, WHEN C: локальная правка подтверждена agent-artifacts/test-bank/batch-01-r2/revision-report.md («Focused QA local fix»); текущий production содержит только обязательную ценность ранней демонстрации. Исторический NEW в старом CSV не является текущим OPEN.

Проверены JSON verdict/issues/findings и CSV severity записи всех имеющихся QA dirs; повторные inherited ссылки на 261 дедуплицированы. Найдены 1 уникальный OPEN и 2 закрытых historical Minor. Нулевые severityCounts не трактовались как закрытие наследованного minor. Других существующих открытых accepted Minor по этим артефактам не обнаружено; это не новый полный QA и не обещание отсутствия новых замечаний.
