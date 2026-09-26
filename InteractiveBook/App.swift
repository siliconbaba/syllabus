import SwiftUI

@main
struct InteractiveBookApp: App {
    @StateObject private var speechReader = SpeechReaderManager()
    @StateObject private var excerpts = SavedExcerptStore()
    @AppStorage("bookTheme") private var theme = "light"

    init() {
        let saved = UserDefaults.standard.dictionary(forKey: "bookState") as? [String: String]
        UserDefaults.standard.set(saved?["ya-theme"] ?? "light", forKey: "bookTheme")
    }

    var body: some Scene {
        WindowGroup {
            BookView(reader: speechReader, excerpts: excerpts)
                .sheet(isPresented: $excerpts.isPresented) { SavedExcerptsView(store: excerpts) }
                .alert("Сохранённое", isPresented: Binding(get: { excerpts.message != nil }, set: { if !$0 { excerpts.message = nil } })) { Button("Понятно") { excerpts.message = nil } } message: { Text(excerpts.message ?? "") }
                .safeAreaInset(edge: .bottom, spacing: 0) {
                    if speechReader.topicID != nil { SpeechControls(reader: speechReader) }
                }
                .preferredColorScheme(theme == "dark" ? .dark : .light)
        }
    }
}
