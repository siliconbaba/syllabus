import SwiftUI

@main
struct InteractiveBookApp: App {
    @StateObject private var speechReader = SpeechReaderManager()
    @AppStorage("bookTheme") private var theme = "light"

    init() {
        let saved = UserDefaults.standard.dictionary(forKey: "bookState") as? [String: String]
        UserDefaults.standard.set(saved?["ya-theme"] ?? "light", forKey: "bookTheme")
    }

    var body: some Scene {
        WindowGroup {
            BookView(reader: speechReader)
                .safeAreaInset(edge: .bottom, spacing: 0) {
                    if speechReader.topicID != nil { SpeechControls(reader: speechReader) }
                }
                .preferredColorScheme(theme == "dark" ? .dark : .light)
        }
    }
}
