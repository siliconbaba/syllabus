import Foundation

// Python str indexing is by code point, not Swift extended grapheme cluster.
func scalars(_ s: String) -> [String] { s.unicodeScalars.map(String.init) }
func trim(_ s: String) -> String { s.trimmingCharacters(in: .whitespacesAndNewlines) }
func sub(_ pattern: String, _ s: String, _ replacement: String) -> String {
    let re = try! NSRegularExpression(pattern: pattern)
    return re.stringByReplacingMatches(in: s, range: NSRange(s.startIndex..., in:s), withTemplate: replacement)
}
func matches(_ pattern: String, _ s: String) -> [String] {
    let re = try! NSRegularExpression(pattern: pattern)
    return re.matches(in:s,range:NSRange(s.startIndex...,in:s)).map { String(s[Range($0.range,in:s)!]) }
}
func splitRE(_ pattern: String, _ s: String, capture: Bool = false) -> [String] {
    let re=try! NSRegularExpression(pattern:pattern);let ns=s as NSString;var result:[String]=[];var start=0
    for match in re.matches(in:s,range:NSRange(location:0,length:ns.length)) {
        result.append(ns.substring(with:NSRange(location:start,length:match.range.location-start)))
        if capture { result.append(ns.substring(with:match.range)) }
        start=match.range.location+match.range.length
    }
    result.append(ns.substring(from:start));return result
}
final class SileroData {
    let values:[String:Any]
    let symbols:[String:Int], vocab:[String:Int], ngrams:[String:Int], exceptions:[String:[Int]], homodict:[String:[String]]
    init(root:URL) throws {
        values=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("data.json"))) as! [String:Any]
        symbols=values["symbol_to_id"] as! [String:Int];vocab=values["vocab"] as! [String:Int];ngrams=values["ngrams"] as! [String:Int]
        exceptions=values["exceptions"] as! [String:[Int]];homodict=values["homodict"] as! [String:[String]]
    }
}
struct SileroNormalizer {
    let data:SileroData
    func normalize(_ raw:String) throws -> String {
        guard !raw.contains("*") && !raw.contains("^") else { throw ResearchError("Focus is outside this plain-text baseline") }
        let text=trim(raw);let chars=scalars(text);var lines=""
        for (i,c) in chars.enumerated() { lines += c == "\n" ? (i>0 && ",;:.!?".contains(chars[i-1]) ? " " : ". ") : c }
        var s=lines.lowercased().replacingOccurrences(of:"—",with:"–").replacingOccurrences(of:"‑",with:"-")
        let allowed=Set(scalars(String((data.values["symbols"] as! String).dropFirst(3))))
        s=scalars(s).filter { allowed.contains($0) }.joined()
        s=trim(sub(#"\s+"#,s," "))
        guard !sub(#"[^а-я\-]"#,s,"").isEmpty else { throw ResearchError("Original Silero rejects text without supported letters") }
        return s
    }
}
struct SileroQuestionClassifier {
    let data:SileroData
    let typeMap=["st":0,"wh_q":1,"general_q":2,"alternative_q":3,"tag_q":4,"exclam":5]
    func outer(_ text:String)->String {
        var s=trim(text)
        while let c=s.first, "\"«“„".contains(c) { s=trim(String(s.dropFirst())) }
        while let c=s.last, "\"»”’".contains(c) { s=trim(String(s.dropLast())) }
        return s
    }
    func sentence(_ text:String)->String {
        let clean=outer(text);var tail=clean
        if tail.hasSuffix("?!") || tail.hasSuffix("?.."){ while let c=tail.last,".!".contains(c){tail.removeLast()} }
        else if tail.hasSuffix("?..."){while let c=tail.last,".!".contains(c){tail.removeLast()}}
        if tail.hasSuffix("?") {
            let q=trim(sub(#"\s+"#,outer(tail).replacingOccurrences(of:"+",with:"").replacingOccurrences(of:"ё",with:"е").replacingOccurrences(of:"Ё",with:"Е")," "))
            for p in data.values["TAG_PATTERNS"] as! [String] { if !matches("(?i)"+p,q).isEmpty{return "tag_q"} }
            let fillers=Set(data.values["LEADING_FILLERS"] as! [String]),wh=Set(data.values["WH_FORMS"] as! [String])
            let content=matches("[а-яёa-z]+",q.lowercased()).prefix(8).filter{!fillers.contains($0)}.prefix(4)
            if content.contains(where:{wh.contains($0)}) {return "wh_q"}
            if !matches(#"(?i)\bили\b"#,q).isEmpty{return "alternative_q"}
            return "general_q"
        }
        return clean.hasSuffix("!") ? "exclam" : "st"
    }
    func classify(_ text:String)->String {
        if trim(text).isEmpty{return "st"}
        return splitRE(#"(?<=[.!?])\s+"#,trim(text)).map(trim).filter{!$0.isEmpty}.map(sentence).joined(separator:"|")
    }
    func typeIDs(_ text:String,_ classification:String,_ length:Int)->[Int64] {
        let types=classification.components(separatedBy:"|");let sents=splitRE(#"(?<=[.!?])\s+"#,trim(text));var per:[Int64]=[]
        for (i,s) in sents.enumerated(){let tid=Int64(typeMap[types[min(i,types.count-1)]] ?? 0);per += Array(repeating:tid,count:scalars(s).count);if i<sents.count-1{per.append(tid)}}
        let defaultID=Int64(typeMap[types[0]] ?? 0)
        return Array(([defaultID]+per+Array(repeating:defaultID,count:length)).prefix(length))
    }
}
struct SileroTokenizer {
    let data:SileroData
    func characters(_ text:String)throws->[Int64] {
        try scalars(text).map{guard let id=data.symbols[$0] else{throw ResearchError("Unknown TTS character \($0)")};return Int64(id)}
    }
    func sequence(_ text:String)throws->[Int64] {try characters("|"+text+"~")}
    func wordpieces(_ text:String)->[String] {
        // Normalization already excludes Chinese/control characters. Markers are ASCII.
        let never=Set(data.values["never_split"] as! [String]);var basic:[String]=[]
        for token in text.split(whereSeparator:{$0.isWhitespace}).map(String.init) {
            if never.contains(token){basic.append(token);continue}
            var word=""
            for scalar in token.unicodeScalars {
                let cp=scalar.value;let ascii=(33...47).contains(cp)||(58...64).contains(cp)||(91...96).contains(cp)||(123...126).contains(cp)
                if ascii || CharacterSet.punctuationCharacters.contains(scalar){if !word.isEmpty{basic.append(word);word=""};basic.append(String(scalar))}else{word+=String(scalar)}
            }
            if !word.isEmpty{basic.append(word)}
        }
        var output:[String]=[]
        for token in basic {
            let chars=scalars(token);if chars.count>100{output.append("[UNK]");continue}
            var start=0;var pieces:[String]=[];var bad=false
            while start<chars.count {
                var end=chars.count;var found:String?=nil
                while start<end {let s=(start>0 ? "##" : "")+chars[start..<end].joined();if data.vocab[s] != nil{found=s;break};end-=1}
                guard let piece=found else{bad=true;break};pieces.append(piece);start=end
            }
            output += bad ? ["[UNK]"] : pieces
        }
        return output
    }
    func bertIDs(_ pieces:[String])->[Int64] {(["[CLS]"]+pieces+["[SEP]"]).map{Int64(data.vocab[$0] ?? data.vocab["[UNK]"]!)}}
}
