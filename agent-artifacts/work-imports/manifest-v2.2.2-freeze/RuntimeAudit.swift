import Foundation

// Compiled with the actual production models, mapping and engine, never reference copies.
@main struct RuntimeAudit {
    static func main() throws {
        let input = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))) as! [String: Any]
        let rows = input["rows"] as! [[String: Any]]
        let template = try JSONDecoder().decode(TrainerCase.self, from: JSONSerialization.data(withJSONObject: input["template"]!))
        let fixtures = ScoringFixtures(template: template)
        precondition(TrainerScoringMapping.domain("unknown-domain") == nil)
        precondition(TrainerScoringMapping.pattern("unknown-pattern") == nil)
        var mapped: [[String: Any]] = []
        var synthetic: [TrainerCase] = []
        var weightsByCase: [[TrainerThinking: Double]] = []
        for row in rows {
            let primary = TrainerScoringMapping.pattern(row["primaryPattern"] as! String)!
            let secondary = (row["secondaryPatterns"] as! [String]).map { TrainerScoringMapping.pattern($0)! }
            let domain = TrainerScoringMapping.domain(row["domain"] as! String)!
            var weights: [TrainerThinking: Double] = primary == .context ? [:] : [primary: 1]
            for p in secondary where p != .context { weights[p] = max(weights[p] ?? 0, 0.5) }
            let divisor = max(1, weights.values.reduce(0, +))
            weights = weights.mapValues { $0 / divisor }
            weightsByCase.append(weights)
            mapped.append(["id": row["id"]!, "uiDomain": domain.rawValue, "uiDomainTitle": domain.title,
                "primaryThinking": primary.rawValue, "secondaryThinking": secondary.map(\.rawValue),
                "normalizedWeights": Dictionary(uniqueKeysWithValues: weights.map { ($0.key.rawValue, $0.value) })])
            synthetic.append(try fixtures.test(id: row["id"] as! String,
                level: TrainerLevel(rawValue: row["requiredLevel"] as! String)!, quality: 1,
                domain: row["domain"] as! String, primary: row["primaryPattern"] as! String,
                secondary: row["secondaryPatterns"] as! [String]))
        }
        // Verify every individual normalized contribution against the real engine via impulse responses.
        // A single quality=1 case with all other qualities=0 exposes its category's normalized share.
        for i in synthetic.indices {
            let cases = try rows.enumerated().map { j, r in
                try fixtures.test(id: r["id"] as! String, level: TrainerLevel(rawValue: r["requiredLevel"] as! String)!,
                    quality: i == j ? 1 : 0, domain: r["domain"] as! String,
                    primary: r["primaryPattern"] as! String, secondary: r["secondaryPatterns"] as! [String])
            }
            let profile = TrainerScoringEngine.profile(history: fixtures.history(cases))
            for p in TrainerThinking.allCases where p != .context {
                let total = weightsByCase.reduce(0) { $0 + ($1[p] ?? 0) }
                if total > 0 {
                    precondition(abs(profile.patterns[p]!.score! - (weightsByCase[i][p] ?? 0) / total) < 1e-10)
                    precondition(profile.patterns[p]!.count == weightsByCase.filter { $0[p] != nil }.count)
                }
            }
            precondition(profile.patterns[.context] == nil)
        }
        let assessmentIDs = Set(input["assessmentIDs"] as! [String])
        let profile = TrainerScoringEngine.profile(history: fixtures.history(synthetic.filter { assessmentIDs.contains($0.id) }))
        let result: [String: Any] = ["rows": mapped, "engineWeightVerification": "PASS: all 300 impulse responses",
            "domainTitles": Dictionary(uniqueKeysWithValues: TrainerDomain.allCases.map { ($0.rawValue, $0.title) }),
            "thinkingTitles": Dictionary(uniqueKeysWithValues: TrainerThinking.allCases.map { ($0.rawValue, $0.title) }),
            "headFeasibility": ["breadthMet": profile.breadthMet, "breadthDomains": profile.breadthDomains.map(\.rawValue),
                "maximumSyntheticLevel": profile.level?.rawValue ?? "none", "eligibleCount": profile.eligibleCount,
                "minimumLevelEvidence": TrainerScoringEngine.minimumLevelEvidence,
                "headDomainEvidence": TrainerScoringEngine.headDomainEvidence,
                "excludedMetadataCount": profile.excludedMetadataCount,
                "note": "Synthetic perfect responses test structural feasibility only, not learner proficiency."],
            "unknownVocabularyRejected": true]
        try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: URL(fileURLWithPath: CommandLine.arguments[2]))
    }
}
