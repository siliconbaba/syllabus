import Foundation

// Preserve numeric production values and legacy strings without inventing conversions.
enum TrainerScalar: Codable, Equatable {
    case number(Double)
    case text(String)
    init(from decoder: Decoder) throws {
        let value = try decoder.singleValueContainer()
        if let number = try? value.decode(Double.self) { self = .number(number) }
        else { self = .text(try value.decode(String.self)) }
    }
    func encode(to encoder: Encoder) throws {
        var value = encoder.singleValueContainer()
        switch self { case .number(let n): try value.encode(n); case .text(let s): try value.encode(s) }
    }
}

private extension CodingUserInfoKey {
    static let trainerProductionV2 = CodingUserInfoKey(rawValue: "trainerProductionV2")!
}

struct TrainerCase: Codable, Identifiable, Equatable {
    struct Option: Codable, Identifiable, Equatable {
        let id: String
        let text: String
        let decisionQuality: TrainerScalar
        let isBest: Bool
        let reasoningPattern: String
        let failurePattern: String?
        let explanation: String
        let whyTempting: String
        let whyNotBest: String
        let whenItWouldBeBest: String
    }
    let id: String
    let type: String?
    let revision: Int
    let topicId: String
    let domain: String
    let requiredLevel: String
    let primaryPattern: String
    let secondaryPatterns: [String]
    let context: String
    let question: String
    let options: [Option]
    let keyInsight: String
    let mentalModel: String
    let decisiveFacts: [String]
    let scenarioFamilyId: String?
    let decisiveMutation: String?
    let authorRationale: String
    let partId: String
    let title: String?
    let sourceTopicExplanation: String
    let trainingEligible: Bool
    let assessmentEligible: Bool

    enum CodingKeys: String, CodingKey {
        case id, type, revision, topicId, domain, requiredLevel, primaryPattern, secondaryPatterns, context, question, options, keyInsight, mentalModel, decisiveFacts, scenarioFamilyId, decisiveMutation, authorRationale, partId, title, sourceTopicExplanation, trainingEligible, assessmentEligible
    }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let strict = decoder.userInfo[.trainerProductionV2] as? Bool == true
        id = try c.decode(String.self, forKey: .id)
        type = try c.decodeIfPresent(String.self, forKey: .type)
        revision = try c.decode(Int.self, forKey: .revision)
        topicId = try c.decode(String.self, forKey: .topicId)
        domain = try c.decode(String.self, forKey: .domain)
        requiredLevel = try c.decode(String.self, forKey: .requiredLevel)
        primaryPattern = try c.decode(String.self, forKey: .primaryPattern)
        secondaryPatterns = try c.decode([String].self, forKey: .secondaryPatterns)
        context = try c.decode(String.self, forKey: .context)
        question = try c.decode(String.self, forKey: .question)
        options = try c.decode([Option].self, forKey: .options)
        keyInsight = try c.decode(String.self, forKey: .keyInsight)
        mentalModel = try c.decode(String.self, forKey: .mentalModel)
        decisiveFacts = try c.decode([String].self, forKey: .decisiveFacts)
        scenarioFamilyId = try c.decodeIfPresent(String.self, forKey: .scenarioFamilyId)
        decisiveMutation = try c.decodeIfPresent(String.self, forKey: .decisiveMutation)
        authorRationale = try c.decode(String.self, forKey: .authorRationale)
        title = try c.decodeIfPresent(String.self, forKey: .title)
        partId = strict ? try c.decode(String.self, forKey: .partId) : try c.decodeIfPresent(String.self, forKey: .partId) ?? ""
        sourceTopicExplanation = strict ? try c.decode(String.self, forKey: .sourceTopicExplanation) : try c.decodeIfPresent(String.self, forKey: .sourceTopicExplanation) ?? ""
        trainingEligible = strict ? try c.decode(Bool.self, forKey: .trainingEligible) : try c.decodeIfPresent(Bool.self, forKey: .trainingEligible) ?? true
        assessmentEligible = strict ? try c.decode(Bool.self, forKey: .assessmentEligible) : try c.decodeIfPresent(Bool.self, forKey: .assessmentEligible) ?? true
    }
}

extension TrainerCase {
    var topicTitle: String {
        let labels = [
            "planning_and_dependencies":"Планирование и зависимости", "delivery_quality":"Качество поставки",
            "experimentation":"Эксперименты", "incident_and_culture":"Инциденты и культура",
            "incident_management":"Управление инцидентами", "mobile_delivery":"Мобильная поставка",
            "organizational_design":"Организация команд", "people_management":"Работа с людьми",
            "portfolio_management":"Управление портфелем", "product_and_uncertainty":"Продукт и неопределённость",
            "program_and_portfolio":"Программы и портфель", "release_and_quality":"Релизы и качество",
            "release_engineering":"Инженерия релизов", "reliability":"Надёжность",
            "risk_management":"Управление рисками", "stakeholder_communication":"Работа со стейкхолдерами",
            "technical_delivery":"Техническая поставка", "uncertainty_and_external_dependencies":"Неопределённость и внешние зависимости",
            "vendors_and_finance":"Подрядчики и финансы"
        ]
        return labels[domain] ?? domain
    }
}

struct TrainerAttempt: Codable, Equatable {
    enum Phase: String, Codable { case answer, review, completed }
    let id: UUID
    let startedAt: Date
    // Keep the original cases with the attempt so a bank update cannot change its explanations.
    let cases: [TrainerCase]
    var index: Int = 0
    var phase: Phase = .answer
    var draftOptionID: String?
    var answers: [String: String] = [:]
    var completedAt: Date?
    var session: TrainerSession? = nil
    var resolvedIDs: [String]? = nil
    var mode: TrainerSession.Kind { session?.kind ?? .legacy }
    var title: String { session?.title ?? "Учебная тренировка" }
}

struct TrainerBank: Codable {
    let schemaVersion: TrainerScalar
    let source: String?
    let cases: [TrainerCase]
    // Bundled banks are strict v2. Legacy decoding is explicit and reserved for archived fixtures.
    static func load(url: URL, allowLegacy: Bool = false) throws -> TrainerBank {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        if !allowLegacy { decoder.userInfo[.trainerProductionV2] = true }
        let bank = try decoder.decode(Self.self, from: data)
        if allowLegacy {
            guard [TrainerScalar.number(1), .text("1.0")].contains(bank.schemaVersion) else { throw TrainerError.invalidBank }
            try validate(bank.cases)
        } else {
            guard bank.schemaVersion == .text("2.0") else { throw TrainerError.invalidBank }
            let catalog = try TrainerCatalog.load(url: url.deletingLastPathComponent().appendingPathComponent("topics.json"))
            try bank.validateProduction(catalog: catalog)
        }
        return bank
    }
    var trainingCases: [TrainerCase] { cases.filter(\.trainingEligible) }
    func validateProduction(catalog: TrainerCatalog) throws {
        guard schemaVersion == .text("2.0") else { throw TrainerError.invalidBank }
        try Self.validate(cases)
        func filled(_ s: String) -> Bool { !s.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        for c in cases {
            guard c.type == "single-best", filled(c.partId), filled(c.sourceTopicExplanation),
                  c.title.map(filled) ?? true,
                  catalog.sections.contains(where: { $0.id == c.partId }),
                  catalog.topics.contains(where: { $0.id == c.topicId && $0.sectionID == c.partId }),
                  Set(c.options.map(\.id)) == Set(["A", "B", "C", "D"]),
                  c.options.allSatisfy({ if case .number = $0.decisionQuality { return true }; return false }) else { throw TrainerError.invalidBank }
        }
        let families = Dictionary(grouping: cases.filter { $0.scenarioFamilyId != nil }, by: { $0.scenarioFamilyId! })
        for family in families.values {
            guard family.count >= 2, Set(family.map(\.topicId)).count == 1,
                  Set(family.compactMap(\.decisiveMutation)).count == family.count else { throw TrainerError.invalidBank }
        }
    }
    static func validate(_ cases: [TrainerCase]) throws {
        func filled(_ s: String) -> Bool { !s.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        guard !cases.isEmpty, Set(cases.map(\.id)).count == cases.count else { throw TrainerError.invalidBank }
        for c in cases {
            let legacy = c.id.hasPrefix("ux-") && c.type == nil
            guard legacy || c.type == "single-best",
                  (c.scenarioFamilyId == nil) == (c.decisiveMutation == nil),
                  c.scenarioFamilyId.map(filled) ?? true,
                  c.decisiveMutation.map(filled) ?? true else { throw TrainerError.invalidBank }
            for option in c.options {
                switch option.decisionQuality {
                case .number(let quality):
                    guard quality.isFinite && (0...1).contains(quality) else { throw TrainerError.invalidBank }
                case .text(let quality):
                    guard legacy && ["preferred", "suboptimal"].contains(quality) else { throw TrainerError.invalidBank }
                }
                guard option.failurePattern.map(filled) ?? true else { throw TrainerError.invalidBank }
            }
            guard c.revision > 0, [c.id,c.topicId,c.domain,c.requiredLevel,c.primaryPattern,c.context,c.question,c.keyInsight,c.mentalModel,c.authorRationale].allSatisfy(filled),
                  !c.decisiveFacts.isEmpty, c.decisiveFacts.allSatisfy(filled), c.secondaryPatterns.allSatisfy(filled),
                  c.options.count == 4, Set(c.options.map(\.id)).count == 4,
                  c.options.filter(\.isBest).count == 1,
                  c.options.allSatisfy({ [ $0.id,$0.text,$0.reasoningPattern,$0.explanation,$0.whyTempting,$0.whyNotBest,$0.whenItWouldBeBest ].allSatisfy(filled) }) else { throw TrainerError.invalidBank }
        }
    }
}

enum TrainerError: LocalizedError {
    case invalidBank, invalidAttempt, unsupportedVersion
    var errorDescription: String? {
        switch self {
        case .invalidBank: return "Не удалось загрузить учебные ситуации. Проверьте версию приложения."
        case .invalidAttempt: return "Сохранённая попытка повреждена. Файл оставлен для восстановления. Можно сбросить только попытку тренажёра."
        case .unsupportedVersion: return "Попытка создана другой версией тренажёра. Файл сохранён; для продолжения обновите приложение или сбросьте попытку."
        }
    }
}

struct TrainerSession: Codable, Equatable {
    enum Kind: String, Codable { case mixed, section, topic, mistakes, legacy }
    let kind: Kind
    let title: String
    var sectionID: String? = nil
    var topicID: String? = nil
}

struct TrainerProgress: Codable, Equatable {
    struct Result: Codable, Equatable {
        let testId: String
        var revision: Int
        var answers: Int = 0
        var errors: Int = 0
        var lastErrorAt: Date?
        var resolved: Bool = false
        var lastAnsweredAt: Date
    }
    var results: [String: Result] = [:]
    mutating func record(test: TrainerCase, optionID: String, mode: TrainerSession.Kind, at date: Date) {
        guard let option = test.options.first(where: { $0.id == optionID }) else { return }
        var result = results[test.id] ?? Result(testId: test.id, revision: test.revision, lastAnsweredAt: date)
        result.revision = test.revision
        result.answers += 1
        result.lastAnsweredAt = date
        if !option.isBest {
            result.errors += 1; result.lastErrorAt = date; result.resolved = false
        } else if mode == .mistakes && result.errors > 0 { result.resolved = true }
        results[test.id] = result
    }
    var unresolvedCount: Int { results.values.filter { $0.errors > 0 && !$0.resolved }.count }
    func unresolved(in bank: [TrainerCase]) -> [TrainerCase] {
        bank.filter { $0.trainingEligible }.filter { results[$0.id].map { $0.errors > 0 && !$0.resolved } ?? false }
    }
    func validate() throws {
        for (id, r) in results {
            guard id == r.testId, !id.isEmpty, r.revision > 0, r.answers > 0,
                  (0...r.answers).contains(r.errors), (r.errors > 0) == (r.lastErrorAt != nil),
                  !r.resolved || r.errors > 0 else { throw TrainerError.invalidAttempt }
        }
    }
}

struct TrainerCatalog: Codable {
    struct Section: Codable, Identifiable { let id: String; let title: String }
    struct Topic: Codable, Identifiable { let id: String; let sectionID: String; let title: String }
    let sections: [Section]
    let topics: [Topic]
    static func load(url: URL) throws -> Self {
        let value = try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
        guard Set(value.sections.map(\.id)).count == value.sections.count,
              Set(value.topics.map(\.id)).count == value.topics.count,
              value.topics.allSatisfy({ t in value.sections.contains { $0.id == t.sectionID } }) else { throw TrainerError.invalidBank }
        return value
    }
    func availableSections(in cases: [TrainerCase]) -> [Section] {
        sections.filter { !casesForSection($0.id, in: cases).isEmpty }
    }
    func availableTopics(sectionID: String, in cases: [TrainerCase]) -> [Topic] {
        topics.filter { $0.sectionID == sectionID && !casesForTopic($0.id, in: cases).isEmpty }
    }
    func casesForSection(_ id: String, in cases: [TrainerCase]) -> [TrainerCase] {
        let ids = Set(topics.filter { $0.sectionID == id }.map(\.id))
        return cases.filter { $0.trainingEligible && ids.contains($0.topicId) }
    }
    func casesForTopic(_ id: String, in cases: [TrainerCase]) -> [TrainerCase] { cases.filter { $0.trainingEligible && $0.topicId == id } }
    static func sample(_ cases: [TrainerCase], count: Int?) -> [TrainerCase] {
        Array(cases.shuffled().prefix(max(0, min(count ?? cases.count, cases.count))))
    }
}

// Eligibility is deliberately separate from learning errors/results.
struct TrainerEncounter: Codable, Equatable {
    enum Source: String, Codable { case training, assessment }
    let firstEncounter: Source
    var assessmentUsed: Bool
}

enum DiagnosticEligibility: String, Codable { case cleanFirstAssessment, previouslyConfirmed }

struct DiagnosticAttempt: Codable, Identifiable, Equatable {
    let id: UUID
    let startedAt: Date
    let bankSchemaVersion: TrainerScalar
    let cases: [TrainerCase]
    var answers: [String: String] = [:]
    var eligibility: [String: DiagnosticEligibility] = [:]
    var draftOptionID: String?
    var index: Int { answers.count }
}

struct DiagnosticResult: Codable, Identifiable, Equatable {
    let id: UUID
    let startedAt: Date
    let completedAt: Date
    let bankSchemaVersion: TrainerScalar
    let cases: [TrainerCase]
    let answers: [String: String]
    let eligibility: [String: DiagnosticEligibility]
    var strongestCount: Int { cases.filter { c in c.options.contains { $0.id == answers[c.id] && $0.isBest } }.count }
}

struct DiagnosticHistory: Codable, Equatable {
    var results: [DiagnosticResult] = []
}
