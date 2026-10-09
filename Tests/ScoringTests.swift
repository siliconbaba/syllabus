import Foundation

@main struct ScoringTests {
    @MainActor static func main() throws {
        func check(_ v: Bool, _ message: String) { precondition(v, message); print("PASS: " + message) }
        func near(_ a: Double?, _ b: Double) -> Bool { a.map { abs($0-b) < 1e-9 } ?? false }
        let bank = try TrainerBank.load(url: URL(fileURLWithPath: CommandLine.arguments[1]))
        let f = ScoringFixtures(template: bank.cases[0])
        func profile(_ groups: [(TrainerLevel, Int, Double)], domains: [String] = ["technical_delivery"]) throws -> TrainerProfile {
            TrainerScoringEngine.profile(history: try f.grouped(groups, domains: domains))
        }
        let fixtures = try f.scenarios()
        for name in ["junior","junior-plus","middle","middle-plus","senior"] {
            let p = TrainerScoringEngine.profile(history: fixtures[name]!)
            check(p.levelTitle == name.replacingOccurrences(of: "-plus", with: "+").capitalized, "fixture " + name)
        }
        check(try profile([(.junior,5,0.779)]).level == nil, "Junior below threshold")
        check(try profile([(.junior,5,0.78)]).level == .junior, "Junior boundary")
        check(try profile([(.junior,5,0.80),(.middle,5,0.72)]).level == .middle, "Middle boundary")
        check(try profile([(.junior,5,0.80),(.middle,5,0.75),(.senior,5,0.66)]).level == .senior, "Senior boundary")
        check(try profile([(.junior,5,0.79),(.middle,5,0.99),(.senior,5,0.99)]).level == .junior, "sequential Middle prerequisite")
        check(try profile([(.junior,5,0.80),(.middle,5,0.74),(.senior,5,0.99)]).level == .middle, "Senior requires Middle 75")
        check(try profile([(.junior,4,0.99),(.middle,20,0.99)]).level == nil, "insufficient evidence blocks level")
        check(try profile([(.junior,5,0.85),(.middle,4,0.70)]).plus == false, "plus needs five next cases")
        check(try profile([(.junior,5,0.85),(.middle,5,0.62)]).plus, "plus lower boundary")
        check(try profile([(.junior,5,0.85),(.middle,5,0.619)]).plus == false, "plus below boundary")
        check(try profile([(.junior,5,0.85),(.middle,5,0.80),(.senior,5,0.42)]).plus == false, "no plus for weak next score")
        for (n,c) in [(4,TrainerConfidence.insufficient),(5,.low),(9,.low),(10,.medium),(14,.medium),(15,.high)] {
            check(TrainerConfidence(count:n)==c, "confidence boundary \(n)")
        }
        check(try profile([(.junior,5,0.79),(.middle,5,0.99)]).plus == false, "no plus from unmet prerequisite alone")
        let broad = ["people_management","portfolio_management","technical_delivery","release_and_quality","experimentation"]
        let groups: [(TrainerLevel,Int,Double)] = [(.junior,5,0.85),(.middle,5,0.8),(.senior,15,0.75),(.head,5,0.60)]
        check(try profile(groups,domains:broad).level == .head, "Head breadth and threshold")
        check(try profile(groups).level != .head, "technical only cannot confirm Head")
        check(try profile(groups).plus == false, "no plus from unmet breadth alone")
        check(try profile(Array(groups.dropLast()),domains:broad).level != .head, "no Head evidence")
        check(try profile([(.junior,5,0.85),(.middle,5,0.8),(.senior,15,0.75),(.head,4,0.99)],domains:broad).level != .head, "four Head cases insufficient")
        let missingPeople = ["risk_management","portfolio_management","technical_delivery","release_and_quality","experimentation"]
        check(try profile(groups,domains:missingPeople).level != .head, "Head requires people or stakeholders")
        let noBusiness = ["people_management","risk_management","technical_delivery","release_and_quality","experimentation"]
        check(try profile(groups,domains:noBusiness).level != .head, "Head requires business breadth")
        let partial = try f.test(id:"partial",level:.junior,quality:0.8)
        check(near(TrainerScoringEngine.profile(history:f.history([partial])).buckets[.junior]?.score,0.8), "quality 0.8 contributes directly even not isBest")
        check(TrainerScoringEngine.profile(history:f.history([partial],eligibility:.previouslyConfirmed)).eligibleCount==0,"previouslyConfirmed excluded")
        check(TrainerScoringEngine.profile(history:f.history([partial])).eligibleCount==1,"clean first counted")
        var duplicates=f.history([partial]); duplicates.results.append(contentsOf:f.history([try f.test(id:"partial",level:.head,quality:0.1)],date:200).results)
        let dedup=TrainerScoringEngine.profile(history:duplicates)
        check(dedup.eligibleCount==1 && near(dedup.buckets[.junior]?.score,0.8),"first eligible per test ID only")
        duplicates.results.reverse()
        check(TrainerScoringEngine.profile(history:duplicates)==dedup,"history array order irrelevant")
        let p1=try f.test(id:"p1",level:.junior,quality:0.8,domain:"release_and_quality",primary:"evidence-before-release")
        let p2=try f.test(id:"p2",level:.junior,quality:0.2,domain:"mobile_delivery",primary:"unknown",secondary:["quality-metrics"])
        let weighted=TrainerScoringEngine.profile(history:f.history([p1,p2]))
        check(near(weighted.domains[.delivery]?.score,0.5) && weighted.domains[.delivery]?.count==2,"domain aggregation")
        check(weighted.domains[.delivery]?.littleData==true,"domain fewer than three")
        check(near(weighted.patterns[.evidence]?.score,0.6),"primary 1 secondary 0.5 weighted average")
        let tags=try f.test(id:"tags",level:.junior,quality:0.2,primary:"evidence-before-release",secondary:["quality-metrics","peeking","forecast","p-value","quality-metrics"])
        let capped=TrainerScoringEngine.profile(history:f.history([p1,tags]))
        check(near(capped.patterns[.evidence]?.score,0.5) && capped.patterns[.evidence]?.count==2,"aliases do not amplify case weight or count")
        let context=try f.test(id:"context",level:.junior,quality:1,primary:"context-sensitivity")
        check(TrainerScoringEngine.profile(history:f.history([context])).patterns[.context]==nil,"no fake context sensitivity score")
        let oldHistory=f.history([p1]); let oldProfile=TrainerScoringEngine.profile(history:oldHistory)
        _ = try f.test(id:p1.id,level:.head,quality:0.1,domain:"people_management",primary:"contract-volatility")
        check(TrainerScoringEngine.profile(history:oldHistory)==oldProfile && oldProfile.domains[.delivery]?.count==1 && oldProfile.patterns[.evidence]?.count==1,"snapshot level domain and pattern independent of new bank")
        check(oldProfile.scoringModelVersion==1,"scoring model version 1")
        for c in bank.cases {
            check(TrainerScoringMapping.domain(c.domain) != nil,"domain mapped \(c.domain)")
            check(([c.primaryPattern]+c.secondaryPatterns).allSatisfy { TrainerScoringMapping.pattern($0) != nil },"patterns mapped \(c.id)")
        }
        check(TrainerScoringMapping.pattern("interest-based-negotiation") == .stakeholders, "interest-based-negotiation maps to Stakeholder maturity")
        check(TrainerScoringMapping.pattern("negotiation-batna") == .stakeholders, "negotiation-batna maps to Stakeholder maturity")
        check(TrainerScoringMapping.pattern("unknown-pattern-code") == nil, "unknown pattern remains unmapped")
        check(TrainerScoringMapping.pattern("NEGOTIATION-BATNA") == nil, "pattern vocabulary remains exact")
        let unknown = try f.test(id: "unknown-only", level: .junior, quality: 0.8, primary: "unknown-pattern-code")
        let unknownProfile = TrainerScoringEngine.profile(history: f.history([unknown]))
        check(unknownProfile.patterns.isEmpty && unknownProfile.eligibleCount == 1, "unknown pattern adds no category and does not change level evidence")
        let rawDomains=TrainerScoringMapping.domains.values.flatMap {$0},rawPatterns=TrainerScoringMapping.patterns.values.flatMap {$0}
        check(Set(rawDomains).count==rawDomains.count && Set(rawPatterns).count==rawPatterns.count,"mapping unambiguous")
        let folder=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at:folder) }
        let store=TrainerStore(url:folder.appendingPathComponent("state.json"))
        let before=TrainerScoringEngine.profile(history:store.diagnosticHistory)
        check(store.start(cases:[partial]),"training test starts");store.select(partial.options[0].id);store.confirm()
        check(TrainerScoringEngine.profile(history:store.diagnosticHistory)==before,"training and review do not affect profile")
        let fixtureFolder = folder.appendingPathComponent("fixtures")
        try f.writeStates(to: fixtureFolder)
        let populatedURL = fixtureFolder.appendingPathComponent("middle.json")
        let populated = TrainerStore(url: populatedURL)
        let stableProfile = TrainerScoringEngine.profile(history: populated.diagnosticHistory)
        check(stableProfile.level == .middle, "persisted history produces Middle")
        check(populated.start(cases: [partial]), "training alongside diagnostics starts")
        populated.select(partial.options[0].id); populated.confirm(); populated.next()
        check(populated.start(cases: [partial], session: TrainerSession(kind: .mistakes, title: "Ошибки"), replacing: true), "mistakes alongside diagnostics starts")
        populated.select(partial.options[1].id); populated.confirm(); populated.next()
        check(TrainerScoringEngine.profile(history: populated.diagnosticHistory) == stableProfile, "training and mistakes preserve existing profile")
        check(populated.startDiagnostic(bank: bank, count: 10), "unfinished diagnostic starts")
        let diagnosticCase = populated.diagnostic!.cases[0]
        populated.selectDiagnostic(diagnosticCase.options[0].id, testID: diagnosticCase.id)
        check(populated.confirmDiagnostic(testID: diagnosticCase.id), "unfinished diagnostic answer saved")
        check(TrainerScoringEngine.profile(history: populated.diagnosticHistory) == stableProfile, "unfinished diagnostic excluded")
        let restored = TrainerStore(url: populatedURL)
        check(TrainerScoringEngine.profile(history: restored.diagnosticHistory) == stableProfile, "profile reproducible after restart")
        check(restored.resetProgress(), "full reset succeeds")
        check(TrainerScoringEngine.profile(history: restored.diagnosticHistory).eligibleCount == 0, "full reset clears derived profile")
        check(TrainerScoringEngine.profile(history: TrainerStore(url: populatedURL).diagnosticHistory).eligibleCount == 0, "profile remains empty after reset and restart")
        if CommandLine.arguments.count>2 { try f.writeStates(to:URL(fileURLWithPath:CommandLine.arguments[2])) }
    }
}
