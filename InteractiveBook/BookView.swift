import SwiftUI
import WebKit

struct BookView: UIViewRepresentable {
    let reader: SpeechReaderManager
    let excerpts: SavedExcerptStore
    func makeCoordinator() -> Coordinator { Coordinator(reader: reader, excerpts: excerpts) }

    func makeUIView(context: Context) -> WKWebView {
        let controller = WKUserContentController()
        controller.add(context.coordinator, name: "setting")
        controller.add(context.coordinator, name: "speech")
        controller.add(context.coordinator, name: "saved")
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
        coordinator.excerpts.openSource = nil
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: "saved")
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

        let excerpts: SavedExcerptStore

        init(reader: SpeechReaderManager, excerpts: SavedExcerptStore) {
            self.excerpts = excerpts
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
            guard BookMessageTrust.accepts(message, controller: userContentController, webView: webView, folder: contentFolder) else { return }
            if message.name == "saved", let payload = message.body as? [String: Any] {
                if payload["action"] as? String == "open" { excerpts.isPresented = true }
                else if payload["action"] as? String == "listenFrom", let item = SavedExcerpt.from(payload: payload), let block = item.anchor, block.hasPrefix(item.topicID + "-block-") {
                    requestTopic(item.topicID, title: item.topicTitle, startBlockID: block)
                    webView?.callAsyncJavaScript("window.bookSaved.feedback(text, true)", arguments: ["text": "Чтение с выбранного абзаца"], in: nil, in: .page, completionHandler: nil)
                }
                else if payload["action"] as? String == "save" {
                    let result = excerpts.save(payload)
                    webView?.callAsyncJavaScript("window.bookSaved.feedback(text)", arguments: ["text": result], in: nil, in: .page, completionHandler: nil)
                }
                return
            }
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
            excerpts.openSource = { [weak self] item in
                guard let self = self else { return }
                self.reader.stop()
                let value: [String: Any] = ["topicID": item.topicID, "anchor": item.anchor ?? "", "text": item.text]
                self.webView?.callAsyncJavaScript("return await window.bookSaved.openSource(value)", arguments: ["value": value], in: nil, in: .page) { [weak self] result in
                    if case .success(let status) = result, let status = status as? String, status != "missingTopic" { return }
                    self?.excerpts.message = "Исходная тема недоступна в этой версии учебника. Фрагмент остался в сохранённом."
                }
            }
            reader.onRequestTopic = { [weak self] id in self?.requestTopic(id, title: self?.reader.title ?? "Аудиочтение") }
            reader.onHighlight = { [weak self] id, block in
                guard UIApplication.shared.applicationState == .active else { return }
                let arguments: [Any] = [id, block as Any? ?? NSNull()]
                guard let data = try? JSONSerialization.data(withJSONObject: arguments),
                      let json = String(data: data, encoding: .utf8) else { return }
                self?.webView?.evaluateJavaScript("window.bookAudio && window.bookAudio.highlight(...\(json))", completionHandler: nil)
            }
        }

        private func requestTopic(_ id: String, title: String, startBlockID: String? = nil) {
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
                self.reader.finishLoading(topic, request: token, startBlockID: startBlockID)
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
