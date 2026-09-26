import AVFoundation
import Combine
import Foundation
#if os(iOS)
import UIKit
import MediaPlayer
#endif

protocol SpeechAudioSession {
    func activate() throws
    func deactivate()
}
struct PlaybackSpeechSession: SpeechAudioSession {
    func activate() throws {
        #if os(iOS)
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playback, mode: .spokenAudio, options: [])
        try session.setActive(true)
        #endif
    }
    func deactivate() {
        #if os(iOS)
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        #endif
    }
}

/// One logical topic/queue, pluggable playback engines, one audio session and Now Playing owner.
@MainActor
final class SpeechReaderManager: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    enum State: String { case idle, loading, playing, paused, finished }
    static let speeds: [Double] = [0.8, 1, 1.2, 1.5, 2]
    @Published private(set) var state: State = .idle
    @Published private(set) var topicID: String?
    @Published private(set) var title = ""
    @Published private(set) var currentIndex = 0
    @Published private(set) var fragments: [SpeechFragment] = []
    @Published private(set) var speed: Double
    @Published private(set) var message: String?
    @Published private(set) var voiceName = ""
    @Published private(set) var availableVoices: [AVSpeechSynthesisVoice] = []
    @Published private(set) var preferredVoiceID: String?
    var onHighlight: ((String, String?) -> Void)?
    var onRequestTopic: ((String) -> Void)?

    @Published private(set) var engineKind:SpeechEngineKind
    private var engine:SpeechEngine
    private let engineFactory:(SpeechEngineKind)->SpeechEngine
    private var topic:SpeechTopic?
    private var requestIDs:[UUID]=[]
    private var activeRequest:UUID?
    private var preparation:Task<Void,Never>?
    private var engineRevision=UUID()
    private let session: SpeechAudioSession
    private let defaults: UserDefaults
    private let processor = SpeechTextProcessor()
    private var spokenOffset = 0
    private var loadID: UUID?
    private var interrupted = false
    private var resumeAfterInterruption = false
    private var sessionActive = false
    private var voice: AVSpeechSynthesisVoice?
    private var notifications: [NSObjectProtocol] = []
    #if os(iOS)
    private var remoteTargets: [(MPRemoteCommand, Any)] = []
    #endif

    init(defaults: UserDefaults = .standard,
         session: SpeechAudioSession = PlaybackSpeechSession(),
         makeSynthesizer: @escaping () -> SpeechSynthesizing = { AVSpeechSynthesizer() },
         observeSystem: Bool = true,
         makeEngine: ((SpeechEngineKind)->SpeechEngine)? = nil) {
        self.defaults = defaults
        self.session = session
        let factory: (SpeechEngineKind)->SpeechEngine = makeEngine ?? { kind in
            if kind == .system{return AppleSpeechEngine(makeSynthesizer:makeSynthesizer)}
            #if os(iOS)
            return SileroSpeechEngine()
            #else
            return UnavailableSpeechEngine()
            #endif
        }
        self.engineFactory=factory
        let kind=SpeechEngineKind(rawValue:defaults.string(forKey:"speech.engine") ?? "") ?? .system
        self.engineKind=kind;self.engine=factory(kind)
        let saved = defaults.double(forKey: "speech.speed")
        self.speed = Self.speeds.contains(saved) ? saved : 1
        super.init()
        connectEngine()
        chooseVoice()
        #if os(iOS)
        if observeSystem {
            func observe(_ name: Notification.Name, action: @escaping @MainActor (SpeechReaderManager, Notification) -> Void) {
                notifications.append(NotificationCenter.default.addObserver(forName: name, object: nil, queue: .main) { [weak self] note in
                    Task { @MainActor in
                        guard let self = self else { return }
                        action(self, note)
                    }
                })
            }
            observe(AVAudioSession.interruptionNotification) { $0.audioInterrupted($1) }
            observe(AVAudioSession.routeChangeNotification) { $0.routeChanged($1) }
            observe(AVAudioSession.mediaServicesWereResetNotification) { reader, _ in reader.mediaReset() }
            observe(UIApplication.didBecomeActiveNotification) { reader, _ in reader.becameActive() }
            observe(UIApplication.didReceiveMemoryWarningNotification) { reader,_ in reader.memoryPressure() }
            installRemoteControls()
        }
        #endif
    }

    deinit {
        notifications.forEach { NotificationCenter.default.removeObserver($0) }
        preparation?.cancel()
        let engine=engine
        Task { @MainActor in engine.shutdown() }
        if sessionActive { session.deactivate() }
        #if os(iOS)
        for (command, target) in remoteTargets { command.removeTarget(target) }
        #endif
    }

    private func connectEngine() {
        let revision=engineRevision
        engine.onEvent={ [weak self] event in
            guard let self=self,self.engineRevision==revision else{return}
            self.receive(event)
        }
    }
    private func receive(_ event:SpeechEngineEvent) {
        switch event {
        case .started(let id):
            guard id==activeRequest,state != .paused else{return}
            state = .playing;persistBookmark();highlightCurrent();updateNowPlaying()
        case .progress(let id,let offset):if id==activeRequest && state == .playing{spokenOffset=offset}
        case .finished(let id):
            guard id==activeRequest,state == .playing else{return}
            activeRequest=nil
            if currentIndex+1<fragments.count{currentIndex+=1;speakCurrent()}
            else{state = .finished;spokenOffset=0;engine.stop();persistBookmark();clearHighlight();releaseSession();updateNowPlaying()}
        case .failed(let id,_):
            guard id==activeRequest else{return}
            if engineKind == .neural{fallbackToSystem(resume:state != .paused)}
            else{activeRequest=nil;state = .paused;releaseSession();updateNowPlaying()}
        }
    }
    func setEngine(_ kind:SpeechEngineKind) {
        guard kind != engineKind else{return}
        let wasPlaying=state == .playing || state == .loading && !fragments.isEmpty
        let block=fragments.indices.contains(currentIndex) ? fragments[currentIndex].blockID:nil
        cancelUtterance();releaseSession();engine.shutdown();engineRevision=UUID()
        engineKind=kind;defaults.set(kind.rawValue,forKey:"speech.engine");engine=engineFactory(kind);connectEngine()
        if let topic=topic{fragments=processor.fragments(from:topic,systemNormalization:kind == .system);requestIDs=fragments.map{_ in UUID()};currentIndex=block.flatMap{b in fragments.firstIndex{$0.blockID==b}} ?? 0}
        spokenOffset=0;chooseVoice()
        if wasPlaying{speakCurrent()}
        else if kind == .neural{prepareSelected(resume:false)}
        else{state = fragments.isEmpty ? .idle:.paused;updateNowPlaying()}
    }
    private func fallbackToSystem(resume:Bool) {
        // Stop before switching; retry the same logical block, never drop it.
        state = resume ? .playing:.paused
        setEngine(.system)
        message="Нейросетевой голос недоступен. Продолжаем системным голосом."
    }
    private func prepareSelected(resume:Bool) {
        preparation?.cancel();let revision=engineRevision;let selected=engine
        state = .loading;updateNowPlaying()
        preparation=Task { [weak self] in
            do {
                try await selected.prepare();try Task.checkCancellation()
                guard let self=self,self.engineRevision==revision else{return}
                self.preparation=nil
                if resume{self.speakCurrent()}
                else{self.state=self.fragments.isEmpty ? .idle:.paused;self.updateNowPlaying()}
            }catch{
                guard !Task.isCancelled,let self=self,self.engineRevision==revision else{return}
                self.preparation=nil;self.fallbackToSystem(resume:resume)
            }
        }
    }
    func memoryPressure() {
        guard engineKind == .neural else{return}
        pauseInternal();cancelUtterance();engine.shutdown();releaseSession();state = .paused
        message="Нейросетевой голос выгружен для освобождения памяти. Нажмите «Продолжить»."
    }

    var hasPrevious: Bool { !fragments.isEmpty && currentIndex > 0 && loadID == nil }
    var hasNext: Bool { currentIndex + 1 < fragments.count && loadID == nil }
    var statusText: String {
        switch state {
        case .idle: return "Готово к чтению"
        case .loading: return engineKind == .neural && loadID == nil ? "Подготовка нейросетевого голоса…":"Подготовка текста…"
        case .playing: return "Чтение · \(currentIndex + 1) из \(fragments.count)"
        case .paused: return "Пауза · \(currentIndex + 1) из \(fragments.count)"
        case .finished: return "Тема прочитана"
        }
    }

    @discardableResult
    func beginLoading(id: String, title: String) -> UUID {
        reset()
        topicID = id; self.title = title
        state = .loading
        let token = UUID(); loadID = token
        return token
    }

    func finishLoading(_ topic: SpeechTopic, request: UUID, startBlockID: String? = nil) {
        guard request == loadID, state == .loading, topic.id == topicID else { return }
        loadID = nil
        self.topic=topic
        fragments = processor.fragments(from: topic, systemNormalization: engineKind == .system)
        requestIDs=fragments.map{_ in UUID()}
        title = topic.title
        guard !fragments.isEmpty else {
            state = .idle; message = "В этой теме нет доступного текста для чтения."; return
        }
        chooseVoice()
        if let block = startBlockID {
            guard let index = fragments.firstIndex(where: { $0.blockID == block }) else {
                state = .idle; message = "Выбранный абзац недоступен. Выделите текст ещё раз."; return
            }
            currentIndex = index
        } else { currentIndex = 0 }
        speakCurrent()
    }

    func failLoading(request: UUID) {
        guard request == loadID else { return }
        loadID = nil; state = .idle
        message = "Не удалось получить текст темы. Нажмите «Слушать» ещё раз."
    }

    func contextChanged(to id: String?, invalidate: Bool = false) {
        guard let topicID = topicID else { return }
        if id != topicID || invalidate { reset() }
    }

    func play() {
        guard state != .playing && loadID == nil, let id = topicID else { return }
        guard !interrupted else { message = "Дождитесь окончания системного аудио или звонка."; return }
        if fragments.isEmpty { onRequestTopic?(id); return }
        if state == .paused {
            guard activate() else { return }
            state = .playing
            if activeRequest != nil, engine.resume() { updateNowPlaying(); return }
            speakCurrent(offset: spokenOffset)
        } else {
            currentIndex = 0; speakCurrent()
        }
    }

    func pause() {
        resumeAfterInterruption = false
        pauseInternal()
    }

    private func pauseInternal() {
        guard state == .playing || state == .loading && loadID == nil else { return }
        preparation?.cancel();preparation=nil
        state = .paused
        engine.pause()
        releaseSession()
        updateNowPlaying()
    }

    func stop() {
        loadID = nil; resumeAfterInterruption = false
        cancelUtterance(); releaseSession()
        currentIndex = 0; spokenOffset = 0; state = .idle
        clearHighlight(); updateNowPlaying()
    }

    func reset() {
        stop(); topicID = nil; topic=nil;title = ""; fragments = [];requestIDs=[]; message = nil; voiceName = ""
    }

    func previous() { if hasPrevious { move(to: currentIndex - 1) } }
    func next() { if hasNext { move(to: currentIndex + 1) } }
    private func move(to index: Int) {
        resumeAfterInterruption = false
        let shouldPlay = state == .playing || state == .loading
        cancelUtterance(); currentIndex = index; spokenOffset = 0
        if shouldPlay { speakCurrent() }
        else { state = .paused; highlightCurrent(); updateNowPlaying() }
    }

    func setSpeed(_ value: Double) {
        guard Self.speeds.contains(value), value != speed else { return }
        speed = value; defaults.set(value, forKey: "speech.speed")
        if engineKind == .neural{engine.setSpeed(value);updateNowPlaying();return}
        let playing = state == .playing
        if playing || state == .paused {
            let offset = spokenOffset
            cancelUtterance()
            if playing { speakCurrent(offset: offset) }
        }
    }

    static func qualityLabel(_ voice: AVSpeechSynthesisVoice) -> String {
        switch voice.quality {
        case .premium: return "Premium"
        case .enhanced: return "Enhanced"
        default: return "Standard"
        }
    }

    // A slightly slower baseline than Apple's default suits dense textbook prose.
    // These are relative TTS settings, not exact audio-duration multipliers.
    static func speechRate(for speed: Double) -> Float {
        AppleSpeechEngine.rate(for:speed)
    }

    func setVoice(_ identifier: String?) {
        guard identifier == nil || availableVoices.contains(where: { $0.identifier == identifier }) else { return }
        defaults.set(identifier, forKey: "speech.voiceIdentifier")
        chooseVoice()
        guard engineKind == .system else{return}
        let playing = state == .playing
        if playing || state == .paused {
            let offset = spokenOffset
            cancelUtterance()
            if playing { speakCurrent(offset: offset) }
        }
    }

    private func chooseVoice() {
        let all = AVSpeechSynthesisVoice.speechVoices()
        availableVoices = all.filter { $0.language.lowercased() == "ru-ru" }.sorted {
            if $0.quality.rawValue != $1.quality.rawValue { return $0.quality.rawValue > $1.quality.rawValue }
            return $0.identifier < $1.identifier
        }
        preferredVoiceID = defaults.string(forKey: "speech.voiceIdentifier")
        let automatic = availableVoices.first(where: { candidate in
            #if os(iOS)
            if #available(iOS 17.0, *), candidate.voiceTraits.contains(.isPersonalVoice) || candidate.voiceTraits.contains(.isNoveltyVoice) { return false }
            #endif
            return true
        }) ?? all.filter { $0.language.lowercased().hasPrefix("ru") }
            .sorted { $0.quality.rawValue > $1.quality.rawValue }.first
        let preferred = availableVoices.first { $0.identifier == preferredVoiceID }
        if preferred == nil { preferredVoiceID = nil } // Keep the saved ID in case its downloaded voice returns.
        voice = preferred ?? automatic ?? AVSpeechSynthesisVoice(language: "ru-RU") ?? AVSpeechSynthesisVoice(language: "ru")
        if voice == nil {
            voice = AVSpeechSynthesisVoice(language: AVSpeechSynthesisVoice.currentLanguageCode())
            message = "Русский голос недоступен. Используется системный голос. Русские голоса можно загрузить в настройках универсального доступа iPhone."
        } else { message = nil }
        voiceName = engineKind == .neural ? "Нейросетевой · Xenia" : (voice?.name ?? "Системный голос")
        #if DEBUG
        for candidate in availableVoices {
            NSLog("Speech voice: name=%@ identifier=%@ quality=%@ selected=%@", candidate.name,
                  candidate.identifier, Self.qualityLabel(candidate), candidate.identifier == voice?.identifier ? "true" : "false")
        }
        NSLog("Automatic speech voice: %@", automatic.map { "\($0.name) | \($0.identifier) | \(Self.qualityLabel($0))" } ?? "system fallback")
        NSLog("Selected speech voice: %@", voice.map { "\($0.name) | \($0.identifier) | \(Self.qualityLabel($0))" } ?? "system fallback")
        #endif
    }

    private func activate() -> Bool {
        do { try session.activate(); sessionActive = true; return true }
        catch {
            state = .paused
            message = "Аудио сейчас недоступно. Попробуйте продолжить чтение позже."
            return false
        }
    }
    private func releaseSession() {
        if sessionActive { session.deactivate(); sessionActive = false }
    }
    private func cancelUtterance() {
        activeRequest=nil;preparation?.cancel();preparation=nil;engine.stop()
        requestIDs=fragments.map{_ in UUID()}
    }
    private func speakCurrent(offset:Int=0) {
        guard fragments.indices.contains(currentIndex),!interrupted else{return}
        if engine.requiresPreparation{prepareSelected(resume:true);return}
        guard activate() else{return}
        func request(_ i:Int,_ offset:Int=0)->SpeechRequest {
            SpeechRequest(id:requestIDs[i],fragment:fragments[i],offset:offset,speed:speed,voiceIdentifier:voice?.identifier)
        }
        spokenOffset=offset;let current=request(currentIndex,offset);activeRequest=current.id
        // Only cold start displays loading. Warm prebuffer never flashes a spinner.
        if state != .playing{state = engineKind == .system ? .playing:.loading}
        engine.speak(current,next:currentIndex+1<fragments.count ? request(currentIndex+1):nil)
    }
    private func persistBookmark() {
        defaults.set(topicID, forKey: "speech.lastTopic")
        defaults.set(currentIndex, forKey: "speech.lastBlock")
    }
    private func highlightCurrent() {
        guard let id = topicID, fragments.indices.contains(currentIndex) else { return }
        onHighlight?(id, fragments[currentIndex].blockID)
    }
    private func clearHighlight() { if let id = topicID { onHighlight?(id, nil) } }

    // Compatibility entry points for existing system-voice regression tests.
    nonisolated func speechSynthesizer(_ s:AVSpeechSynthesizer,didFinish u:AVSpeechUtterance){Task{@MainActor [weak self] in (self?.engine as? AppleSpeechEngine)?.speechSynthesizer(s,didFinish:u)}}
    nonisolated func speechSynthesizer(_ s:AVSpeechSynthesizer,didCancel u:AVSpeechUtterance){Task{@MainActor [weak self] in (self?.engine as? AppleSpeechEngine)?.speechSynthesizer(s,didCancel:u)}}
    nonisolated func speechSynthesizer(_ s:AVSpeechSynthesizer,willSpeakRangeOfSpeechString r:NSRange,utterance u:AVSpeechUtterance){Task{@MainActor [weak self] in (self?.engine as? AppleSpeechEngine)?.speechSynthesizer(s,willSpeakRangeOfSpeechString:r,utterance:u)}}

    func interruptionBegan() {
        interrupted = true
        resumeAfterInterruption = state == .playing || state == .loading && loadID == nil
        pauseInternal()
    }
    func interruptionEnded(shouldResume: Bool) {
        interrupted = false
        let resume = resumeAfterInterruption && shouldResume && state == .paused
        resumeAfterInterruption = false
        if resume { play() }
    }
    #if os(iOS)
    @objc private func audioInterrupted(_ note: Notification) {
        guard let raw = note.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
        if type == .began { interruptionBegan() }
        else {
            let rawOptions = note.userInfo?[AVAudioSessionInterruptionOptionKey] as? UInt ?? 0
            interruptionEnded(shouldResume: AVAudioSession.InterruptionOptions(rawValue: rawOptions).contains(.shouldResume))
        }
    }
    @objc private func routeChanged(_ note: Notification) {
        guard let raw = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
              AVAudioSession.RouteChangeReason(rawValue: raw) == .oldDeviceUnavailable else { return }
        pause() // Do not suddenly continue through the loudspeaker after headphones disconnect.
    }
    @objc private func mediaReset() {
        stop(); interrupted = false;engine.shutdown();engineRevision=UUID();engine=engineFactory(engineKind);connectEngine()
        message = "Аудиосистема перезапущена. Нажмите «Слушать», чтобы продолжить."
    }
    @objc private func becameActive() { if state == .playing || state == .paused { highlightCurrent() } }
    private func installRemoteControls() {
        let center = MPRemoteCommandCenter.shared()
        func add(_ command: MPRemoteCommand, action: @escaping @MainActor (SpeechReaderManager) -> Void) {
            let target = command.addTarget { [weak self] _ in
                guard let self = self else { return .commandFailed }
                Task { @MainActor in action(self) }
                return .success
            }
            remoteTargets.append((command, target))
        }
        add(center.playCommand) { $0.play() }
        add(center.pauseCommand) { $0.pause() }
        add(center.togglePlayPauseCommand) { if $0.state == .playing { $0.pause() } else { $0.play() } }
        add(center.stopCommand) { $0.stop() }
        add(center.nextTrackCommand) { $0.next() }
        add(center.previousTrackCommand) { $0.previous() }
        updateNowPlaying()
    }
    #endif
    private func updateNowPlaying() {
        #if os(iOS)
        guard !remoteTargets.isEmpty else { return }
        let active = state == .playing || state == .paused || state == .loading && !fragments.isEmpty
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.isEnabled = active && state == .paused
        center.pauseCommand.isEnabled = active && state == .playing
        center.togglePlayPauseCommand.isEnabled = active
        center.stopCommand.isEnabled = active
        center.nextTrackCommand.isEnabled = active && hasNext
        center.previousTrackCommand.isEnabled = active && hasPrevious
        if active {
            MPNowPlayingInfoCenter.default().nowPlayingInfo = [
                MPMediaItemPropertyTitle: title,
                MPMediaItemPropertyArtist: "Учебник · блок \(currentIndex + 1) из \(fragments.count)",
                MPNowPlayingInfoPropertyPlaybackRate: state == .playing ? speed : 0,
                MPNowPlayingInfoPropertyMediaType: MPNowPlayingInfoMediaType.audio.rawValue
            ]
        } else { MPNowPlayingInfoCenter.default().nowPlayingInfo = nil }
        #endif
    }
}
