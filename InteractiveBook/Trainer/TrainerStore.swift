import Foundation
import Combine

@MainActor final class TrainerStore: ObservableObject {
    private struct State: Codable {
        var schemaVersion: Int
        var attempt: TrainerAttempt?
        var progress: TrainerProgress?
        var encounters: [String: TrainerEncounter]?
        var diagnostic: DiagnosticAttempt?
        var diagnosticHistory: DiagnosticHistory?
    }
    @Published private(set) var attempt: TrainerAttempt?
    @Published private(set) var progress = TrainerProgress()
    @Published private(set) var encounters: [String: TrainerEncounter] = [:]
    @Published private(set) var diagnostic: DiagnosticAttempt?
    @Published private(set) var diagnosticHistory = DiagnosticHistory()
    @Published private(set) var recoveryRequired = false
    @Published var error: String?
    private let url: URL
    init(url: URL? = nil) {
        self.url = url ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Trainer", isDirectory: true).appendingPathComponent("state.json")
        guard FileManager.default.fileExists(atPath: self.url.path) else { return }
        do {
            let data = try Data(contentsOf: self.url)
            var saved = try JSONDecoder().decode(State.self, from: data)
            guard [1, 2, 3].contains(saved.schemaVersion) else { throw TrainerError.unsupportedVersion }
            if let a = saved.attempt { try Self.validate(a) }
            let originalVersion = saved.schemaVersion
            let needsMigration = saved.schemaVersion < 3
            if saved.schemaVersion == 1 {
                var migrated = TrainerProgress()
                if let a = saved.attempt {
                    for c in a.cases {
                        if let id = a.answers[c.id] { migrated.record(test: c, optionID: id, mode: .legacy, at: a.completedAt ?? a.startedAt) }
                    }
                }
                try backup(data, version: 1)
                saved.progress = migrated; saved.schemaVersion = 2
            }
            guard let progress = saved.progress else { throw TrainerError.invalidAttempt }
            try progress.validate()
            if saved.schemaVersion == 2 {
                try backup(originalVersion == 2 ? data : JSONEncoder().encode(saved), version: 2)
                saved.encounters = Dictionary(uniqueKeysWithValues: progress.results.keys.map {
                    ($0, TrainerEncounter(firstEncounter: .training, assessmentUsed: false))
                })
                // Include confirmed snapshot answers conservatively, even if an older state omitted aggregates.
                for id in saved.attempt?.answers.keys ?? Dictionary<String, String>().keys {
                    saved.encounters?[id] = TrainerEncounter(firstEncounter: .training, assessmentUsed: false)
                }
                saved.diagnostic = nil; saved.diagnosticHistory = DiagnosticHistory(); saved.schemaVersion = 3
            }
            try Self.validate(saved)
            if needsMigration {
                guard commit(saved) else { recoveryRequired = true; return }
            } else { publish(saved) }
        } catch {
            recoveryRequired = true
            self.error = (error as? TrainerError)?.localizedDescription ?? TrainerError.invalidAttempt.localizedDescription
        }
    }
    private func backup(_ data: Data, version: Int) throws {
        let backup = url.appendingPathExtension("slice\(version)-backup")
        if !FileManager.default.fileExists(atPath: backup.path) { try data.write(to: backup, options: .atomic) }
    }
    private var currentState: State {
        State(schemaVersion: 3, attempt: attempt, progress: progress, encounters: encounters,
              diagnostic: diagnostic, diagnosticHistory: diagnosticHistory)
    }
    private func publish(_ state: State) {
        attempt = state.attempt; progress = state.progress!
        encounters = state.encounters!; diagnostic = state.diagnostic; diagnosticHistory = state.diagnosticHistory!
        recoveryRequired = false
    }
    private static func validate(_ state: State) throws {
        guard state.schemaVersion == 3, let progress = state.progress,
              let encounters = state.encounters, let history = state.diagnosticHistory else { throw TrainerError.invalidAttempt }
        try progress.validate()
        if let a = state.attempt { try validate(a) }
        guard Set(progress.results.keys).isSubset(of: Set(encounters.keys)),
              encounters.allSatisfy({ !$0.key.isEmpty && ($0.value.firstEncounter != .assessment || $0.value.assessmentUsed) }),
              Set(history.results.map(\.id)).count == history.results.count else { throw TrainerError.invalidAttempt }
        if let a = state.attempt {
            guard Set(a.answers.keys).isSubset(of: Set(encounters.keys)) else { throw TrainerError.invalidAttempt }
        }
        func validateAnswers(_ cases: [TrainerCase], _ answers: [String: String], _ eligibility: [String: DiagnosticEligibility], completed: Bool) throws {
            try TrainerBank.validate(cases)
            guard completed ? answers.count == cases.count : answers.count < cases.count,
                  Set(answers.keys) == Set(cases.prefix(answers.count).map(\.id)),
                  Set(eligibility.keys) == Set(answers.keys) else { throw TrainerError.invalidAttempt }
            for c in cases.prefix(answers.count) {
                guard c.options.contains(where: { $0.id == answers[c.id] }), encounters[c.id]?.assessmentUsed == true else { throw TrainerError.invalidAttempt }
                if eligibility[c.id] == .cleanFirstAssessment && encounters[c.id]?.firstEncounter != .assessment { throw TrainerError.invalidAttempt }
            }
        }
        if let a = state.diagnostic {
            try validateAnswers(a.cases, a.answers, a.eligibility, completed: false)
            guard !history.results.contains(where: { $0.id == a.id }),
                  a.draftOptionID == nil || a.cases[a.index].options.contains(where: { $0.id == a.draftOptionID }) else { throw TrainerError.invalidAttempt }
        }
        for r in history.results {
            try validateAnswers(r.cases, r.answers, r.eligibility, completed: true)
        }
    }
    @discardableResult private func commit(_ state: State) -> Bool {
        do {
            try Self.validate(state)
            let data = try JSONEncoder().encode(state)
            try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
            try data.write(to: url, options: .atomic)
            publish(state); error = nil
            return true
        } catch { self.error = "Не удалось сохранить данные тренажёра: \(error.localizedDescription)"; return false }
    }
    static func validate(_ a: TrainerAttempt) throws {
        try TrainerBank.validate(a.cases)
        guard a.cases.indices.contains(a.index), a.answers.count == (a.phase == .answer ? a.index : a.index + 1),
              a.phase != .completed || a.index == a.cases.count - 1,
              (a.phase == .completed) == (a.completedAt != nil),
              a.phase == .answer || a.draftOptionID == nil else { throw TrainerError.invalidAttempt }
        for (i,c) in a.cases.enumerated() {
            if let selected = a.answers[c.id] {
                guard i <= a.index, c.options.contains(where: {$0.id == selected}) else { throw TrainerError.invalidAttempt }
            } else if i < a.index || i == a.index && a.phase != .answer { throw TrainerError.invalidAttempt }
        }
        if let draft = a.draftOptionID, !a.cases[a.index].options.contains(where: {$0.id == draft}) { throw TrainerError.invalidAttempt }
        let resolved = a.resolvedIDs ?? []
        guard Set(resolved).count == resolved.count,
              resolved.allSatisfy({ id in a.mode == .mistakes && a.cases.contains { c in c.id == id && c.options.contains { $0.id == a.answers[id] && $0.isBest } } }) else { throw TrainerError.invalidAttempt }
    }
    @discardableResult private func persist(_ value: TrainerAttempt?, progress: TrainerProgress? = nil,
                                            encounters: [String: TrainerEncounter]? = nil) -> Bool {
        var state = currentState
        state.attempt = value; state.progress = progress ?? self.progress; state.encounters = encounters ?? self.encounters
        return commit(state)
    }
    @discardableResult func start(cases: [TrainerCase], session: TrainerSession? = nil, replacing: Bool = false) -> Bool {
        guard (attempt == nil || replacing), !recoveryRequired else { return false }
        let candidates = cases.filter(\.trainingEligible)
        guard !candidates.isEmpty else { return false }
        var a = TrainerAttempt(id: UUID(), startedAt: Date(), cases: candidates)
        a.session = session
        return persist(a)
    }
    func select(_ id: String) {
        guard var a = attempt, a.phase == .answer, a.cases[a.index].options.contains(where: {$0.id == id}) else { return }
        a.draftOptionID = id; persist(a)
    }
    func confirm() {
        guard var a = attempt, a.phase == .answer, let id = a.draftOptionID else { return }
        let c = a.cases[a.index]
        var progress = self.progress
        let wasUnresolved = progress.results[c.id].map { $0.errors > 0 && !$0.resolved } ?? false
        progress.record(test: c, optionID: id, mode: a.mode, at: Date())
        if a.mode == .mistakes && wasUnresolved && progress.results[c.id]?.resolved == true {
            a.resolvedIDs = (a.resolvedIDs ?? []) + [c.id]
        }
        a.answers[c.id] = id; a.draftOptionID = nil; a.phase = .review
        var encounters = self.encounters
        if encounters[c.id] == nil { encounters[c.id] = TrainerEncounter(firstEncounter: .training, assessmentUsed: false) }
        persist(a, progress: progress, encounters: encounters)
    }
    func next() {
        guard var a = attempt, a.phase == .review else { return }
        if a.index == a.cases.count - 1 { a.phase = .completed; a.completedAt = Date() }
        else { a.index += 1; a.phase = .answer }
        persist(a)
    }
    @discardableResult func resetAttempt() -> Bool {
        guard !recoveryRequired, let a = attempt, a.phase != .completed else { return false }
        return persist(nil)
    }
    func unseen(in cases: [TrainerCase]) -> [TrainerCase] { cases.filter { $0.assessmentEligible && encounters[$0.id] == nil } }
    @discardableResult func startDiagnostic(bank: TrainerBank, count: Int?) -> Bool {
        guard !recoveryRequired, diagnostic == nil else { return false }
        let cases = TrainerCatalog.sample(unseen(in: bank.cases), count: count)
        guard !cases.isEmpty else { return false }
        var state = currentState
        state.diagnostic = DiagnosticAttempt(id: UUID(), startedAt: Date(), bankSchemaVersion: bank.schemaVersion, cases: cases)
        return commit(state)
    }
    func selectDiagnostic(_ optionID: String, testID: String) {
        guard var a = diagnostic, a.cases[a.index].id == testID,
              a.cases[a.index].options.contains(where: { $0.id == optionID }) else { return }
        a.draftOptionID = optionID
        var state = currentState; state.diagnostic = a; commit(state)
    }
    @discardableResult func confirmDiagnostic(testID: String) -> Bool {
        guard var a = diagnostic, a.cases[a.index].id == testID, let id = a.draftOptionID else { return false }
        var state = currentState
        var encounters = self.encounters
        a.eligibility[testID] = encounters[testID] == nil ? .cleanFirstAssessment : .previouslyConfirmed
        var encounter = encounters[testID] ?? TrainerEncounter(firstEncounter: .assessment, assessmentUsed: false)
        encounter.assessmentUsed = true; encounters[testID] = encounter
        a.answers[testID] = id; a.draftOptionID = nil
        state.encounters = encounters
        if a.answers.count == a.cases.count {
            let result = DiagnosticResult(id: a.id, startedAt: a.startedAt, completedAt: Date(), bankSchemaVersion: a.bankSchemaVersion,
                                          cases: a.cases, answers: a.answers, eligibility: a.eligibility)
            state.diagnosticHistory?.results.append(result); state.diagnostic = nil
        } else { state.diagnostic = a }
        return commit(state)
    }
    @discardableResult func resetDiagnostic() -> Bool {
        guard !recoveryRequired, diagnostic != nil else { return false }
        var state = currentState; state.diagnostic = nil
        return commit(state)
    }
    @discardableResult func resetProgress() -> Bool {
        do {
            for version in [1, 2] {
                let backup = url.appendingPathExtension("slice\(version)-backup")
                if FileManager.default.fileExists(atPath: backup.path) { try FileManager.default.removeItem(at: backup) }
            }
        } catch { self.error = "Не удалось удалить резервную копию: \(error.localizedDescription)"; return false }
        return commit(State(schemaVersion: 3, progress: TrainerProgress(), encounters: [:], diagnosticHistory: DiagnosticHistory()))
    }
}
