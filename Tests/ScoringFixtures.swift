import Foundation

struct ScoringFixtures {
    let template: TrainerCase
    func test(id: String, level: TrainerLevel, quality: Double, domain: String = "technical_delivery",
              primary: String = "evidence-before-release", secondary: [String] = []) throws -> TrainerCase {
        var object = try JSONSerialization.jsonObject(with: JSONEncoder().encode(template)) as! [String: Any]
        object["id"] = id; object["requiredLevel"] = level.rawValue; object["domain"] = domain
        object["primaryPattern"] = primary; object["secondaryPatterns"] = secondary
        object["context"] = "Синтетическая ситуация для проверки профиля. " + id
        object.removeValue(forKey: "scenarioFamilyId"); object.removeValue(forKey: "decisiveMutation")
        var options = object["options"] as! [[String: Any]]
        for i in options.indices { options[i]["isBest"] = i == 1; options[i]["decisionQuality"] = i == 0 ? quality : 0.99 }
        object["options"] = options
        return try JSONDecoder().decode(TrainerCase.self, from: JSONSerialization.data(withJSONObject: object))
    }
    func history(_ cases: [TrainerCase], date: Double = 100, eligibility: DiagnosticEligibility = .cleanFirstAssessment) -> DiagnosticHistory {
        guard !cases.isEmpty else { return DiagnosticHistory() }
        return DiagnosticHistory(results: [DiagnosticResult(id: UUID(), startedAt: Date(timeIntervalSince1970: date - 10),
            completedAt: Date(timeIntervalSince1970: date), bankSchemaVersion: .text("1.0"), cases: cases,
            answers: Dictionary(uniqueKeysWithValues: cases.map { ($0.id, $0.options[0].id) }),
            eligibility: Dictionary(uniqueKeysWithValues: cases.map { ($0.id, eligibility) }))])
    }
    func grouped(_ groups: [(TrainerLevel, Int, Double)], domains: [String] = ["technical_delivery"]) throws -> DiagnosticHistory {
        var cases: [TrainerCase] = []
        for (level, count, quality) in groups {
            for _ in 0..<count {
                let i = cases.count
                cases.append(try test(id: "fixture-\(i)", level: level, quality: quality, domain: domains[i % domains.count]))
            }
        }
        return history(cases)
    }
    func scenarios() throws -> [String: DiagnosticHistory] {
        var result: [String: DiagnosticHistory] = ["empty": DiagnosticHistory()]
        result["insufficient"] = try grouped([(.junior,4,0.9)])
        result["junior"] = try grouped([(.junior,5,0.82)])
        result["junior-plus"] = try grouped([(.junior,5,0.82),(.middle,5,0.65)])
        result["middle"] = try grouped([(.junior,5,0.82),(.middle,5,0.78)])
        result["middle-plus"] = try grouped([(.junior,5,0.82),(.middle,5,0.78),(.senior,5,0.61)])
        result["senior"] = try grouped([(.junior,5,0.82),(.middle,5,0.78),(.senior,5,0.70)])
        result["medium"] = try grouped([(.junior,10,0.82),(.middle,10,0.78),(.senior,10,0.70)])
        result["high"] = try grouped([(.junior,15,0.82),(.middle,15,0.78),(.senior,15,0.70)])
        let tags = ["dependency-decoupling", "evidence-before-release", "blameless-system-thinking", "contract-volatility", "risk-based-hotfix", "decision-at-right-level"]
        var thinking: [TrainerCase] = []
        for (i, tag) in tags.enumerated() {
            for j in 0..<5 { thinking.append(try test(id: "thinking-\(i)-\(j)", level: .junior,
                quality: [0.95,0.90,0.85,0.60,0.50,0.40][i], domain: j == 0 && i == 0 ? "people_management" : "technical_delivery", primary: tag)) }
        }
        result["thinking"] = history(thinking)
        return result
    }
    func writeStates(to folder: URL) throws {
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        for (name, history) in try scenarios() {
            let object = try JSONSerialization.jsonObject(with: JSONEncoder().encode(history))
            var encounters: [String: Any] = [:]
            for c in history.results.flatMap(\.cases) { encounters[c.id] = ["firstEncounter": "assessment", "assessmentUsed": true] }
            let state: [String: Any] = ["schemaVersion":3, "progress":["results":[:]], "encounters":encounters, "diagnosticHistory":object]
            try JSONSerialization.data(withJSONObject: state, options: [.prettyPrinted, .sortedKeys]).write(to: folder.appendingPathComponent(name + ".json"))
        }
    }
}
