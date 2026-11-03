# U-EXP: подтверждение failure и routing delta

Новая проверка выполнена по фактическим master JSON, а не только по verdict автора. Все275 manifest rows, family contracts, coverage и unresolved registry совпадают с accepted B1. Changed rows0; TC-221/263 остаются unresolved; всего72. Все hashes U-EXP artifacts проверены. Production совпадает с контрактным SHA256. Совпадает content, не весь master-файл: U-EXP меняет manifestVersion/provenance и добавляет отчёт о неудачной попытке. Это НЕ accepted content base.

Четыре направления:221 metric selection → NEAR DUPLICATE259/260;221 pilot composition → Middle FAIL;263 repeat segment test → NEAR DUPLICATE164;263 restore control → NEAR DUPLICATE261. Три rejected ND направления,0 applied. Это независимая сверка evidence в рамках planning delta, не новый independent TEST QA и не повторный авторинг.

## Routing

Обе строки: R3 → R5, retryCurrentTreatment=NO. Тема13.3 поддерживает экспериментальный дизайн и интерпретацию, но это само по себе не доказывает свободную Middle-роль. Четыре проверенных конструкции либо возвращают уже занятую decision boundary, либо дают готовое правило. Реалистичное свободное пространство в рамках проверенного salvage-подхода не доказано. Рекомендация — заменить diagnostic concept через архитектурное решение, а не повторить R3 с добавлением цены/длительности. Это не утверждение, что математически исчерпана вся тема. Frozen topic/level/domain/eligibility остаются ограничениями; их изменение здесь не разрешается.

## Причины и пределы вывода

A — локальный выбор первой unit был слишком оптимистичен: два одинаково crowded Middle slots требовали сначала доказать две роли.
B — PARTIAL SYSTEMIC risk: G-LEARNING и несколько R3 с известными anchors имеют тот же риск «цена информации плюс готовое правило». Это planning-risk finding, не измеренный общий failure rate.
C — salvageability была оценена по поддержке общей темы, а не по существованию незанятой диагностической обязанности. Classification confidence нельзя превращать в success confidence.
D — retrieval top-N/same-topic недостаточен без cross-topic reservations:259/260 не входят в исходный nearestAnalog список U-EXP, хотя именно они блокируют proxy-направление. В прошлой попытке ручное расширение поймало это до применения.

Не экстраполируем0/2 на все R3. Остальные treatments не переводятся автоматически в replacement. Точные изменения, confidence и зависимости перечислены в affected-units.json.
