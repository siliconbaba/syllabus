import Foundation

struct SpeechTopic: Decodable {
    struct Block: Decodable {
        let id: String
        let text: String
        var kind: String? = nil
    }
    let id: String
    let title: String
    let blocks: [Block]
}

struct SpeechFragment: Equatable {
    let blockID: String
    let text: String
    var postDelay: TimeInterval = 0.30
}

/// Only the speech copy is transformed. The textbook DOM is never rewritten.
struct SpeechTextProcessor {
    // Keep pronunciation rules in one place; longest matches win (HTTPS before HTTP).
    static let pronunciations: [String: String] = [
        "API": "эй пи ай", "REST": "рэст", "HTTP": "эйч ти ти пи",
        "HTTPS": "эйч ти ти пи эс", "SQL": "эс кью эль", "CI/CD": "си ай си ди",
        "SLA": "эс эл эй", "SLO": "эс эл оу", "DORA": "дора",
        "Kafka": "кафка", "PostgreSQL": "постгрес", "Kubernetes": "кубернетес",
        "OpenShift": "оупен шифт", "JSON": "джейсон", "XML": "икс эм эль",
        "UI": "ю ай", "UX": "ю икс", "backend": "бэкенд", "frontend": "фронтенд",
        "blue-green": "блю грин", "canary": "канареечный", "go/no-go": "гоу ноу гоу",
        "rollback": "откат"
    ]
    private static let termRegex: NSRegularExpression = {
        let alternatives = pronunciations.keys.sorted { $0.count > $1.count }
            .map(NSRegularExpression.escapedPattern(for:)).joined(separator: "|")
        return try! NSRegularExpression(pattern: "(?<![\\p{L}\\p{N}_])(" + alternatives + ")(?![\\p{L}\\p{N}_])", options: .caseInsensitive)
    }()
    private static let lowerRules = Dictionary(uniqueKeysWithValues: pronunciations.map { ($0.key.lowercased(), $0.value) })

    func normalize(_ text: String) -> String {
        var result = text.replacingOccurrences(of: "(?:https?://|www\\.)[^\\s<>]+", with: "", options: [.regularExpression, .caseInsensitive])
        // Plain URL labels are also common in the references section.
        result = result.replacingOccurrences(of: "(?i)\\b[a-z0-9-]+(?:\\.[a-z0-9-]+)*\\.(?:ru|com|org|net|io|dev)(?:/[^\\s<>]*)?", with: "", options: .regularExpression)
        let source = result as NSString
        for match in Self.termRegex.matches(in: result, range: NSRange(location: 0, length: source.length)).reversed() {
            let key = source.substring(with: match.range).lowercased()
            if let value = Self.lowerRules[key], let range = Range(match.range, in: result) {
                result.replaceSubrange(range, with: value)
            }
        }
        return result.replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    func fragments(from topic: SpeechTopic, systemNormalization: Bool = true) -> [SpeechFragment] {
        topic.blocks.flatMap { block in
            let pieces = split(systemNormalization ? normalize(block.text) : block.text, limit: systemNormalization ? 1200 : 600)
            return pieces.enumerated().map { index, text in
                let endDelay: TimeInterval
                switch block.kind {
                case "heading": endDelay = 0.45
                case "list": endDelay = 0.20
                default: endDelay = 0.30
                }
                return SpeechFragment(blockID: block.id, text: text,
                                      postDelay: index == pieces.count - 1 ? endDelay : 0.10)
            }
        }
    }

    /// Natural sentence boundaries first. Only pathological sentences need the safety cap.
    func split(_ text: String, limit: Int = 1200) -> [String] {
        guard limit > 0 else { return [] }
        var sentences: [String] = []
        text.enumerateSubstrings(in: text.startIndex..<text.endIndex, options: .bySentences) { sentence, _, _, _ in
            if let sentence = sentence { sentences.append(sentence) }
        }
        if sentences.isEmpty { sentences = [text] }
        return sentences.flatMap { sentence -> [String] in
            var remaining = sentence.trimmingCharacters(in: .whitespacesAndNewlines)
            var chunks: [String] = []
            while remaining.count > limit {
                let prefix = remaining.prefix(limit)
                let boundary = prefix.lastIndex(where: { $0.isWhitespace }) ?? prefix.endIndex
                let end = boundary == remaining.startIndex ? prefix.endIndex : boundary
                chunks.append(String(remaining[..<end]).trimmingCharacters(in: .whitespacesAndNewlines))
                remaining = String(remaining[end...]).trimmingCharacters(in: .whitespacesAndNewlines)
            }
            if !remaining.isEmpty { chunks.append(remaining) }
            return chunks
        }
    }
}
