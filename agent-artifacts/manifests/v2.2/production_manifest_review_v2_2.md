# Targeted revision v2.2 — для focused QA

Self-QA: 34 row issues и 4 family issues addressed; независимый focused QA ещё требуется. READY не заявляется, Batch 01 не начинать.

Изменены 40 строк: 34 из row-fixes плюс 6 членов двух triplet из family-fixes. Остальные 235 строк совпадают со v2.1 по всем полям. Конструкции 39 остальных семей неизменны; F-PR-P01, F-PO-T01 и F-PO-P04 получили только согласованный requiredLevel по row QA.

10 спорных Head: 8 → Middle, TC-282/283 → Senior. whyHead, authorityScope, secondaryEffect очищены. Оставшиеся 35 Head не перепроектировались.

## Уровни

| Pool | Junior | Middle | Senior | Head |
|---|---:|---:|---:|---:|
| New 275 | 42 | 122 | 76 | 35 |
| All 300 | 44 | 143 | 78 | 35 |
| Planned assessment 200 | 32 | 99 | 46 | 23 |

| Level | Target all300 | Actual | Actual − target |
|---|---:|---:|---:|
| junior | 45 | 44 | -1 |
| middle | 120 | 143 | +23 |
| senior | 90 | 78 | -12 |
| head | 45 | 35 | -10 |

## Изменения уровней

- TC-064: head → middle.
- TC-072: senior → middle.
- TC-075: senior → junior.
- TC-088: senior → middle.
- TC-092: senior → middle.
- TC-100: senior → middle.
- TC-106: junior → middle.
- TC-107: junior → middle.
- TC-113: senior → middle.
- TC-122: senior → middle.
- TC-144: senior → middle.
- TC-168: head → middle.
- TC-194: head → middle.
- TC-201: head → middle.
- TC-202: head → middle.
- TC-203: head → middle.
- TC-217: senior → middle.
- TC-253: senior → middle.
- TC-254: senior → middle.
- TC-255: head → middle.
- TC-256: head → middle.
- TC-261: senior → middle.
- TC-275: senior → middle.
- TC-282: head → senior.
- TC-283: head → senior.
- TC-300: senior → middle.

## Runtime и feasibility

Производственные Swift mapping/engine скомпилированы с существующим audit harness. Все 300 impulse responses PASS; context evidence=0, aliases max/category/case и engine normalization подтверждены.

Head feasibility: PASS; областей с ≥3 Senior/Head: 8. Проверка использует синтетические идеальные ответы, не гарантирует результат учащегося или короткой сессии.

| Domain | Gold | New | All | Assessment | J | M | S | H | Assessment S+H | Raw S+H |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Аналитика | 1 | 15 | 16 | 12 | 5 | 6 | 1 | 0 | 1 | 3 |
| Delivery и релизы | 4 | 23 | 27 | 12 | 3 | 7 | 2 | 0 | 2 | 9 |
| Финансы и подрядчики | 1 | 24 | 25 | 19 | 2 | 12 | 1 | 4 | 5 | 9 |
| Люди | 3 | 33 | 36 | 23 | 2 | 14 | 1 | 6 | 7 | 13 |
| Портфель и стратегия | 2 | 28 | 30 | 17 | 1 | 9 | 5 | 2 | 7 | 18 |
| Процессы | 3 | 41 | 44 | 30 | 5 | 11 | 10 | 4 | 14 | 18 |
| Продукт | 1 | 14 | 15 | 11 | 1 | 6 | 4 | 0 | 4 | 4 |
| Управление проектами | 5 | 24 | 29 | 18 | 5 | 7 | 6 | 0 | 6 | 10 |
| Стейкхолдеры | 2 | 27 | 29 | 20 | 4 | 10 | 4 | 2 | 6 | 8 |
| Технический TPM | 3 | 46 | 49 | 38 | 4 | 17 | 12 | 5 | 17 | 21 |

275 IDs, 181 standalone/94 linked, 35 pairs/8 triplets, 11×25 batches сохранены. Structural regression и CSV/JSON roundtrip PASS. Training pool 300; planned assessment 200; 46 families; 246 max independent units.

Assessment 200 требует отдельного будущего отключения TC-001/002/003/004/017/018 в gold; текущие флаги дали бы 206. Gold, engine, mapping, thresholds и UI не изменялись.

Новых vocabulary codes не добавлено. TC-144 сохраняет boundary обработки дубликатов; TC-273 проверяет безопасную retry-policy при уже заданной идемпотентности. Обе используют существующий safeguards.

Незакрытых замечаний по self-QA нет; содержательная приёмка 4 mutations и исправленных строк остаётся за focused QA. Дефицит 10 Head относительно target показан без компенсации. Полный app/WebKit suite не запускался: изменены только planning artifacts.

Полный before/after — change-log-v2_1-to-v2_2.csv. Head audit содержит 35 текущих Head; решения по 10 снятым Head сохранены в change-log.

Source SHA-256:
- TrainerScoringMapping.swift: `a0e578503d7a13868326ffaa786ad363cddbe0782cecfa42a74f6cb2646d3cad`
- TrainerScoringEngine.swift: `13e6a94d5deb5483d9cdf87fd6369540ad36cff821e220e6418409788dbeb5a4`
