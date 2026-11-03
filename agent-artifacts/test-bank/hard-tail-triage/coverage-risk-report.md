# Coverage / product risk — baseline inventory

Ничего не пересчитывается в candidate и не изменяется. Инвентарь в triage-evidence.json сохраняет исходные UI-domain/primary/secondary-thinking по каждой строке и treatment category; это карта зависимостей для будущих решений, не доказательство содержательной валидности unresolved.

-78 unresolved: J8/M37/S30/H3;36standalone/42linked,34topics,20затронутых семей.19семей входят целиком, F-PO-P03 содержит только unresolved234;235 вне списка.
-275new:181standalone/94linked;35pairs+8triplets=43families;11×25batches. Финальная архитектура300training,200ordinary assessment после отдельного отключения шести gold linked,46families,246max independent units.
-Нынешнее распределение new J42/M122/S76/H35; all300 J44/M143/S78/H35; assessment200 J32/M99/S46/H23. Историческая цель all300 J45/M120/S90/H45 уже не совпадает: actual−target=−1/+23/−12/−10. Это существующий разрыв, не результат triage; его нельзя компенсировать повышением других строк.
-Level риск:30Senior и3Head в unresolved. Head234/259/260; C/F mechanism decisions не означают согласие на downgrade. Любое изменение уровня требует отдельного решения и пересчёта assessment breadth.
-Topic риск:34темы. Замены F должны оставаться в исходной теме или потребовать отдельного coverage-решения; нельзя менять topicId ради удобства. Доказательств E-мисматча нет; слабая текущая boundary не равна слабому учебнику.
-Domain/thinking риск: будущий strongest reasoning может изменить patterns. Сначала содержание, затем metadata; старые codes не наследовать ради квот. Текущие unknown codes0 по принятому coverage/runtime contract; high runtimeRisk в triage означает семантический риск использования pattern, не неисправность mapping. Context scored evidence остаётся0. Pattern quotas не являются целью.
-Family риск: replacement не означает удаление пары/триплета. Сохранить IDs, single variable, constants,3meaningful states/2boundaries у triplet, общий topic/domain/level и batch. TC-235 read-only до отдельного scope. Нельзя скрыто превратить family в standalone или компенсировать split другой строкой.
-Product риск: exact300,181/94new и training/assessment eligibility сохраняются. Frozen production100 не редактируется; каталожные planned026–100 также вне remediation. Дублирование runtime coverage с реальными quality gates недопустимо: формальная breadth feasibility не доказывает уровень78unresolved.

## Unresolved coverage by UI domain

| UI domain | Rows | Assessment eligible | Senior+Head assessment eligible |
|---|---:|---:|---:|
| Delivery и релизы | 4 | 0 | 0 |
| Аналитика | 5 | 3 | 0 |
| Люди | 11 | 4 | 1 |
| Портфель и стратегия | 8 | 4 | 0 |
| Продукт | 5 | 3 | 0 |
| Процессы | 13 | 7 | 2 |
| Стейкхолдеры | 13 | 6 | 1 |
| Технический TPM | 8 | 4 | 1 |
| Управление проектами | 8 | 4 | 1 |
| Финансы и подрядчики | 3 | 1 | 0 |

Все baseline vectors и per-row patterns доступны в triage-evidence.json. До future contract approval требуется показать before/after topic/level/domain/thinking и pool counts; никакого их изменения здесь не произведено.

