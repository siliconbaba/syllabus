import Foundation
@main struct SnapshotRegression {
 @MainActor static func main() throws {
  let old = try JSONDecoder().decode(TrainerBank.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
  let current = try TrainerBank.load(url: URL(fileURLWithPath: CommandLine.arguments[2]))
  let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
  defer { try? FileManager.default.removeItem(at: dir) }
  let url = dir.appendingPathComponent("state.json")
  let store = TrainerStore(url: url)
  precondition(store.startDiagnostic(bank: old, count: nil))
  for c in store.diagnostic!.cases {
   store.selectDiagnostic(c.options.first { $0.isBest }!.id, testID: c.id)
   precondition(store.confirmDiagnostic(testID: c.id))
  }
  precondition(store.start(cases: old.cases))
  store.select(old.cases[0].options[0].id); store.confirm()
  let attempt = store.attempt!, history = store.diagnosticHistory
  let profile = TrainerScoringEngine.profile(history: history)
  let bytes = try Data(contentsOf: url)
  let reopened = TrainerStore(url: url)
  precondition(reopened.attempt == attempt && reopened.attempt?.phase == .review)
  precondition(reopened.diagnosticHistory == history && TrainerScoringEngine.profile(history: reopened.diagnosticHistory) == profile)
  let reopenedBytes = try Data(contentsOf: url)
  precondition(reopenedBytes == bytes)
  precondition(reopened.start(cases: current.cases, replacing: true))
  precondition(reopened.attempt?.cases.count == 75)
  precondition(TrainerScoringEngine.profile(history: TrainerStore(url: url).diagnosticHistory) == profile)
  let fresh = TrainerStore(url: dir.appendingPathComponent("fresh.json"))
  precondition(fresh.startDiagnostic(bank: current, count: nil))
  precondition(fresh.diagnostic?.cases.count == 51 && fresh.diagnostic!.cases.allSatisfy { $0.scenarioFamilyId == nil && $0.assessmentEligible })
  print("PASS: exact pre-import schema-2 bank snapshot: Continue/review, immutable history/profile, new 75-case training, fresh 51 standalone diagnostic")
 }
}
