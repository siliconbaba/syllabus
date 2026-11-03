# Batch 04 — semantic preflight / MANIFEST BLOCKED

Manifest source: **v2.2.3**. Created: **0/25**. Full case authoring: **NOT STARTED**.

Production SHA-256: `6becf4f8ccdb914e9ebd51ca780902174ecdd7914824408139b40477cd25c6a3` — соответствует заданию. Production: TC-001…TC-100; 100 cases, 67 standalone, 33 linked, 15 families; training 100 / assessment 67; J16/M53/S21/H10.

## Фактический frozen contract

TC-101…TC-125: 25; standalone 16; linked 9; 3 pairs + 1 triplet, 4 families; J3/M13/S6/H3. Training 25 / assessment 16. Полные неизменённые поля (topics, domains, patterns, decisive facts, boundaries, eligibility и family contracts) сохранены в frozen-batch04-contract.json.

| ID | Topic | Level | Domain | Primary pattern | Family |
|---|---|---|---|---|---|
| TC-101 | t-3-3 | senior | release_engineering | rollback-data-awareness | F-TD-T01 |
| TC-102 | t-3-3 | senior | release_engineering | rollback-data-awareness | F-TD-T01 |
| TC-103 | t-3-3 | senior | release_engineering | rollback-data-awareness | F-TD-T01 |
| TC-104 | t-2-6 | junior | risk_management | risk-to-issue-transition | F-PM-P01 |
| TC-105 | t-2-6 | junior | risk_management | risk-to-issue-transition | F-PM-P01 |
| TC-106 | t-3-7 | middle | delivery_quality | structural-dependency-reduction | F-PR-P01 |
| TC-107 | t-3-7 | middle | delivery_quality | structural-dependency-reduction | F-PR-P01 |
| TC-108 | t-10-4 | middle | technical_delivery | gate-effect-diagnosis | F-PA-P02 |
| TC-109 | t-10-4 | middle | technical_delivery | gate-effect-diagnosis | F-PA-P02 |
| TC-110 | t-10-1 | middle | technical_delivery | structural-dependency-reduction | — |
| TC-111 | t-4-3 | head | organizational_design | decision-at-right-level | — |
| TC-112 | t-6-1 | middle | stakeholder_communication | expectation-management | — |
| TC-113 | t-7-4 | middle | people_management | diagnosis-before-intervention | — |
| TC-114 | t-8-2 | middle | vendors_and_finance | gate-effect-diagnosis | — |
| TC-115 | t-10-6 | middle | incident_management | incident-command | — |
| TC-116 | t-10-4 | middle | technical_delivery | safeguards | — |
| TC-117 | t-2-6 | senior | risk_management | early-warning-response | — |
| TC-118 | t-9-3 | senior | portfolio_management | cheap-learning-before-build | — |
| TC-119 | t-3-2 | senior | delivery_quality | progressive-quality-gates | — |
| TC-120 | t-4-3 | head | organizational_design | gate-effect-diagnosis | — |
| TC-121 | t-6-6 | middle | stakeholder_communication | interest-based-negotiation | — |
| TC-122 | t-7-6 | middle | people_management | diagnosis-before-intervention | — |
| TC-123 | t-8-1 | middle | vendors_and_finance | portfolio-reprioritization | — |
| TC-124 | t-10-6 | junior | incident_management | risk-based-hotfix | — |
| TC-125 | t-10-7 | head | technical_delivery | decision-at-right-level | — |

## Cross-bank verdict

Проверены все 25 blueprint относительно production TC-001…TC-100. Классификация — содержательное экспертное суждение по ошибке кандидата, фактам, решению, strongest reasoning и mental model; не порог лексической похожести. Nearest analog — ближайший для сравнения, а не утверждение о близости при NO CLOSE ANALOG. Exact production evidence сохранено отдельно.

ALLOWED REINFORCEMENT: 11 / DUPLICATE: 6 / NEAR DUPLICATE: 5 / NO CLOSE ANALOG: 3

| Planned | Nearest production | Verdict |
|---|---|---|
| TC-101 | TC-054 | ALLOWED REINFORCEMENT |
| TC-102 | TC-010 | ALLOWED REINFORCEMENT |
| TC-103 | TC-010 | DUPLICATE |
| TC-104 | TC-006 | ALLOWED REINFORCEMENT |
| TC-105 | TC-006 | DUPLICATE |
| TC-106 | TC-086 | ALLOWED REINFORCEMENT |
| TC-107 | TC-086 | ALLOWED REINFORCEMENT |
| TC-108 | TC-044 | NEAR DUPLICATE |
| TC-109 | TC-044 | ALLOWED REINFORCEMENT |
| TC-110 | TC-013 | NO CLOSE ANALOG |
| TC-111 | TC-040 | NEAR DUPLICATE |
| TC-112 | TC-069 | ALLOWED REINFORCEMENT |
| TC-113 | TC-081 | DUPLICATE |
| TC-114 | TC-042 | NO CLOSE ANALOG |
| TC-115 | TC-023 | DUPLICATE |
| TC-116 | TC-050 | NO CLOSE ANALOG |
| TC-117 | TC-007 | ALLOWED REINFORCEMENT |
| TC-118 | TC-025 | NEAR DUPLICATE |
| TC-119 | TC-009 | DUPLICATE |
| TC-120 | TC-039 | NEAR DUPLICATE |
| TC-121 | TC-096 | ALLOWED REINFORCEMENT |
| TC-122 | TC-017 | DUPLICATE |
| TC-123 | TC-042 | ALLOWED REINFORCEMENT |
| TC-124 | TC-023 | ALLOWED REINFORCEMENT |
| TC-125 | TC-013 | NEAR DUPLICATE |

## Почему wording не устраняет blockers

- **TC-103 ↔ TC-010**: В обоих случаях старый код не читает новые записи, обратная миграция превышает recovery window. В обоих: сначала expand-contract, затем новое поведение. Наличие rollback не обеспечивает восстановление в допустимое время.
- **TC-105 ↔ TC-006**: В обоих оператор официально подтвердил задержку на три недели; response подготовлен. В обоих: issue, запуск response, последствия и остаточные риски. Подтверждённый trigger переводит риск в проблему.
- **TC-108 ↔ TC-044**: В обоих агрегат после релиза не локализует причину; полный rollback дорог. В обоих сначала сегментировать/локализовать, затем выбрать вмешательство. Цена широкого вмешательства не оправдана без достаточного причинного сигнала.
- **TC-111 ↔ TC-040**: В обоих конфликты систематические и прежняя координация не устраняет их. В обоих изменить governance/decision rights вместо повторных согласований. Устойчивый конфликт приоритетов требует правил принятия решений.
- **TC-113 ↔ TC-081**: Сильный сотрудник теряет инициативу, причина не обсуждалась; деньги не доказаны как причина. В обоих диагностический разговор перед деньгами/автономией/ростом. Нельзя выбирать мотивационный инструмент по одному симптому.
- **TC-115 ↔ TC-023**: В обоих нет IC и несколько людей одновременно меняют production при активном инциденте. В обоих назначить command/роли и установить контроль изменений. Сначала сделать реагирование управляемым.
- **TC-118 ↔ TC-025**: В обоих ключевая гипотеза не подтверждена и доступна дешёвая проверка. В обоих сначала снизить uncertainty дешёвым тестом, затем полная инвестиция. Ценность дополнительной информации выше немедленного полномасштабного запуска.
- **TC-119 ↔ TC-009**: В обоих автоматизация зрелая не у всех; legacy не готовы, критерии общие. В обоих progressive blocking по измеримой readiness. Общий стандарт качества не требует одинаковой даты технического enforcement.
- **TC-120 ↔ TC-039**: В обоих слабые межгрупповые зависимости и высокая цена общей координации. В обоих ограничить coordination framework реальным value flow. Стоимость координации оправдывается зависимостями, не числом команд.
- **TC-122 ↔ TC-017**: В обоих ранее сильный сотрудник, внезапная просадка, ещё нет диагностического feedback. В обоих диагностический разговор до formal performance process. Причина и поддержка должны быть выяснены прежде формальной эскалации.
- **TC-125 ↔ TC-013**: TC-125: формальные risk tiers и low-risk config; TC-013: типовые операции допустимы с валидацией/аудитом. В обоих вывести допустимый класс работ из центрального ручного обслуживания под guardrails. Убрать саму зависимость вместо ускорения той же очереди.

Имена, масштаб, числа и формулировки не меняют повторяющуюся диагностическую задачу. Устранение отмеченных пересечений требует согласованного изменения frozen concept, decisive facts или decision boundary. Для linked TC-103, TC-105 и TC-108 пересмотр должен учитывать целую семью; это не разрешение менять siblings автоматически. Manifest не изменён.

## Internal и families

Все 300 внутренних пар перечислены в internal-preflight.csv. 6 пар — намеренные sibling contrasts, 294 — остальные пары; блокирующих внутренних совпадений на уровне concept не выявлено. Тематически близкие TC-111/120/125 различаются объектом governance (приоритеты / граница coordination framework / risk-tiered approvals); TC-115/124 — command против безопасного восстановления; TC-104/117 — статус риска против цены раннего вмешательства; TC-108/116 — локализация против минимизации данных.

- **F-TD-T01**: Три стратегии различимы: code rollback; cutover с recovery в окне; expand-contract до включения. Две границы: совместимость старого кода; достижимость восстановления в окне. Точка невозврата в среднем состоянии относится к обычному code rollback, не к абсолютной невозможности восстановления. Cross-bank blockers: TC-103.
- **F-PM-P01**: Одна переменная — событие ещё не подтверждено / официально наступило. Готовность response сменяется его активацией. Cross-bank blockers: TC-105.
- **F-PR-P01**: Одна переменная — временный пик / устойчивое повторение. Временная разгрузка сменяется изменением постоянного ограничения; WIP и приоритеты остаются фиксированными. Cross-bank blockers: нет.
- **F-PA-P02**: Одна переменная — достаточность причинного сигнала. Нелокализованный агрегат требует диагностики; согласованные trace/logs/metrics допускают локальную mitigation. Cross-bank blockers: TC-108.

PASS family contract означает различимость frozen состояний и стратегий. Он не заменяет будущую проверку одинаковых options, literal sibling diff и unique strongest.

## Границы результата

Это pre-authoring evidence, не полный QA банка. Полные cases, source-trace авторинга, surface leakage и 125-case audit не создавались/не запускались. Schema/runtime validation новых cases неприменима: новых cases нет. Runtime, schema, учебник, production bank и authoritative manifest сохранены без изменений; контрольные hashes — input-hashes.json. Внешние содержательные источники не использовались.

Для ALLOWED REINFORCEMENT в CSV явно указаны различия decisive facts и actual decision/strongest reasoning. Эти различия необходимо удержать при будущем авторинге после manifest hotfix; одна тематическая близость не считается дефектом.

**AUTHORING STARTED: NO**  
**READY FOR MANIFEST HOTFIX: YES**
