import Cocoa
import WebKit

// Standalone WebKit integration checks. Runs with isolated storage, not the user's app data.
@MainActor final class Runner: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
    var web: WKWebView!
    var window: NSWindow!
    let excerpts = SavedExcerptStore(defaults: UserDefaults(suiteName: "WebKitSavedTests." + UUID().uuidString)!)
    var listenedBlock: String?
    var trainerOpened = false
    var phase = 0
    var state: [String:String] = [:]
    let root: URL
    init(root: URL) { self.root = root; super.init() }
    func start() {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        config.userContentController.add(self, name: "setting")
        config.userContentController.add(self, name: "result")
        config.userContentController.add(self, name: "saved")
        config.userContentController.add(self, name: "trainer")
        web = WKWebView(frame: NSRect(x:0,y:0,width:Double(CommandLine.arguments.count > 3 ? CommandLine.arguments[3] : "390") ?? 390,height:Double(CommandLine.arguments.count > 4 ? CommandLine.arguments[4] : "760") ?? 760), configuration:config)
        web.navigationDelegate = self
        window = NSWindow(contentRect: web.frame, styleMask: [.titled], backing:.buffered, defer:false)
        window.contentView = web
        window.title = "Проверка учебника WebKit"
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        web.loadFileURL(root.appendingPathComponent("index.html"), allowingReadAccessTo:root)
        DispatchQueue.main.asyncAfter(deadline:.now()+180) { print("FAIL: timeout"); exit(1) }
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        print("Loaded test phase \(phase)")
        if phase < 2 {
            waitForVisibleFrames { self.runPhase() }
        } else {
            runPhase()
        }
    }
    // A hidden/occluded desktop can suspend rAF and JS timers while native timers run.
    // Do not turn unavailable rendering into a misleading content-test timeout.
    func waitForVisibleFrames(_ ready: @escaping () -> Void) {
        var finished = false
        web.evaluateJavaScript("window.__smokeFrames = 0; requestAnimationFrame(function(){ window.__smokeFrames++; requestAnimationFrame(function(){window.__smokeFrames++;}); });") { _, error in
            if let error = error { print("FAIL: rendering preflight JavaScript: \(error)"); exit(1) }
        }
        func poll() {
            guard !finished else { return }
            web.evaluateJavaScript("({frames:window.__smokeFrames || 0, visibility:document.visibilityState})") { value, error in
                guard !finished else { return }
                if let error = error { print("FAIL: rendering preflight: \(error)"); exit(1) }
                if let status = value as? [String:Any], (status["frames"] as? Int ?? 0) >= 2,
                   status["visibility"] as? String == "visible", self.window.occlusionState.contains(.visible) {
                    finished = true
                    print("PASS: visible animation frames available")
                    ready()
                } else {
                    DispatchQueue.main.asyncAfter(deadline:.now()+0.5) { poll() }
                }
            }
        }
        DispatchQueue.main.asyncAfter(deadline:.now()+0.1) { poll() }
        DispatchQueue.main.asyncAfter(deadline:.now()+20) {
            guard !finished else { return }
            finished = true
            if !self.window.occlusionState.contains(.visible) {
                print("ENVIRONMENT_UNAVAILABLE: WebKit window is occluded; no animation frames. Run in an unlocked visible desktop. Remaining UI assertions NOT_RUN; phase \(self.phase).")
                exit(2)
            }
            print("FAIL: visible WebKit did not produce animation frames in 20 seconds")
            exit(1)
        }
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        print("FAIL: WebContent process terminated during phase \(phase)"); exit(1)
    }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        print("FAIL: navigation: \(error)"); exit(1)
    }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        print("FAIL: provisional navigation: \(error)"); exit(1)
    }
    func runPhase() {
        if phase >= 2 {
            let testFile = phase == 2 ? "/saved-excerpts.test.js" : phase == 3 ? "/reader-gestures.test.js" : "/content.test.js"
            let js = try! String(contentsOfFile: CommandLine.arguments[2] + testFile, encoding: .utf8)
            web.evaluateJavaScript("void " + js) { _, error in if let error = error { print(error); exit(1) } }
            return
        }
        let path = CommandLine.arguments[2] + (phase == 0 ? "/reader.test.js" : "/restore.test.js")
        do {
            let extraction = phase == 0 ? try String(contentsOfFile: CommandLine.arguments[2] + "/audio-extraction.test.js", encoding: .utf8) : ""
            let js = extraction + "\nvoid " + (try String(contentsOfFile:path, encoding:.utf8))
            web.evaluateJavaScript("void " + js) { _, error in if let error = error { print(error); exit(1) } }
        } catch { print(error); exit(1) }
    }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "trainer" {
            guard BookMessageTrust.accepts(message, controller:userContentController, webView:web, folder:root),
                  let payload = message.body as? [String:String], payload == ["action":"open"] else { print("FAIL: trainer bridge"); exit(1) }
            trainerOpened = true; return
        }
        if message.name == "setting", let p = message.body as? [String:String], let k=p["key"],let v=p["value"] { state[k]=v; return }
        if message.name == "saved", let payload = message.body as? [String: Any], ["save","listenFrom"].contains(payload["action"] as? String ?? "") {
            guard BookMessageTrust.accepts(message, controller:userContentController, webView:web, folder:root) else { print("FAIL: production bridge rejected local saved action");exit(1) }
            if payload["action"] as? String == "listenFrom" {
                guard let item = SavedExcerpt.from(payload:payload), excerpts.excerpts.contains(where:{$0.anchor == item.anchor}) else {print("FAIL: cross-feature semantic ID");exit(1)}
                listenedBlock = item.anchor
            } else { _ = excerpts.save(payload) }
            return
        }
        guard let result=message.body as? [String:Any] else { return }
        print(result)
        if result["ok"] as? Bool != true { exit(1) }
        if phase == 4 { guard trainerOpened else {print("FAIL: trainer entry");exit(1)}; print("PASS: integrated content, answer tabs, search, diagram layout and speech"); exit(0) }
        if phase == 3 { print("PASS: edge navigation and menu gestures, cancellation and conflict guards"); phase=4; self.webView(web, didFinish:nil); return }
        if phase == 2 {
            guard excerpts.excerpts.count == 1 && listenedBlock == excerpts.excerpts[0].anchor else { print("FAIL: native saved store"); exit(1) }
            print("PASS: saved selection, bridge, persistence and source navigation"); phase=3; self.webView(web, didFinish:nil); return
        }
        if phase == 0 {
            guard state["ya-reading"] != nil, state["ya-done-t-10-9"] == "1" else { print("FAIL: native bridge did not receive state");exit(1) }
            let json = String(data:try! JSONSerialization.data(withJSONObject:state),encoding:.utf8)!
            web.configuration.userContentController.addUserScript(WKUserScript(source:"window.__nativeState = \(json);",injectionTime:.atDocumentStart,forMainFrameOnly:true))
            phase=1
            web.reload()
        } else { print("PASS: WebKit integration and native-state restoration"); phase=2; self.webView(web, didFinish:nil) }
    }
}
@main struct WebKitChecks {
 @MainActor static func main() {
let app = NSApplication.shared
app.setActivationPolicy(.regular)
let runner = Runner(root:URL(fileURLWithPath:CommandLine.arguments[1]))
runner.start()
app.run()

 }
}
