import Foundation
struct ResearchError:Error {init(_ text:String){}}
@main struct EnglishTests {
 struct Row:Decodable {let source:String;let expected:String}
 static func main() throws {
  let normalizer=TechnicalSpeechNormalizer()
  let rows=try JSONDecoder().decode([Row].self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
  for row in rows {let actual=try normalizer.normalize(row.source);guard actual==row.expected else{fatalError("\(row.source): \(actual) != \(row.expected)")}}
  for (term,pronunciation) in TechnicalLexicon.entries {guard try normalizer.normalize(term)==normalizer.normalize(pronunciation) else{fatalError("Dictionary changed: \(term)")}}
  for phones in EnglishPronunciation.dictionary.values {
   for phone in phones.split(separator:" ") {
    let key=String(phone.filter { !$0.isNumber })
    precondition(EnglishPronunciation.phonemeMap[key] != nil, "Unknown phone: " + key)
   }
  }
  precondition(EnglishPronunciation.cyrillic("S K OW1 P") == "скоуп")
  precondition(EnglishPronunciation.cyrillic("S P AY1 K") == "спайк")
  precondition(EnglishPronunciation.cyrillic("K Y UW1") == "кью")
  precondition(EnglishPronunciation.fallback("blape") == "блэйп")
  precondition(EnglishPronunciation.fallback("snoat") == "сноут")
  // Engine separation: shared Apple rules have not inherited Neural pronunciation.
  precondition(SpeechTextProcessor().normalize("scope spike rollback") == "scope spike откат")
  let batch=rows.map(\.source).joined(separator:" ")
  let start=Date()
  for _ in 0..<5 { _ = try normalizer.normalize(batch) }
  print("Normalization: \(batch.count) characters, \(Date().timeIntervalSince(start)/5) seconds per batch")
  print("PASS: \(rows.count) English regressions and all dictionary entries")
 }
}
