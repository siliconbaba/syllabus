import Foundation

@main struct TrainerSchemaTests {
    @MainActor static func main() throws {
        func check(_ value: Bool, _ name: String) { precondition(value, name); print("PASS: " + name) }
        let source = URL(fileURLWithPath: CommandLine.arguments[1])
        let fixture = source.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("Tests/Fixtures/trainer-gold-v1.json")
        let bank = try TrainerBank.load(url: source)
        let old = try TrainerBank.load(url: fixture, allowLegacy: true)
        let catalogURL = source.deletingLastPathComponent().appendingPathComponent("topics.json")
        let catalog = try TrainerCatalog.load(url: catalogURL)
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        try FileManager.default.copyItem(at: catalogURL, to: directory.appendingPathComponent("topics.json"))
        let raw = try JSONSerialization.jsonObject(with: Data(contentsOf: source)) as! [String: Any]
        func rejects(_ edit: (inout [String: Any]) -> Void, _ name: String) throws {
            var changed = raw; edit(&changed)
            let url = directory.appendingPathComponent("cases.json")
            try JSONSerialization.data(withJSONObject: changed).write(to: url)
            do { _ = try TrainerBank.load(url: url); fatalError("accepted: " + name) } catch { print("PASS: rejects " + name) }
        }
        func changeCase(_ root: inout [String: Any], _ edit: (inout [String: Any]) -> Void) {
            var cases = root["cases"] as! [[String: Any]]; edit(&cases[0]); root["cases"] = cases
        }
        check(bank.schemaVersion == .text("2.0") && bank.cases.count == 75, "v2 production bank decodes")
        for key in ["partId", "sourceTopicExplanation", "trainingEligible", "assessmentEligible"] {
            try rejects({ r in changeCase(&r) { $0.removeValue(forKey: key) } }, "missing " + key)
            try rejects({ r in changeCase(&r) { $0[key] = NSNull() } }, "null " + key)
        }
        for key in ["partId", "sourceTopicExplanation", "title"] {
            try rejects({ r in changeCase(&r) { $0[key] = "  " } }, "blank " + key)
        }
        try rejects({ r in changeCase(&r) { $0["partId"] = "unknown" } }, "unknown part")
        try rejects({ r in changeCase(&r) { $0["partId"] = "part-3" } }, "topic belongs to different part")
        try rejects({ r in changeCase(&r) { $0["topicId"] = "unknown" } }, "unknown topic")
        try rejects({ r in changeCase(&r) { $0["trainingEligible"] = "true" } }, "string instead of bool")
        try rejects({ $0["schemaVersion"] = "1.0" }, "v1 as production bank")
        try rejects({ r in changeCase(&r) { $0["scenarioFamilyId"] = "orphan" } }, "orphan family")
        check(bank.trainingCases.count == 75 && bank.cases.allSatisfy { $0.title != nil }, "75 training cases and titles")
        check(bank.cases.filter(\.assessmentEligible).count == 51 && bank.cases.allSatisfy { $0.assessmentEligible == ($0.scenarioFamilyId == nil) }, "51 standalone diagnostic cases; all linked training-only")
        var restored = raw
        let goldIDs = Set(old.cases.map(\.id))
        var cases = (restored["cases"] as! [[String: Any]]).filter { goldIDs.contains($0["id"] as! String) }
        for i in cases.indices {
            for key in ["partId", "title", "sourceTopicExplanation", "trainingEligible", "assessmentEligible"] { cases[i].removeValue(forKey: key) }
        }
        restored["cases"] = cases; restored["schemaVersion"] = "1.0"
        let original = try JSONSerialization.jsonObject(with: Data(contentsOf: fixture)) as! NSDictionary
        check((restored as NSDictionary) == original, "gold-standard existing fields and order unchanged")
        check(old.cases.allSatisfy { $0.partId.isEmpty && $0.title == nil && $0.sourceTopicExplanation.isEmpty && $0.trainingEligible && $0.assessmentEligible }, "legacy snapshot defaults")

        func caseWith(_ base: TrainerCase, training: Bool, assessment: Bool) throws -> TrainerCase {
            var object = try JSONSerialization.jsonObject(with: JSONEncoder().encode(base)) as! [String: Any]
            object["trainingEligible"] = training; object["assessmentEligible"] = assessment
            return try JSONDecoder().decode(TrainerCase.self, from: JSONSerialization.data(withJSONObject: object))
        }
        let trainingOnly = try caseWith(bank.cases[0], training: true, assessment: false)
        let assessmentOnly = try caseWith(bank.cases[1], training: false, assessment: true)
        let restricted = TrainerBank(schemaVersion: bank.schemaVersion, source: bank.source, cases: [trainingOnly, assessmentOnly])
        check(restricted.trainingCases == [trainingOnly], "mixed pool excludes trainingEligible false")
        check(catalog.casesForSection(trainingOnly.partId, in: restricted.cases) == [trainingOnly], "section pool respects training eligibility")
        check(catalog.casesForTopic(trainingOnly.topicId, in: restricted.cases) == [trainingOnly], "topic pool respects training eligibility")
        let store = TrainerStore(url: directory.appendingPathComponent("selection.json"))
        check(store.start(cases: restricted.cases) && store.attempt?.cases == [trainingOnly], "training start filters candidates")
        check(store.unseen(in: restricted.cases) == [assessmentOnly], "diagnostic unseen excludes assessmentEligible false")
        check(store.startDiagnostic(bank: restricted, count: nil) && store.diagnostic?.cases == [assessmentOnly], "diagnostic selection independent of training eligibility")
        store.selectDiagnostic(assessmentOnly.options[0].id, testID: assessmentOnly.id)
        check(store.confirmDiagnostic(testID: assessmentOnly.id), "assessment-only case confirms")
        check(store.unseen(in: restricted.cases).isEmpty, "eligible but seen still excluded")
        var progress = TrainerProgress()
        let wrong = assessmentOnly.options.first { !$0.isBest }!.id
        progress.record(test: assessmentOnly, optionID: wrong, mode: .mixed, at: Date())
        check(progress.unresolved(in: restricted.cases).isEmpty, "mistakes excludes trainingEligible false")
        check(!store.start(cases: [assessmentOnly], replacing: true), "empty eligible training pool cannot overwrite attempt")
        // Training exposure remains relevant when the current bank later allows assessment.
        store.select(trainingOnly.options[0].id); store.confirm()
        let newlyEligible = try caseWith(trainingOnly, training: true, assessment: true)
        check(store.unseen(in: [newlyEligible]).isEmpty, "training exposure still excludes newly assessment-eligible case")

        // Actual v1 JSON snapshots, without any new keys, inside persistence schema 3.
        let stateURL = directory.appendingPathComponent("legacy-state.json")
        let originalCases = original["cases"] as! [[String: Any]]
        let id = UUID(), attemptID = UUID()
        let answers = Dictionary(uniqueKeysWithValues: old.cases.map { ($0.id, $0.options[0].id) })
        let eligibility = Dictionary(uniqueKeysWithValues: old.cases.map { ($0.id, "cleanFirstAssessment") })
        let encounters = Dictionary(uniqueKeysWithValues: old.cases.map { ($0.id, ["firstEncounter":"assessment", "assessmentUsed":true] as [String:Any]) })
        let historyObject: [String:Any] = ["results":[["id":id.uuidString,"startedAt":0,"completedAt":1,"bankSchemaVersion":"1.0","cases":originalCases,"answers":answers,"eligibility":eligibility]]]
        let state: [String:Any] = ["schemaVersion":3,"progress":["results":[:]],"encounters":encounters,"diagnosticHistory":historyObject,
            "attempt":["id":attemptID.uuidString,"startedAt":0,"cases":originalCases,"index":0,"phase":"review","answers":[old.cases[0].id:old.cases[0].options[0].id]]]
        let bytes = try JSONSerialization.data(withJSONObject: state)
        try bytes.write(to: stateURL)
        let expectedHistory = try JSONDecoder().decode(DiagnosticHistory.self, from: JSONSerialization.data(withJSONObject: historyObject))
        let expectedProfile = TrainerScoringEngine.profile(history: expectedHistory)
        let reopened = TrainerStore(url: stateURL)
        check(!reopened.recoveryRequired && reopened.attempt?.cases == old.cases && reopened.attempt?.phase == .review, "old Attempt opens in review")
        check(reopened.diagnosticHistory == expectedHistory && TrainerScoringEngine.profile(history: reopened.diagnosticHistory) == expectedProfile, "old diagnostic review and scoring unchanged")
        check(try Data(contentsOf: stateURL) == bytes, "opening v1 snapshots does not rewrite persistence v3")
        check(reopened.start(cases: bank.cases, replacing: true) && reopened.attempt?.cases == bank.cases, "new attempt uses full v2 metadata")
        check(TrainerScoringEngine.profile(history: TrainerStore(url:stateURL).diagnosticHistory) == expectedProfile, "old profile unchanged after new v2 session persisted")
        let fresh = TrainerStore(url: directory.appendingPathComponent("new.json"))
        check(fresh.startDiagnostic(bank: bank, count: nil) && fresh.diagnostic?.bankSchemaVersion == .text("2.0"), "new diagnostic records bank schema 2 separately")
        check(fresh.diagnostic?.cases.count == 51 && fresh.diagnostic!.cases.allSatisfy { $0.assessmentEligible && $0.scenarioFamilyId == nil }, "ordinary diagnostic excludes every linked case")
        let persisted = try JSONSerialization.jsonObject(with: Data(contentsOf: directory.appendingPathComponent("new.json"))) as! [String:Any]
        check(persisted["schemaVersion"] as? Int == 3, "persistence remains schema 3")
    }
}
