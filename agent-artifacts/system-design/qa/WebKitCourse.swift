import Cocoa
import WebKit

// Isolated, reproducible course interaction checks. Never reads the installed app's data.
@MainActor final class CourseRunner: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
    var web: WKWebView!
    var window: NSWindow!
    var phase = 0
    let root: URL
    let qa: URL
    let width: Double
    init(root: URL, qa: URL, width: Double) {
        self.root = root; self.qa = qa; self.width = width; super.init()
    }
    func start() {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        config.userContentController.add(self, name: "result")
        config.userContentController.addUserScript(WKUserScript(source: "window.__qaErrors=[];addEventListener('error',e=>__qaErrors.push(String(e.message)));addEventListener('unhandledrejection',e=>__qaErrors.push(String(e.reason)));", injectionTime: .atDocumentStart, forMainFrameOnly: true))
        web = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: 850), configuration: config)
        web.navigationDelegate = self
        window = NSWindow(contentRect: web.frame, styleMask: [.titled], backing: .buffered, defer: false)
        window.contentView = web
        window.title = "System Design QA \(Int(width))px"
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        web.loadFileURL(root.appendingPathComponent("system-design.html"), allowingReadAccessTo: root)
        DispatchQueue.main.asyncAfter(deadline: .now() + 60) { print("NOT_RUN: WebKit timeout before completion"); exit(2) }
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        let file = qa.appendingPathComponent(phase == 0 ? "course.test.js" : "restore.test.js")
        do {
            let source = try String(contentsOf: file, encoding: .utf8)
            web.evaluateJavaScript("void " + source) { _, error in
                if let error { print("FAIL: JS: \(error)"); exit(1) }
            }
        } catch { print("FAIL: \(error)"); exit(1) }
    }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        print("FAIL: load \(error)"); exit(1)
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        print("FAIL: WebContent process terminated"); exit(1)
    }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let result = message.body as? [String: Any] else { return }
        print(result)
        guard result["ok"] as? Bool == true else { exit(1) }
        if phase == 0 { phase = 1; web.reload(); return }
        let snapshot = WKSnapshotConfiguration()
        snapshot.rect = web.bounds
        web.takeSnapshot(with: snapshot) { image, error in
            guard let image, let tiff = image.tiffRepresentation,
                  let bitmap = NSBitmapImageRep(data: tiff),
                  let png = bitmap.representation(using: .png, properties: [:]) else {
                print("PASS: interaction checks; screenshot NOT_RUN: \(String(describing: error))"); exit(0)
            }
            do { try png.write(to: self.qa.appendingPathComponent("course-\(Int(self.width)).png")) }
            catch { print("FAIL: screenshot save \(error)"); exit(1) }
            print("PASS: course interactions, reload persistence, \(Int(self.width))px snapshot"); exit(0)
        }
    }
}
@main struct CourseChecks {
    @MainActor static func main() {
        guard CommandLine.arguments.count == 4, let width = Double(CommandLine.arguments[3]) else {
            print("Usage: WebKitCourse COURSE_FOLDER QA_FOLDER WIDTH"); exit(1)
        }
        let app = NSApplication.shared
        app.setActivationPolicy(.regular)
        let runner = CourseRunner(root: URL(fileURLWithPath: CommandLine.arguments[1]), qa: URL(fileURLWithPath: CommandLine.arguments[2]), width: width)
        runner.start()
        app.run()
    }
}
