import Foundation

/// Opt-in product layer. Does not modify SileroPreprocessor or visible book text.
final class TechnicalSpeechNormalizer {
    private let terms:NSRegularExpression
    private let folded:[String:String]
    init(){
        let keys=TechnicalLexicon.entries.keys.sorted{$0.count == $1.count ? $0<$1:$0.count>$1.count}
        terms=try! NSRegularExpression(pattern:"(?<![\\p{L}\\p{N}_])(?:"+keys.map(NSRegularExpression.escapedPattern(for:)).joined(separator:"|")+")(?![\\p{L}\\p{N}_])",options:.caseInsensitive)
        folded=Dictionary(uniqueKeysWithValues:TechnicalLexicon.entries.map{($0.key.lowercased(),$0.value)})
    }
    private func replace(_ pattern:String,_ text:String,_ transform:([String])->String)->String {
        let re=try! NSRegularExpression(pattern:pattern);let source=text as NSString;var result=text
        for m in re.matches(in:text,range:NSRange(location:0,length:source.length)).reversed(){
            let groups=(0..<m.numberOfRanges).map{m.range(at:$0).location == NSNotFound ? "":source.substring(with:m.range(at:$0))}
            result.replaceSubrange(Range(m.range,in:result)!,with:transform(groups))
        };return result
    }
    // Unknown short ALL CAPS tokens are abbreviations; ordinary/camelCase words are not.
    static func latinWord(_ token:String)->String {
        if token.count <= 5 && token == token.uppercased() && (token.count <= 3 || token.range(of:"[AEIOUY]",options:.regularExpression) == nil) {
            return token.lowercased().map { TechnicalLexicon.letters[String($0)]! }.joined(separator:" ")
        }
        let chunks = token.replacingOccurrences(of:"([A-Z])([A-Z][a-z])",with:"$1 $2",options:.regularExpression).replacingOccurrences(of: "([a-z])([A-Z])", with: "$1 $2", options:.regularExpression).components(separatedBy:" ")
        return chunks.map { chunk in
            if let known = TechnicalLexicon.entries.first(where: { $0.key.lowercased() == chunk.lowercased() }) { return known.value }
            if chunks.count > 1 { return latinWord(chunk) }
            var value = chunk.lowercased()
            let rules:[(String,String)] = [("tion","шн"),("sion","жн"),("ough","оу"),("igh","ай"),("tch","ч"),("sh","ш"),("ch","ч"),("ph","ф"),("th","т"),("qu","кв"),("ee","и"),("ea","и"),("oo","у"),("ou","ау"),("ow","оу"),("ai","эй"),("ay","эй"),("ck","к"),("ng","нг")]
            for (from,to) in rules { value=value.replacingOccurrences(of:from,with:to) }
            let letters:[Character:String] = ["a":"а","b":"б","c":"к","d":"д","e":"е","f":"ф","g":"г","h":"х","i":"и","j":"дж","k":"к","l":"л","m":"м","n":"н","o":"о","p":"п","q":"к","r":"р","s":"с","t":"т","u":"у","v":"в","w":"в","x":"кс","y":"и","z":"з"]
            return value.map { letters[$0] ?? String($0) }.joined()
        }.joined(separator:" ")
    }
    func normalize(_ source:String)throws->String {
        var text=replace(#"(\d)(?=(?:KB|MB|GB|TB|RPS|TPS|CPU)\b)"#,source){$0[1]+" "}
        // Versions precede decimals; lexical composites precede slash/digit rules.
        text=replace(#"(?i)\b(версия|версии)\s+v(\d+(?:\.\d+)*)\b"#,text){$0[1]+" "+TechnicalNumbers.version($0[2])}
        text=replace(#"(?i)\bv(\d+(?:\.\d+)*)\b"#,text){"версия "+TechnicalNumbers.version($0[1])}
        text=replace(#"(?i)\b(PostgreSQL|Postgres|iOS|Java|Python|Kotlin|Swift|Kubernetes|Docker|версия|версии)\s+(\d+(?:\.\d+)*)\b"#,text){$0[1]+" "+TechnicalNumbers.version($0[2])}
        let ns=text as NSString
        for m in terms.matches(in:text,range:NSRange(location:0,length:ns.length)).reversed(){let token=ns.substring(with:m.range);text.replaceSubrange(Range(m.range,in:text)!,with:TechnicalLexicon.entries[token] ?? folded[token.lowercased()]!)}
        text=replace(#"(?<=\d)\s*[-−]\s*(?=\d)"#,text){_ in " минус "}
        text=replace(#"(?<![\p{L}\p{N}])[-−](?=\d)"#,text){_ in "минус "}
        text=replace(#"(?<![А-Яа-яёЁ])\+|\+(?![А-Яа-яёЁ])"#,text){_ in " плюс "}
        text=replace(#"\b(\d{4})\s+(год|года|году)\b"#,text){TechnicalNumbers.year($0[1],$0[2])}
        text=replace(#"(?i)\b(с|до|от)\s+(\d+(?:[.,]\d+)?)\s*%"#,text){g in
            let decimal=g[2].contains(".") || g[2].contains(",");let n=Int64(g[2]) ?? 0
            return g[1]+" "+TechnicalNumbers.genitive(TechnicalNumbers.number(g[2]))+" "+(decimal || (n%10==1 && n%100 != 11) ? "процента":"процентов")
        }
        text=replace(#"(?<!\d)(\d+(?:[.,]\d+)?)\s*%"#,text){let v=$0[1];return TechnicalNumbers.number(v)+" "+(v.contains(".") || v.contains(",") ? "процента":TechnicalNumbers.form(Int64(v) ?? 0,["процент","процента","процентов"]))}
        // Unit tokens have already acquired Cyrillic spelling from the lexicon.
        let unitForms:[String:([String],Bool,String)] = [
            "килобайт":(["килобайт","килобайта","килобайт"],false,""),"мегабайт":(["мегабайт","мегабайта","мегабайт"],false,""),"гигабайт":(["гигабайт","гигабайта","гигабайт"],false,""),"терабайт":(["терабайт","терабайта","терабайт"],false,""),
            "мс":(["миллисекунда","миллисекунды","миллисекунд"],true,""),"ар пи эс":(["запрос","запроса","запросов"],false," в секунду"),"ти пи эс":(["транзакция","транзакции","транзакций"],true," в секунду"),"си пи ю":(["процессор","процессора","процессоров"],false,"")]
        text=replace(#"(?i)\b(\d+(?:[.,]\d+)?)\s*(килобайт|мегабайт|гигабайт|терабайт|мс|ар пи эс|ти пи эс|си пи ю)\b"#,text){g in let rule=unitForms[g[2].lowercased()]!;let decimal=g[1].contains(".") || g[1].contains(",");return TechnicalNumbers.number(g[1],female:rule.1)+" "+(decimal ? rule.0[1]:TechnicalNumbers.form(Int64(g[1]) ?? 0,rule.0))+rule.2}
        text=replace(#"\b(\d+)\s+(минут[ауы]?|секунд[ауы]?)\b"#,text){TechnicalNumbers.integer($0[1],female:true)+" "+$0[2]}
        text=replace(#"\d+(?:\.\d+){2,}"#,text){TechnicalNumbers.version($0[0])}
        text=replace(#"\d+(?:[.,]\d+)?"#,text){TechnicalNumbers.number($0[0])}
        text=replace(#"[A-Za-z]+"#,text){Self.latinWord($0[0])}
        // Preserve Russian stress markers if supplied; arithmetic '+' becomes a word.
        text=replace(#"(?<![А-Яа-яёЁ])\+|\+(?![А-Яа-яёЁ])"#,text){_ in " плюс "}
        let symbols:[String:String] = ["/":" слэш ","=":" равно ","%":" процент ","&":" и ","@":" собака ","#":" номер ","×":" умножить на ","→":" переходит в ","_":" подчёркивание ","^":" в степени ","*":" умножить на ","−":" минус ","—":"–","‑":"-","\"":"","«":"","»":"","“":"","”":"","(":", ",")":", ","[":", ","]":", "]
        for (key,value) in symbols{text=text.replacingOccurrences(of:key,with:value)}
        text=trim(sub(#"\s+"#,text," "));text=sub(#"\s+([.,!?;:])"#,text,"$1")
        // Fail explicitly for unhandled significant glyphs rather than losing them in Silero.
        let unsupported=matches(#"[^А-Яа-яёЁ!+,\-.:;?–… ]"#,text)
        guard unsupported.isEmpty else{throw ResearchError("Technical normalizer: unsupported symbols \(Set(unsupported).sorted())")}
        return text
    }
}
