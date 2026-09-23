import SwiftUI
import WebKit

struct BookView: UIViewRepresentable {
    let reader: SpeechReaderManager
    func makeCoordinator() -> Coordinator { Coordinator(reader: reader) }

    func makeUIView(context: Context) -> WKWebView {
        let controller = WKUserContentController()
        controller.add(context.coordinator, name: "setting")
        controller.add(context.coordinator, name: "speech")
        let saved = UserDefaults.standard.dictionary(forKey: "bookState") as? [String: String] ?? [:]
        let encoded = (try? JSONSerialization.data(withJSONObject: saved)) ?? Data("{}".utf8)
        let json = String(data: encoded, encoding: .utf8) ?? "{}"
        controller.addUserScript(WKUserScript(
            source: "window.__nativeState = \(json);",
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))

        let config = WKWebViewConfiguration()
        config.defaultWebpagePreferences.allowsContentJavaScript = true
        config.websiteDataStore = .default()
        config.userContentController = controller
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = true
        webView.backgroundColor = .systemBackground
        webView.scrollView.bounces = false
        webView.scrollView.alwaysBounceHorizontal = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.navigationDelegate = context.coordinator
        context.coordinator.webView = webView
        context.coordinator.connectReader()

        if let folder = Bundle.main.url(forResource: "WebContent", withExtension: nil) {
            let index = folder.appendingPathComponent("index.html")
            context.coordinator.contentFolder = folder
            webView.loadFileURL(index, allowingReadAccessTo: folder)
        } else {
            webView.loadHTMLString("<h1>WebContent/index.html отсутствует в сборке</h1>", baseURL: nil)
        }
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) {
        coordinator.reader.reset()
        coordinator.reader.onHighlight = nil
        coordinator.reader.onRequestTopic = nil
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: "setting")
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: "speech")
        uiView.navigationDelegate = nil
    }

    @MainActor
    final class Coordinator: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
        var contentFolder: URL?
        weak var webView: WKWebView?

        let reader: SpeechReaderManager

        init(reader: SpeechReaderManager) {
            self.reader = reader
            super.init()
            NotificationCenter.default.addObserver(self, selector: #selector(saveReadingPosition),
                name: UIApplication.willResignActiveNotification, object: nil)
        }

        @objc private func saveReadingPosition() {
            webView?.evaluateJavaScript("window.bookSavePosition && window.bookSavePosition()", completionHandler: nil)
        }

        deinit { NotificationCenter.default.removeObserver(self) }

        func userContentController(_ userContentController: WKUserContentController,
                                   didReceive message: WKScriptMessage) {
            guard message.frameInfo.isMainFrame,
                  let url = webView?.url, url.isFileURL,
                  let folder = contentFolder,
                  url.standardizedFileURL.path.hasPrefix(folder.standardizedFileURL.path + "/") else { return }
            if message.name == "speech", let payload = message.body as? [String: Any] {
                let id = payload["id"] as? String ?? ""
                guard id.count < 150 else { return }
                if payload["action"] as? String == "listen", !id.isEmpty {
                    requestTopic(id, title: String((payload["title"] as? String ?? "Аудиочтение").prefix(500)))
                } else if payload["action"] as? String == "context" {
                    reader.contextChanged(to: id.isEmpty ? nil : id, invalidate: payload["invalidate"] as? Bool ?? false)
                }
                return
            }
            guard message.name == "setting",
                  let payload = message.body as? [String: String],
                  let key = payload["key"], let value = payload["value"],
                  key.hasPrefix("ya-"), key.count <= 150, value.count <= 1000 else { return }
            var state = UserDefaults.standard.dictionary(forKey: "bookState") as? [String: String] ?? [:]
            guard state.count < 3000 || state[key] != nil else { return }
            if key == "ya-theme" { UserDefaults.standard.set(value, forKey: "bookTheme") }
            state[key] = value
            UserDefaults.standard.set(state, forKey: "bookState")
        }

        func connectReader() {
            reader.onRequestTopic = { [weak self] id in self?.requestTopic(id, title: self?.reader.title ?? "Аудиочтение") }
            reader.onHighlight = { [weak self] id, block in
                guard UIApplication.shared.applicationState == .active else { return }
                let arguments: [Any] = [id, block as Any? ?? NSNull()]
                guard let data = try? JSONSerialization.data(withJSONObject: arguments),
                      let json = String(data: data, encoding: .utf8) else { return }
                self?.webView?.evaluateJavaScript("window.bookAudio && window.bookAudio.highlight(...\(json))", completionHandler: nil)
            }
        }

        private func requestTopic(_ id: String, title: String) {
            guard let webView = webView,
                  let data = try? JSONSerialization.data(withJSONObject: [id]),
                  let argument = String(data: data, encoding: .utf8) else { return }
            let token = reader.beginLoading(id: id, title: title)
            webView.evaluateJavaScript("window.bookAudio && window.bookAudio.extractTopic(\(argument)[0])") { [weak self] value, error in
                guard let self = self else { return }
                guard error == nil, let value = value as? [String: Any],
                      let data = try? JSONSerialization.data(withJSONObject: value), data.count <= 1_000_000,
                      let topic = try? JSONDecoder().decode(SpeechTopic.self, from: data),
                      topic.id == id, topic.blocks.count <= 5000,
                      topic.blocks.allSatisfy({ $0.id.count < 200 && $0.text.count < 50_000 }) else {
                    self.reader.failLoading(request: token); return
                }
                self.reader.finishLoading(topic, request: token)
            }
        }

        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }
            if url.isFileURL, let folder = contentFolder,
               url.standardizedFileURL.path.hasPrefix(folder.standardizedFileURL.path + "/") {
                decisionHandler(.allow)
            } else if ["https", "http"].contains(url.scheme?.lowercased() ?? "") {
                UIApplication.shared.open(url)
                decisionHandler(.cancel)
            } else {
                decisionHandler(.cancel)
            }
        }
    }
}
