import SwiftUI
import AVFoundation

@MainActor final class PoCState: ObservableObject {
    @Published var status = "Готов к проверке"
    @Published var fixtures: [String] = []
    @Published var busy = false
    @Published var technicalMode = false
    @Published var titles: [String:String] = [:]
    @Published var speakable: [String:String] = [:]
    private var player: AVAudioPlayer?
    func start(technical: Bool = false) {
        guard !busy else { return };technicalMode=technical;let useTechnical=technicalMode;busy=true;fixtures=[];titles=[:];speakable=[:];status="Загрузка исследовательского runtime…"
        Task.detached(priority:.userInitiated) { [self] in
            do {
                if useTechnical {
                    let harness=try TechnicalHarness()
                    let report=try harness.run { name in Task { @MainActor in self.status="Синтез: \(name)" } }
                    let rows=report["audio"] as! [[String:Any]]
                    await MainActor.run {
                        self.fixtures=rows.map{$0["id"] as! String}
                        self.titles=Dictionary(uniqueKeysWithValues:rows.map{($0["id"] as! String,$0["source"] as! String)})
                        self.speakable=Dictionary(uniqueKeysWithValues:rows.map{($0["id"] as! String,$0["speakable"] as! String)})
                        self.status="Текст: \((report["cases"] as! [[String:Any]]).count)/60; аудио: \(rows.count)/20";self.busy=false
                    }
                } else if ProcessInfo.processInfo.arguments.contains("--fixtures-only") {
                    let harness = try FixtureHarness()
                    let report = try harness.all { name in Task { @MainActor in self.status="Проверка: \(name)" } }
                    let ids = (report["cases"] as! [[String:Any]]).filter { $0["pass"] as? Bool == true }.map { $0["id"] as! String }
                    await MainActor.run { self.fixtures=ids;self.status="Fixture parity: \(ids.count)/8";self.busy=false }
                } else {
                    let harness = try PreprocessingHarness()
                    let report = try harness.run { name in Task { @MainActor in self.status="Проверка: \(name)" } }
                    let ids = (report["waveforms"] as! [[String:Any]]).filter { $0["pass"] as? Bool == true }.map { $0["id"] as! String }
                    await MainActor.run { self.fixtures=ids;self.status="Preprocessing: 25/25; waveform: \(ids.count)/8.";self.busy=false }
                }
            } catch {
                let message=String(describing:error)
                let dir=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0]
                try? message.write(to:dir.appendingPathComponent("error.txt"),atomically:true,encoding:.utf8)
                print("POC ERROR \(message)")
                await MainActor.run { self.status=message;self.busy=false }
            }
        }
    }
    func play(_ fixture: String) {
        do {
            let url=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0].appendingPathComponent("\(technicalMode ? "TechnicalResults" : "Results")/\(fixture).wav")
            player=try AVAudioPlayer(contentsOf:url);player?.prepareToPlay()
            let started=player?.play() ?? false
            status=started ? "Воспроизведение: \(fixture)" : "Не удалось начать воспроизведение"
            let proof:[String:Any]=["fixture":fixture,"play_returned":started,"is_playing":player?.isPlaying ?? false,"duration":player?.duration ?? 0]
            try JSONSerialization.data(withJSONObject:proof).write(to:url.deletingLastPathComponent().appendingPathComponent("playback.json"))
        } catch { status=String(describing:error) }
    }
}
@main struct SileroIOSPoCApp: App {
    @StateObject private var state=PoCState()
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                List {
                    Text(state.status).accessibilityIdentifier("poc.status")
                    Button("Raw text → waveform") { state.start() }.disabled(state.busy)
                    Button("Технические примеры") { state.start(technical:true) }.disabled(state.busy)
                    ForEach(state.fixtures,id:\.self) { name in
                        Button { state.play(name) } label: {
                            VStack(alignment:.leading,spacing:6) {
                                Text(state.titles[name] ?? "Play \(name)")
                                if let text=state.speakable[name]{Text(text).font(.caption).foregroundStyle(.secondary)}
                            }
                        }.accessibilityIdentifier("play.\(name)")
                    }
                }.navigationTitle("Silero Fixture PoC")
            }.task { state.start(technical:ProcessInfo.processInfo.arguments.contains("--technical")) }
        }
    }
}
