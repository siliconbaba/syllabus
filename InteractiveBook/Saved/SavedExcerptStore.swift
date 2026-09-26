import Foundation
import Combine

struct SavedExcerpt: Codable, Identifiable, Equatable {
    let id: UUID
    let text: String
    let topicID: String
    let topicTitle: String
    let sectionTitle: String?
    let anchor: String?
    let createdAt: Date

    static func normalized(_ value: String) -> String {
        value.split(whereSeparator: { $0.isWhitespace }).joined(separator: " ")
    }
    static func from(payload: [String: Any]) -> SavedExcerpt? {
        guard let raw = payload["text"] as? String, raw.count <= 20_000,
              let topic = payload["topicID"] as? String,
              topic.range(of: "^t-[0-9]+-[0-9]+$", options: .regularExpression) != nil,
              let title = payload["topicTitle"] as? String, !normalized(title).isEmpty, title.count <= 500 else { return nil }
        let text = normalized(raw)
        guard !text.isEmpty else { return nil }
        let anchor = payload["anchor"] as? String
        if let anchor = anchor, (!anchor.hasPrefix(topic + "-saved-") && !anchor.hasPrefix(topic + "-block-")) || anchor.count > 200 { return nil }
        if payload["anchor"] != nil && anchor == nil { return nil }
        let section = payload["sectionTitle"] as? String
        if payload["sectionTitle"] != nil && section == nil { return nil }
        guard (section?.count ?? 0) <= 500 else { return nil }
        return SavedExcerpt(id: UUID(), text: text, topicID: topic, topicTitle: normalized(title), sectionTitle: section.map(normalized), anchor: anchor, createdAt: Date())
    }
}

@MainActor final class SavedExcerptStore: ObservableObject {
    @Published private(set) var excerpts: [SavedExcerpt] = []
    @Published var isPresented = false
    @Published var message: String?
    var openSource: ((SavedExcerpt) -> Void)?
    private let defaults: UserDefaults
    private let key = "saved.excerpts"
    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let data = defaults.data(forKey: key) {
            if let decoded = try? JSONDecoder().decode([SavedExcerpt].self, from: data) { excerpts = decoded }
            else { message = "Не удалось прочитать сохранённые фрагменты. Исходные данные сохранены для восстановления."; defaults.set(data, forKey: key + ".recovery") }
        }
    }
    @discardableResult func save(_ payload: [String: Any]) -> String {
        guard let item = SavedExcerpt.from(payload: payload) else { return "Не удалось сохранить выделение." }
        if excerpts.contains(where: { $0.topicID == item.topicID && $0.anchor == item.anchor && SavedExcerpt.normalized($0.text) == item.text }) { return "Уже сохранено" }
        let updated = [item] + excerpts
        guard let data = try? JSONEncoder().encode(updated) else { return "Не удалось сохранить выделение." }
        defaults.set(data, forKey: key)
        excerpts = updated
        #if DEBUG
        NSLog("Saved excerpts: persisted and published count=%d", excerpts.count)
        #endif
        return "Сохранено"
    }
    func delete(ids: Set<UUID>) { excerpts.removeAll { ids.contains($0.id) }; persist() }
    private func persist() {
        guard let data = try? JSONEncoder().encode(excerpts) else { message = "Не удалось сохранить коллекцию."; return }
        defaults.set(data, forKey: key)
    }
}
