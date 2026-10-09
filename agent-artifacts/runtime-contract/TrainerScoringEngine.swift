import Foundation

enum TrainerLevel: String, CaseIterable, Codable { case junior, middle, senior, head
    var title: String { rawValue.capitalized }
    var threshold: Double { switch self { case .junior: return 0.78; case .middle: return 0.72; case .senior: return 0.66; case .head: return 0.60 } }
}
enum TrainerConfidence: String, Codable {
    case insufficient, low, medium, high
    init(count: Int) { self = count < 5 ? .insufficient : count < 10 ? .low : count < 15 ? .medium : .high }
    var title: String { switch self {
    case .insufficient: return "Недостаточно данных"; case .low: return "Низкая уверенность"
    case .medium: return "Средняя уверенность"; case .high: return "Высокая уверенность"
    } }
}
struct TrainerProfile: Equatable {
    struct Metric: Equatable {
        let score: Double?
        let count: Int
        var confidence: TrainerConfidence { TrainerConfidence(count: count) }
        var littleData: Bool { count < 3 }
    }
    struct Requirement: Equatable {
        let level: TrainerLevel
        let threshold: Double
        let evidence: Metric
        var missingCount: Int { max(0, 5 - evidence.count) }
        var met: Bool { missingCount == 0 && (evidence.score ?? -1) + 1e-10 >= threshold }
    }
    struct PairEvidence: Equatable {
        let testID: String
        let revision: Int
        let familyID: String
        let mutation: String?
        let selectedOptionID: String
    }
    let scoringModelVersion: Int
    let eligibleCount: Int
    let excludedMetadataCount: Int
    let level: TrainerLevel?
    let plus: Bool
    let confidence: TrainerConfidence
    let relevantEvidenceCount: Int
    let buckets: [TrainerLevel: Metric]
    let domains: [TrainerDomain: Metric]
    let patterns: [TrainerThinking: Metric]
    let nextLevel: TrainerLevel?
    let requirements: [Requirement]
    let breadthDomains: [TrainerDomain]
    let breadthMet: Bool
    let pairEvidence: [PairEvidence]
    var levelTitle: String? { level.map { $0.title + (plus ? "+" : "") } }
    var missingEvidence: Int { requirements.reduce(0) { $0 + $1.missingCount } }
    var strengths: [TrainerThinking] { rankedPatterns.prefix(3).map { $0 } }
    var growth: [TrainerThinking] {
        Array(rankedPatterns.filter { !strengths.contains($0) }.suffix(3).reversed())
    }
    private var rankedPatterns: [TrainerThinking] {
        patterns.keys.filter { $0 != .context && (patterns[$0]?.count ?? 0) >= 5 }.sorted {
            let a = patterns[$0]?.score ?? 0, b = patterns[$1]?.score ?? 0
            return a == b ? $0.rawValue < $1.rawValue : a > b
        }
    }
}

struct TrainerScoringEngine {
    static let scoringModelVersion = 1
    static let minimumLevelEvidence = 5
    static let headDomainEvidence = 3
    private struct Evidence {
        let test: TrainerCase
        let option: TrainerCase.Option
        let level: TrainerLevel
        let quality: Double
    }
    static func profile(history: DiagnosticHistory) -> TrainerProfile {
        var seen = Set<String>(), evidence: [Evidence] = [], invalid = 0
        // Stable chronological first encounter, independent of array ordering.
        let results = history.results.sorted {
            if $0.completedAt != $1.completedAt { return $0.completedAt < $1.completedAt }
            if $0.startedAt != $1.startedAt { return $0.startedAt < $1.startedAt }
            return $0.id.uuidString < $1.id.uuidString
        }
        for result in results {
            for c in result.cases where result.eligibility[c.id] == .cleanFirstAssessment {
                guard seen.insert(c.id).inserted else { continue }
                guard let option = c.options.first(where: { $0.id == result.answers[c.id] }),
                      case .number(let quality) = option.decisionQuality, quality.isFinite, (0...1).contains(quality),
                      let level = TrainerLevel(rawValue: c.requiredLevel.lowercased()) else { invalid += 1; continue }
                evidence.append(Evidence(test: c, option: option, level: level, quality: quality))
            }
        }
        func metric(_ items: [Evidence]) -> TrainerProfile.Metric {
            TrainerProfile.Metric(score: items.isEmpty ? nil : items.map(\.quality).reduce(0,+) / Double(items.count), count: items.count)
        }
        let buckets = Dictionary(uniqueKeysWithValues: TrainerLevel.allCases.map { level in (level, metric(evidence.filter { $0.level == level })) })
        let domains = Dictionary(uniqueKeysWithValues: TrainerDomain.allCases.map { domain in
            (domain, metric(evidence.filter { TrainerScoringMapping.domain($0.test.domain) == domain }))
        })
        let breadth = TrainerDomain.allCases.filter { domain in
            evidence.filter { ($0.level == .senior || $0.level == .head) && TrainerScoringMapping.domain($0.test.domain) == domain }.count >= headDomainEvidence
        }
        let breadthMet = breadth.count >= 5 && (breadth.contains(.people) || breadth.contains(.stakeholders)) && (breadth.contains(.portfolio) || breadth.contains(.finance))
        func requirements(_ level: TrainerLevel) -> [TrainerProfile.Requirement] {
            let thresholds: [(TrainerLevel, Double)]
            switch level {
            case .junior: thresholds = [(.junior, 0.78)]
            case .middle: thresholds = [(.junior, 0.80), (.middle, 0.72)]
            case .senior: thresholds = [(.junior, 0.80), (.middle, 0.75), (.senior, 0.66)]
            case .head: thresholds = [(.junior, 0.80), (.middle, 0.75), (.senior, 0.70), (.head, 0.60)]
            }
            return thresholds.map { TrainerProfile.Requirement(level: $0.0, threshold: $0.1, evidence: buckets[$0.0]!) }
        }
        var confirmed: TrainerLevel?
        for level in TrainerLevel.allCases {
            guard requirements(level).allSatisfy(\.met), level != .head || breadthMet else { break }
            confirmed = level
        }
        let next = confirmed.flatMap { value -> TrainerLevel? in
            let i = TrainerLevel.allCases.firstIndex(of: value)! + 1
            return i < TrainerLevel.allCases.count ? TrainerLevel.allCases[i] : nil
        } ?? (confirmed == nil ? .junior : nil)
        let gaps = next.map(requirements) ?? []
        // '+' requires positive evidence in the next bucket, never compensates for an unconfirmed base.
        // A failed prerequisite or Head breadth alone must not manufacture a plus.
        let plus = confirmed != nil && next.map { level in
            let bucket = buckets[level]!
            return bucket.count >= minimumLevelEvidence && (bucket.score ?? -1) + 1e-10 >= level.threshold - 0.10
                && (bucket.score ?? -1) + 1e-10 < level.threshold
        } == true
        let relevant = confirmed.map { requirements($0).map { $0.evidence.count }.min() ?? 0 } ?? (buckets[.junior]?.count ?? 0)
        var totals: [TrainerThinking: (sum: Double, weight: Double, count: Int)] = [:]
        for e in evidence {
            var weights: [TrainerThinking: Double] = [:]
            if let p = TrainerScoringMapping.pattern(e.test.primaryPattern), p != .context { weights[p] = 1 }
            for raw in e.test.secondaryPatterns {
                if let p = TrainerScoringMapping.pattern(raw), p != .context { weights[p] = max(weights[p] ?? 0, 0.5) }
            }
            // Collapse aliases per category, then cap total influence of one case at 1.
            let divisor = max(1, weights.values.reduce(0,+))
            for (p, weight) in weights {
                var value = totals[p] ?? (0,0,0)
                let normalized = weight / divisor
                value.sum += normalized * e.quality; value.weight += normalized; value.count += 1
                totals[p] = value
            }
        }
        let patterns = totals.mapValues { TrainerProfile.Metric(score: $0.sum / $0.weight, count: $0.count) }
        return TrainerProfile(scoringModelVersion: scoringModelVersion, eligibleCount: evidence.count, excludedMetadataCount: invalid,
            level: confirmed, plus: plus, confidence: TrainerConfidence(count: relevant), relevantEvidenceCount: relevant,
            buckets: buckets, domains: domains, patterns: patterns, nextLevel: next, requirements: gaps,
            breadthDomains: breadth, breadthMet: breadthMet, pairEvidence: evidence.compactMap { e in
                e.test.scenarioFamilyId.map { TrainerProfile.PairEvidence(testID: e.test.id, revision: e.test.revision, familyID: $0,
                    mutation: e.test.decisiveMutation, selectedOptionID: e.option.id) }
            })
    }
}
