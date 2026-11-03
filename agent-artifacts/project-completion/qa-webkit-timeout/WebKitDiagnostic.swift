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
    var diagnosticTimer: Timer?
    let root: URL
    init(root: URL) { self.root = root; super.init() }
    func start() {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        config.userContentController.add(self, name: "probe")
        let probeJS = """
        (() => {
          let frames = 0;
          const send = (mark, extra={}) => window.webkit.messageHandlers.probe.postMessage({mark, now:Date.now(), ready:document.readyState, visibility:document.visibilityState, frames, hash:location.hash, ...extra});
          window.addEventListener('error', e => send('window-error',{message:String(e.message)}));
          window.addEventListener('unhandledrejection', e => send('unhandled-rejection',{message:String(e.reason)}));
          window.addEventListener('visibilitychange', () => send('visibilitychange'));
          function frame() { frames++; requestAnimationFrame(frame); }
          requestAnimationFrame(frame);
          setInterval(() => send('js-heartbeat'), 2000);
          send('document-start');
        })();
        """
        config.userContentController.addUserScript(WKUserScript(source:probeJS, injectionTime:.atDocumentStart, forMainFrameOnly:true))
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
        diagnosticTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats:true) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self = self else { return }
                print("NATIVE heartbeat phase=\(self.phase) active=\(NSApp.isActive) visible=\(self.window.isVisible) occluded=\(!self.window.occlusionState.contains(.visible)) loading=\(self.web.isLoading)")
                fflush(stdout)
            }
        }
        web.loadFileURL(root.appendingPathComponent("index.html"), allowingReadAccessTo:root)
        DispatchQueue.main.asyncAfter(deadline:.now()+65) { print("FAIL: timeout"); exit(1) }
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        print("Loaded test phase \(phase)"); fflush(stdout)
        if phase >= 2 {
            let testFile = phase == 2 ? "/saved-excerpts.test.js" : phase == 3 ? "/reader-gestures.test.js" : "/content.test.js"
            let js = try! String(contentsOfFile: CommandLine.arguments[2] + testFile, encoding: .utf8)
            web.evaluateJavaScript("void " + js) { _, error in print("evaluateJavaScript returned phase=\(self.phase) error=\(String(describing:error))"); fflush(stdout); if let error = error { print(error); exit(1) } }
            return
        }
        let path = CommandLine.arguments[2] + (phase == 0 ? "/reader.test.js" : "/restore.test.js")
        do {
            let extraction = phase == 0 ? try String(contentsOfFile: CommandLine.arguments[2] + "/audio-extraction.test.js", encoding: .utf8) : ""
            let js = "window.webkit.messageHandlers.probe.postMessage({mark:'before-audio'});\n" + extraction + "\nwindow.webkit.messageHandlers.probe.postMessage({mark:'after-audio'});\nvoid " + (try String(contentsOfFile:path, encoding:.utf8)) + "\nwindow.webkit.messageHandlers.probe.postMessage({mark:'reader-scheduled'}); void 0;"
            web.evaluateJavaScript("void " + js) { _, error in print("evaluateJavaScript returned phase=\(self.phase) error=\(String(describing:error))"); fflush(stdout); if let error = error { print(error); exit(1) } }
        } catch { print(error); exit(1) }
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) { print("FAIL: WebContent process terminated phase=\(phase)"); fflush(stdout); exit(2) }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { print("FAIL: navigation: \(error)"); fflush(stdout); exit(3) }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { print("FAIL: provisional navigation: \(error)"); fflush(stdout); exit(4) }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "probe" { print("JS probe \(message.body)"); fflush(stdout); return }
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
