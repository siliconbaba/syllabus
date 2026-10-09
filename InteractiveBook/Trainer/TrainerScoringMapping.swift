import Foundation

enum TrainerDomain: String, CaseIterable, Identifiable {
    case project, delivery, processes, stakeholders, people, finance, portfolio, technical, analytics, product
    var id: String { rawValue }
    var title: String { switch self {
    case .project: return "Управление проектами"; case .delivery: return "Delivery и релизы"
    case .processes: return "Процессы"; case .stakeholders: return "Стейкхолдеры"; case .people: return "Люди"
    case .finance: return "Финансы и подрядчики"; case .portfolio: return "Портфель и стратегия"
    case .technical: return "Технический TPM"; case .analytics: return "Аналитика"; case .product: return "Продукт"
    } }
}
enum TrainerThinking: String, CaseIterable, Identifiable {
    case context, risk, uncertainty, dependencies, prioritization, evidence, proportionality, systems, stakeholders, organization
    var id: String { rawValue }
    var title: String { switch self {
    case .context: return "Контекстная чувствительность"; case .risk: return "Работа с риском"
    case .uncertainty: return "Снижение неопределённости"; case .dependencies: return "Работа с зависимостями"
    case .prioritization: return "Приоритизация"; case .evidence: return "Доказательность"
    case .proportionality: return "Соразмерность решений"; case .systems: return "Системное мышление"
    case .stakeholders: return "Работа со стейкхолдерами"; case .organization: return "Организационное мышление"
    } }
}

// V1 metadata mapping, independent of SwiftUI. Unknown values are never guessed.
enum TrainerScoringMapping {
    static let domains: [TrainerDomain: [String]] = [
        .project: ["planning_and_dependencies", "risk_management", "uncertainty_and_external_dependencies"],
        .delivery: ["release_and_quality", "mobile_delivery", "release_engineering"],
        .processes: ["delivery_quality", "organizational_design"],
        .stakeholders: ["stakeholder_communication"], .people: ["people_management", "incident_and_culture"],
        .finance: ["vendors_and_finance"], .portfolio: ["program_and_portfolio", "portfolio_management"],
        .technical: ["technical_delivery", "reliability", "incident_management"],
        .analytics: ["experimentation"], .product: ["product_and_uncertainty"]
    ]
    static let patterns: [TrainerThinking: [String]] = [
        .context: ["context-sensitivity"],
        .risk: "risk-based-hotfix risk-to-issue-transition early-warning-response error-budget-governance buffer buffer-consumption guardrails mitigation regression-evidence reliability rework-risk risk-based-testing risk-differentiation risk-register rollback safeguards slo warning-mode".components(separatedBy: " "),
        .uncertainty: "contract-volatility uncertainty-impact-plan-b cheap-learning-before-build hypothesis mvp options reversible-investment scope-uncertainty".components(separatedBy: " "),
        .dependencies: "dependency-decoupling external-critical-path api-contracts app-store-review bottleneck contract-first critical-path dependency dependency-management external-contact parallel-work required-date".components(separatedBy: " "),
        .prioritization: "portfolio-reprioritization cost-of-delay feature-velocity lead-time resource-conflict strategic-fit sunk-cost".components(separatedBy: " "),
        .evidence: "evidence-before-release gate-effect-diagnosis precommitted-stop-criteria forecast forecasting impact-analysis p-value peeking quality-metrics".components(separatedBy: " "),
        .proportionality: "progressive-quality-gates diagnosis-before-intervention contract-risk-allocation fixed-price process-economics time-and-materials".components(separatedBy: " "),
        .systems: "rollback-data-awareness backward-compatible-change blameless-system-thinking data-migration expand-contract feature-flags migration-strategy postmortem root-cause versioning".components(separatedBy: " "),
        .stakeholders: "interest-based-negotiation negotiation-batna early-bad-news escalation-readiness communications escalation expectation-management feedback one-on-one support".components(separatedBy: " "),
        .organization: "decision-at-right-level structural-dependency-reduction formal-performance-management incident-command accountability change-control change-management performance pip platform-self-service proactive-management roles team-topologies".components(separatedBy: " ")
    ]
    static func domain(_ raw: String) -> TrainerDomain? { domains.first { $0.value.contains(raw) }?.key }
    static func pattern(_ raw: String) -> TrainerThinking? { patterns.first { $0.value.contains(raw) }?.key }
}
