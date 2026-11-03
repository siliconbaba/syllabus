import Foundation
@main struct ValidateBatch {
 static func main() throws {
  let bank = try TrainerBank.load(url: URL(fileURLWithPath: CommandLine.arguments[1]))
  precondition(bank.cases.count == 25)
  for c in bank.cases {
   precondition(TrainerScoringMapping.domain(c.domain) != nil)
   precondition(TrainerScoringMapping.pattern(c.primaryPattern) != nil)
   precondition(c.secondaryPatterns.allSatisfy { TrainerScoringMapping.pattern($0) != nil })
   precondition(c.options.filter { $0.decisionQuality == .number(1) }.count == 1)
   precondition(c.options.allSatisfy { $0.isBest == ($0.decisionQuality == .number(1)) })
  }
  print("PASS: TrainerBank.load strict production schema 2.0; 25 cases; vocabulary; one quality=1 per case")
 }
}
