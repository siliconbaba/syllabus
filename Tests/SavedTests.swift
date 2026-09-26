import Foundation
@main struct SavedTests {
 @MainActor static func main() {
  func check(_ ok: Bool, _ label: String) { guard ok else { fatalError(label) }; print("PASS: " + label) }
  let defaults = UserDefaults(suiteName: "SavedTests." + UUID().uuidString)!
  var p: [String: Any] = ["text":"  API  вернул\n ошибку. ", "topicID":"t-10-1", "topicTitle":"Архитектура", "anchor":"t-10-1-saved-3", "sectionTitle":"Техническая грамотность"]
  let store = SavedExcerptStore(defaults: defaults)
  check(store.save(p) == "Сохранено", "save excerpt")
  check(store.excerpts[0].text == "API вернул ошибку.", "visual whitespace normalization without TTS")
  check(store.save(p) == "Уже сохранено" && store.excerpts.count == 1, "duplicate prevention")
  check(SavedExcerptStore(defaults: defaults).excerpts == store.excerpts, "persistence and navigation metadata")
  p["topicID"] = "t-10-2"; p["anchor"] = "t-10-2-saved-3"
  check(store.save(p) == "Сохранено" && store.excerpts.count == 2, "same text different topics")
  p["text"] = " \n "; check(SavedExcerpt.from(payload:p) == nil, "empty selection")
  p["text"] = "текст"; p["anchor"] = 42; check(SavedExcerpt.from(payload:p) == nil, "invalid payload types")
  p["anchor"] = "foreign-anchor"; check(SavedExcerpt.from(payload:p) == nil, "invalid anchor")
  p["anchor"] = nil; p["topicID"] = "https://example.org"; check(SavedExcerpt.from(payload:p) == nil, "invalid topic")
  store.delete(ids: [store.excerpts[0].id]); check(SavedExcerptStore(defaults:defaults).excerpts.count == 1, "delete persists")
  defaults.set(Data("broken".utf8), forKey:"saved.excerpts")
  let broken = SavedExcerptStore(defaults:defaults)
  check(broken.excerpts.isEmpty && broken.message != nil && defaults.data(forKey:"saved.excerpts.recovery") != nil, "corrupted persistence recoverable")
 }
}
