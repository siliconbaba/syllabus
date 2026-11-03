import Foundation

@main struct TrainerTests {
    @MainActor static func main() throws {
        func check(_ value: Bool, _ name: String) { precondition(value, name); print("PASS: " + name) }
        let source = URL(fileURLWithPath: CommandLine.arguments[1])
        let bank = try TrainerBank.load(url: source)
        check(bank.cases.count == 150, "150 production cases load")
        func rejects(_ edit: (inout [[String: Any]]) -> Void) throws {
            var root = try JSONSerialization.jsonObject(with: Data(contentsOf: source)) as! [String: Any]
            var cases = root["cases"] as! [[String: Any]]; edit(&cases); root["cases"] = cases
            let decoded = try JSONDecoder().decode(TrainerBank.self, from: JSONSerialization.data(withJSONObject: root))
            do { try TrainerBank.validate(decoded.cases); fatalError("accepted invalid bank") } catch {}
        }
        try rejects { $0[1]["id"] = $0[0]["id"] }
        try rejects { cases in var opts = cases[0]["options"] as! [[String: Any]]; for i in opts.indices {opts[i]["isBest"] = false}; cases[0]["options"] = opts }
        try rejects { cases in var opts = cases[0]["options"] as! [[String: Any]]; for i in opts.indices {opts[i]["isBest"] = true}; cases[0]["options"] = opts }
        try rejects { cases in var opts = cases[0]["options"] as! [[String: Any]]; opts[1]["id"] = opts[0]["id"]; cases[0]["options"] = opts }
        print("PASS: duplicate case/option IDs and zero/multiple best choices rejected")
        try rejects { $0[0]["scenarioFamilyId"] = "" }
        try rejects { $0[0].removeValue(forKey: "decisiveMutation") }
        try rejects { $0[0]["type"] = "unsupported" }
        for quality in [-0.01, 1.01] {
            try rejects { cases in var options = cases[0]["options"] as! [[String: Any]]; options[0]["decisionQuality"] = quality; cases[0]["options"] = options }
        }
        // Compare every production field, including source/type and all option metadata.
        let roundtrip = try JSONSerialization.jsonObject(with: JSONEncoder().encode(bank)) as! NSDictionary
        let raw = try JSONSerialization.jsonObject(with: Data(contentsOf: source)) as! NSDictionary
        func withoutNulls(_ value: Any) -> Any {
            if let map = value as? [String: Any] { return map.filter { !($0.value is NSNull) }.mapValues(withoutNulls) }
            if let list = value as? [Any] { return list.map(withoutNulls) }
            return value
        }
        check((withoutNulls(roundtrip) as! NSDictionary) == (withoutNulls(raw) as! NSDictionary), "all production fields roundtrip unchanged")
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("TrainerTests-" + UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: dir) }
        let url = dir.appendingPathComponent("state.json")
        let store = TrainerStore(url: url)
        check(store.start(cases: bank.cases), "start persisted")
        let initial = store.attempt
        store.confirm(); store.select("missing")
        check(store.attempt == initial, "no answer without valid selection")
        store.select("A"); store.select("B")
        check(TrainerStore(url: url).attempt?.draftOptionID == "B", "draft restored and can change")
        store.confirm()
        let review = store.attempt
        store.select("A"); store.confirm()
        check(store.attempt == review, "confirmed answer immutable")
        let restored = TrainerStore(url: url)
        check(restored.attempt == review && restored.attempt?.phase == .review, "exact review restored after relaunch")
        restored.next()
        check(TrainerStore(url: url).attempt?.index == 1 && TrainerStore(url: url).attempt?.phase == .answer, "next question phase persisted")
        for _ in 1..<bank.cases.count { restored.select("A"); restored.confirm(); restored.next() }
        let completed = TrainerStore(url: url)
        check(completed.attempt?.phase == .completed && completed.attempt?.answers.count == bank.cases.count, "All answers and summary restored")
        check(completed.attempt?.cases == bank.cases, "review content snapshot preserved")
        var invalid = completed.attempt!; invalid.answers[invalid.cases[0].id] = "missing"
        do {try TrainerStore.validate(invalid); fatalError("bad answer accepted")} catch {}
        check(!completed.start(cases: bank.cases), "cannot overwrite existing attempt")
        check(completed.resetProgress() && TrainerStore(url: url).attempt == nil, "reset persisted")
        check(completed.start(cases: bank.cases), "new attempt after reset")
        try Data("broken".utf8).write(to: url)
        let corrupted = TrainerStore(url: url)
        check(corrupted.recoveryRequired && !corrupted.start(cases: bank.cases), "corruption cannot silently overwrite results")
        check(try Data(contentsOf: url) == Data("broken".utf8), "corrupt data retained")
        check(corrupted.resetProgress(), "explicit reset recovers")
        let legacyURL = source.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("Tests/Fixtures/trainer-legacy-bank.json")
        let legacy = try TrainerBank.load(url: legacyURL, allowLegacy: true)
        let legacyStore = TrainerStore(url: dir.appendingPathComponent("legacy.json"))
        check(legacyStore.start(cases: legacy.cases), "old five-case bank accepted for snapshots")
        legacyStore.select("b"); legacyStore.confirm()
        let oldAttempt = legacyStore.attempt!
        let reopened = TrainerStore(url: dir.appendingPathComponent("legacy.json"))
        check(reopened.attempt == oldAttempt && reopened.attempt?.phase == .review && reopened.attempt?.cases.count == 5, "legacy review survives production bank update")
        check(!reopened.start(cases: bank.cases) && reopened.attempt == oldAttempt, "new bank cannot replace active snapshot")
        check(reopened.resetProgress() && reopened.start(cases: bank.cases) && reopened.attempt?.cases.count == bank.cases.count, "reset starts current bank without changing legacy snapshot implicitly")
        let catalog = try TrainerCatalog.load(url: source.deletingLastPathComponent().appendingPathComponent("topics.json"))
        check(Set(bank.cases.map(\.topicId)).isSubset(of: Set(catalog.topics.map(\.id))), "catalog covers bank topics")
        for size in [5, 10, 15, bank.cases.count] {
            let sample = TrainerCatalog.sample(bank.cases, count: size)
            check(sample.count == size && Set(sample.map(\.id)).count == size, "mixed size and uniqueness \(size)")
            let sessionStore = TrainerStore(url: dir.appendingPathComponent("sample-\(size).json"))
            check(sessionStore.start(cases: sample, session: TrainerSession(kind: .mixed, title: "Смешанная")), "mixed start")
            check(TrainerStore(url: dir.appendingPathComponent("sample-\(size).json")).attempt?.cases == sample, "fixed order after reload")
        }
        check(TrainerCatalog.sample(bank.cases, count: nil).count == bank.trainingCases.count, "all sample")
        check(TrainerCatalog.sample(Array(bank.cases.prefix(2)), count: 5).count == 2, "small bank sample clamped")
        let sections = catalog.availableSections(in: bank.cases)
        check(!sections.isEmpty && sections.allSatisfy { !catalog.casesForSection($0.id, in: bank.cases).isEmpty }, "only populated sections")
        let section = sections.first { catalog.availableTopics(sectionID: $0.id, in: bank.cases).count > 1 }!
        let topics = catalog.availableTopics(sectionID: section.id, in: bank.cases)
        let sectionCases = catalog.casesForSection(section.id, in: bank.cases)
        check(sectionCases.allSatisfy { Set(topics.map(\.id)).contains($0.topicId) }, "section filter")
        check(catalog.casesForTopic(topics[0].id, in: bank.cases).allSatisfy { $0.topicId == topics[0].id }, "topic filter")
        let progressURL = dir.appendingPathComponent("progress.json")
        let training = TrainerStore(url: progressURL)
        let test = bank.cases.first { $0.assessmentEligible }!
        let wrong = test.options.first { !$0.isBest }!.id
        let best = test.options.first { $0.isBest }!.id
        check(training.start(cases: [test], session: TrainerSession(kind: .mixed, title: "Смешанная")), "progress training starts")
        training.select(wrong); training.confirm(); training.confirm()
        check(training.progress.results[test.id]?.errors == 1 && training.progress.results[test.id]?.answers == 1, "wrong confirmation records once")
        check(training.resetAttempt() && training.progress.results[test.id]?.errors == 1, "reset attempt preserves progress")
        let mistakes = TrainerSession(kind: .mistakes, title: "Работа над ошибками")
        check(training.start(cases: training.progress.unresolved(in: bank.cases), session: mistakes), "mistakes selects unresolved")
        training.select(wrong); training.confirm()
        check(training.progress.results[test.id]?.errors == 2 && training.progress.results[test.id]?.resolved == false, "repeat error increments")
        check(training.resetAttempt(), "reset mistakes attempt")
        check(training.start(cases: [test], session: mistakes), "retry starts")
        training.select(best); training.confirm(); training.next()
        let persistedProgress = TrainerStore(url: progressURL)
        check(persistedProgress.progress.results[test.id]?.resolved == true && persistedProgress.progress.results[test.id]?.errors == 2, "resolved history retained")
        check(persistedProgress.attempt?.resolvedIDs == [test.id], "resolved in session summary")
        check(persistedProgress.progress.unresolved(in: bank.cases).isEmpty, "resolved excluded from mistakes")
        check(!persistedProgress.resetAttempt(), "current reset only applies to unfinished attempt")
        check(training.start(cases: [test], session: TrainerSession(kind: .mixed, title: "Смешанная"), replacing: true), "replace completed attempt")
        training.select(wrong); training.confirm()
        check(training.progress.results[test.id]?.resolved == false && training.progress.results[test.id]?.errors == 3, "new mistake reopens resolved case")
        check(training.progress.unresolved(in: bank.cases.filter { $0.id != test.id }).isEmpty, "removed case skipped")
        check(training.progress.results[test.id] != nil, "removed case history retained")
        var revisedObject = try JSONSerialization.jsonObject(with: JSONEncoder().encode(test)) as! [String: Any]
        revisedObject["revision"] = test.revision + 1; revisedObject["context"] = "Обновлённая ситуация"
        let revised = try JSONDecoder().decode(TrainerCase.self, from: JSONSerialization.data(withJSONObject: revisedObject))
        check(training.progress.unresolved(in: [revised]) == [revised], "mistakes uses current bank revision")
        check(training.attempt?.cases == [test], "active snapshot independent of revised bank")
        check(training.resetAttempt(), "reset before ordinary correct answer")
        check(training.start(cases: [test]), "ordinary retry starts")
        training.select(best); training.confirm()
        check(training.progress.results[test.id]?.resolved == false, "ordinary correct does not resolve mistakes")
        check(training.resetProgress(), "full reset")
        let empty = TrainerStore(url: progressURL)
        check(empty.attempt == nil && empty.progress.results.isEmpty, "full reset removes attempt and progress")

        // Actual Slice 1 JSON: no mode/resolved IDs/progress, numeric envelope version 1.
        var legacyAttempt = try JSONSerialization.jsonObject(with: JSONEncoder().encode(oldAttempt)) as! [String: Any]
        legacyAttempt.removeValue(forKey: "session"); legacyAttempt.removeValue(forKey: "resolvedIDs")
        let migrationURL = dir.appendingPathComponent("migration.json")
        let oldData = try JSONSerialization.data(withJSONObject: ["schemaVersion": 1, "attempt": legacyAttempt])
        try oldData.write(to: migrationURL)
        let migrated = TrainerStore(url: migrationURL)
        check(migrated.attempt == oldAttempt && !migrated.recoveryRequired, "Slice 1 snapshot and review migrate")
        check(migrated.progress.results.count == 1, "Slice 1 confirmed answers backfilled")
        check(try Data(contentsOf: migrationURL.appendingPathExtension("slice1-backup")) == oldData, "migration keeps original backup")
        check(TrainerStore(url: migrationURL).progress == migrated.progress, "migration is not repeated")
        check(migrated.attempt?.cases == legacy.cases && migrated.attempt?.cases != bank.cases, "bank revision cannot mutate old snapshot")
        check(migrated.resetProgress() && !FileManager.default.fileExists(atPath: migrationURL.appendingPathExtension("slice1-backup").path), "full reset removes migration recovery copy")
        let unknownURL = dir.appendingPathComponent("unknown.json")
        try Data("{\"schemaVersion\":99}".utf8).write(to: unknownURL)
        let unknown = TrainerStore(url: unknownURL)
        check(unknown.recoveryRequired && !unknown.start(cases: bank.cases), "unsupported version preserved")
        let diagnosticURL = dir.appendingPathComponent("diagnostic.json")
        let assessment = TrainerStore(url: diagnosticURL)
        check(assessment.start(cases: Array(bank.cases.prefix(2))), "training remains independent")
        assessment.select(bank.cases[0].options[0].id); assessment.confirm()
        let learningSnapshot = assessment.attempt
        let learningProgress = assessment.progress
        check(assessment.unseen(in: bank.cases).count == bank.cases.filter { $0.assessmentEligible && $0.id != bank.cases[0].id }.count && !assessment.unseen(in: bank.cases).contains { $0.id == bank.cases[0].id }, "training confirmed excluded from unseen")
        check(assessment.encounters[bank.cases[0].id]?.firstEncounter == .training, "first training encounter recorded")
        check(assessment.startDiagnostic(bank: bank, count: 10), "assessment starts from unseen")
        let diagnosticCases = assessment.diagnostic!.cases
        check(diagnosticCases.count == 10 && Set(diagnosticCases.map(\.id)).count == 10, "assessment size unique IDs")
        check(assessment.attempt == learningSnapshot, "diagnostic start keeps training attempt")
        check(!assessment.startDiagnostic(bank: bank, count: 10), "active diagnostic cannot silently replace")
        let first = diagnosticCases[0]
        assessment.selectDiagnostic(first.options[0].id, testID: first.id)
        let restoredDiagnostic = TrainerStore(url: diagnosticURL)
        check(restoredDiagnostic.diagnostic?.draftOptionID == first.options[0].id && restoredDiagnostic.diagnostic?.cases == diagnosticCases, "diagnostic draft and order restored")
        check(assessment.confirmDiagnostic(testID: first.id), "assessment confirms")
        check(assessment.diagnostic?.index == 1 && assessment.diagnostic?.draftOptionID == nil, "confirm immediately advances without review")
        check(!assessment.confirmDiagnostic(testID: first.id), "stale repeated confirm rejected")
        assessment.selectDiagnostic(first.options[1].id, testID: first.id)
        check(assessment.diagnostic?.answers[first.id] == first.options[0].id, "assessment confirmed answer immutable")
        check(assessment.encounters[first.id]?.assessmentUsed == true && assessment.encounters[first.id]?.firstEncounter == .assessment, "assessment first encounter and used flag")
        check(!assessment.unseen(in: bank.cases).contains { $0.id == first.id }, "assessment used no longer unseen")
        check(TrainerStore(url: diagnosticURL).diagnostic == assessment.diagnostic, "resume next unanswered with same order")
        for c in diagnosticCases.dropFirst() {
            assessment.selectDiagnostic(c.options[0].id, testID: c.id)
            check(assessment.confirmDiagnostic(testID: c.id), "assessment next confirmation")
        }
        check(assessment.diagnostic == nil && assessment.diagnosticHistory.results.count == 1, "completion atomically archives diagnostic")
        let historical = assessment.diagnosticHistory.results[0]
        check(historical.cases == diagnosticCases && historical.answers.count == 10 && historical.eligibility.values.allSatisfy { $0 == .cleanFirstAssessment }, "immutable complete snapshot and eligibility")
        check(assessment.progress == learningProgress && assessment.attempt == learningSnapshot, "assessment never changes learning progress or attempt")
        _ = historical.strongestCount
        _ = historical.cases.map { c in c.options.first { $0.id == historical.answers[c.id] }?.explanation }
        check(assessment.diagnosticHistory.results[0] == historical, "review reads do not mutate result")
        check(TrainerStore(url: diagnosticURL).diagnosticHistory == assessment.diagnosticHistory, "history survives restart")
        var changed = try JSONSerialization.jsonObject(with: JSONEncoder().encode(bank)) as! [String: Any]
        var changedCases = changed["cases"] as! [[String: Any]]
        for i in changedCases.indices { changedCases[i]["revision"] = 99; changedCases[i]["context"] = "New bank context" }
        changed["cases"] = changedCases
        let changedBank = try JSONDecoder().decode(TrainerBank.self, from: JSONSerialization.data(withJSONObject: changed))
        check(assessment.startDiagnostic(bank: changedBank, count: nil), "new diagnostic uses remaining unseen")
        check(Set(assessment.diagnostic!.cases.map(\.id)).isDisjoint(with: Set(diagnosticCases.map(\.id))), "new diagnostic excludes old assessment cases")
        check(assessment.diagnosticHistory.results[0] == historical, "bank/revision replacement leaves history unchanged")
        check(assessment.resetDiagnostic() && assessment.diagnosticHistory.results[0] == historical && assessment.progress == learningProgress, "diagnostic reset retains history and training")
        // A concurrent learning confirmation must remove clean eligibility at answer time.
        let overlap = TrainerStore(url: dir.appendingPathComponent("overlap.json"))
        let smallBank = TrainerBank(schemaVersion: bank.schemaVersion, source: bank.source, cases: [test])
        check(overlap.startDiagnostic(bank: smallBank, count: nil) && overlap.start(cases: [test]), "independent concurrent sessions")
        overlap.select(wrong); overlap.confirm()
        overlap.selectDiagnostic(best, testID: test.id); overlap.confirmDiagnostic(testID: test.id)
        check(overlap.diagnosticHistory.results[0].eligibility[test.id] == .previouslyConfirmed, "interleaved training marks encounter not clean")
        check(overlap.unseen(in: [test]).isEmpty, "no unseen when exhausted")
        check(!overlap.startDiagnostic(bank: smallBank, count: nil), "empty unseen cannot start")
        check(assessment.resetProgress() && assessment.diagnosticHistory.results.isEmpty && assessment.encounters.isEmpty && assessment.progress.results.isEmpty && assessment.attempt == nil, "full reset clears all assessment and training state")
        let cleared = TrainerStore(url: diagnosticURL)
        check(cleared.diagnosticHistory.results.isEmpty && cleared.unseen(in: bank.cases).count == bank.cases.filter(\.assessmentEligible).count, "full reset persisted and restores unseen")

        let v2URL = dir.appendingPathComponent("v2.json")
        let progressObject = try JSONSerialization.jsonObject(with: JSONEncoder().encode(learningProgress))
        let attemptObject = try JSONSerialization.jsonObject(with: JSONEncoder().encode(learningSnapshot!))
        let v2Data = try JSONSerialization.data(withJSONObject: ["schemaVersion": 2, "progress": progressObject, "attempt": attemptObject])
        try v2Data.write(to: v2URL)
        let from2 = TrainerStore(url: v2URL)
        check(from2.progress == learningProgress && from2.attempt == learningSnapshot && from2.diagnosticHistory.results.isEmpty, "migration 2 to 3 preserves training")
        check(from2.encounters[bank.cases[0].id]?.firstEncounter == .training && from2.unseen(in: bank.cases).count == bank.cases.filter { $0.assessmentEligible && $0.id != bank.cases[0].id }.count, "migration seeds eligibility conservatively")
        check(FileManager.default.fileExists(atPath: v2URL.appendingPathExtension("slice2-backup").path), "v2 migration backup")
        check(try Data(contentsOf: v2URL.appendingPathExtension("slice2-backup")) == v2Data, "v2 backup byte-identical")
        let afterMigration = try Data(contentsOf: v2URL)
        _ = TrainerStore(url: v2URL)
        check(try Data(contentsOf: v2URL) == afterMigration, "v2 migration idempotent")
        try oldData.write(to: migrationURL)
        let chain = TrainerStore(url: migrationURL)
        let chainJSON = try JSONSerialization.jsonObject(with: Data(contentsOf: migrationURL)) as! [String: Any]
        check(chainJSON["schemaVersion"] as? Int == 3 && chain.attempt == oldAttempt && chain.progress.results.count == 1 && chain.encounters.count == 1, "full migration chain 1 to 2 to 3")
        check(FileManager.default.fileExists(atPath: migrationURL.appendingPathExtension("slice1-backup").path) && FileManager.default.fileExists(atPath: migrationURL.appendingPathExtension("slice2-backup").path), "full chain keeps both backups")
        let corruptV3 = dir.appendingPathComponent("corrupt-v3.json")
        let corruptData = Data("{\"schemaVersion\":3,\"progress\":{\"results\":{}}}".utf8)
        try corruptData.write(to: corruptV3)
        let protected = TrainerStore(url: corruptV3)
        check(protected.recoveryRequired && !protected.startDiagnostic(bank: bank, count: 10), "corrupt v3 protected")
        check(try Data(contentsOf: corruptV3) == corruptData, "corrupt v3 retained")
        let blocker = dir.appendingPathComponent("file"); try Data().write(to: blocker)
        let failing = TrainerStore(url: blocker.appendingPathComponent("state.json"))
        check(!failing.start(cases: bank.cases) && failing.attempt == nil && failing.error != nil, "write failure does not publish unsaved progress")
    }
}
