import WebKit

/// Shared by the production coordinator and the WebKit integration tests.
enum BookMessageTrust {
    static func accepts(_ message: WKScriptMessage, controller: WKUserContentController, webView: WKWebView?, folder: URL?) -> Bool {
        guard let webView = webView, let folder = folder,
              message.webView === webView,
              controller === webView.configuration.userContentController,
              message.frameInfo.isMainFrame,
              let url = webView.url, url.isFileURL,
              url.standardizedFileURL.path == folder.appendingPathComponent("index.html").standardizedFileURL.path,
              let source = message.frameInfo.request.url, source.isFileURL,
              source.standardizedFileURL.path == url.standardizedFileURL.path else { return false }
        return true
    }
}
