import Cocoa
import WebKit
@MainActor final class Probe: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
 var web: WKWebView!; var window:NSWindow!
 func start(){
 let c=WKWebViewConfiguration();c.websiteDataStore = .nonPersistent();c.userContentController.add(self,name:"result")
 web=WKWebView(frame:NSRect(x:0,y:0,width:1280,height:900),configuration:c);web.navigationDelegate=self
 window=NSWindow(contentRect:web.frame,styleMask:[.titled],backing:.buffered,defer:false);window.contentView=web;window.makeKeyAndOrderFront(nil)
 let url=URL(fileURLWithPath:CommandLine.arguments[1]);web.loadFileURL(url,allowingReadAccessTo:url.deletingLastPathComponent())
 DispatchQueue.main.asyncAfter(deadline:.now()+60){print("TIMEOUT");exit(1)}
 }
 func webView(_ webView:WKWebView,didFinish navigation:WKNavigation!){
 let js=try! String(contentsOfFile:CommandLine.arguments[2],encoding:.utf8)
 web.evaluateJavaScript("void "+js){_,e in if let e=e{print(e);exit(1)}}
 }
 func userContentController(_ c:WKUserContentController,didReceive m:WKScriptMessage){print(m.body);exit(0)}
}
@main struct Main { @MainActor static func main(){let app=NSApplication.shared;app.setActivationPolicy(.regular);let p=Probe();p.start();app.run()} }
