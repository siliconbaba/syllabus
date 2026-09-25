import Foundation
struct ResearchError:Error { let description:String;init(_ s:String){description=s} }
let rows=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))) as! [[String:Any]]
let normalizer=TechnicalSpeechNormalizer();var failed=0
for row in rows {
 do {let actual=try normalizer.normalize(row["source"] as! String);if actual != row["expected"] as! String{failed+=1;print(row["id"]!,"\nexpected:",row["expected"]!,"\nactual:  ",actual)}}
 catch{failed+=1;print(row["id"]!,error)}
}
print("Text tests: \(rows.count-failed)/\(rows.count)");exit(failed == 0 ? 0:1)
