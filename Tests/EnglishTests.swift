import Foundation
struct ResearchError:Error {init(_ text:String){}}
@main struct EnglishTests {
 struct Row:Decodable {let source:String;let expected:String}
 static func main() throws {
  let normalizer=TechnicalSpeechNormalizer()
  let rows=try JSONDecoder().decode([Row].self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
  for row in rows {let actual=try normalizer.normalize(row.source);guard actual==row.expected else{fatalError("\(row.source): \(actual) != \(row.expected)")}}
  for (term,pronunciation) in TechnicalLexicon.entries {guard try normalizer.normalize(term)==normalizer.normalize(pronunciation) else{fatalError("Dictionary changed: \(term)")}}
  print("PASS: \(rows.count) English regressions and all dictionary entries")
 }
}
