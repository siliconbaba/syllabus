import Foundation
@main struct RuntimeProbe {
 static func main() {
  var output: [String: Any] = [:]
  do {
   if CommandLine.arguments.count > 1 {
    let bank = try TrainerBank.load(url: URL(fileURLWithPath: CommandLine.arguments[1]))
    let unknown = bank.cases.flatMap { c -> [String] in
     var result: [String] = []
     if TrainerScoringMapping.domain(c.domain) == nil { result.append("\(c.id): domain \(c.domain)") }
     for p in [c.primaryPattern] + c.secondaryPatterns where TrainerScoringMapping.pattern(p) == nil { result.append("\(c.id): pattern \(p)") }
     return result
    }
    output = ["schema": "PASS", "runtime": unknown.isEmpty ? "PASS" : "FAIL", "issues": unknown]
   } else {
    output = ["domains": Dictionary(uniqueKeysWithValues: TrainerScoringMapping.domains.flatMap { key, codes in codes.map { ($0, key.rawValue) } }), "patterns": Dictionary(uniqueKeysWithValues: TrainerScoringMapping.patterns.flatMap { key, codes in codes.map { ($0, key.rawValue) } })]
   }
  } catch { output = ["schema": "FAIL", "runtime": "NOT_RUN", "issues": [String(describing: error)]] }
  let data = try! JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
  print(String(data: data, encoding: .utf8)!)
 }
}
