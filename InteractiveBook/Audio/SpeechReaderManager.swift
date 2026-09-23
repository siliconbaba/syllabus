import AVFoundation
import Combine
import Foundation
#if os(iOS)
import UIKit
import MediaPlayer
#endif

protocol SpeechSynthesizing: AnyObject {
    var delegate: AVSpeechSynthesizerDelegate? { get set }
    func speak(_ utterance: AVSpeechUtterance)
    func stopSpeaking(at boundary: AVSpeechBoundary) -> Bool
    func pauseSpeaking(at boundary: AVSpeechBoundary) -> Bool
    func continueSpeaking() -> Bool
}
extension AVSpeechSynthesizer: SpeechSynthesizing {}

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

/// One synthesizer, one active utterance, one in-memory topic. No WebKit dependency.
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

    private var synthesizer: SpeechSynthesizing
    private let makeSynthesizer: () -> SpeechSynthesizing
    private let session: SpeechAudioSession
    private let defaults: UserDefaults
    private let processor = SpeechTextProcessor()
    private var activeUtterance: AVSpeechUtterance?
    private var utteranceOffset = 0
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
         observeSystem: Bool = true) {
        self.defaults = defaults
        self.session = session
        self.makeSynthesizer = makeSynthesizer
        self.synthesizer = makeSynthesizer()
        let saved = defaults.double(forKey: "speech.speed")
        self.speed = Self.speeds.contains(saved) ? saved : 1
        super.init()
        configureSynthesizer()
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
            installRemoteControls()
        }
        #endif
    }

    deinit {
        notifications.forEach { NotificationCenter.default.removeObserver($0) }
        synthesizer.delegate = nil
        _ = synthesizer.stopSpeaking(at: .immediate)
        if sessionActive { session.deactivate() }
        #if os(iOS)
        for (command, target) in remoteTargets { command.removeTarget(target) }
        #endif
    }

    private func configureSynthesizer() {
        synthesizer.delegate = self
        #if os(iOS)
        (synthesizer as? AVSpeechSynthesizer)?.usesApplicationAudioSession = true
        #endif
    }

    var hasPrevious: Bool { !fragments.isEmpty && currentIndex > 0 && state != .loading }
    var hasNext: Bool { currentIndex + 1 < fragments.count && state != .loading }
    var statusText: String {
        switch state {
        case .idle: return "Готово к чтению"
        case .loading: return "Подготовка текста…"
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

    func finishLoading(_ topic: SpeechTopic, request: UUID) {
        guard request == loadID, state == .loading, topic.id == topicID else { return }
        loadID = nil
        fragments = processor.fragments(from: topic)
        title = topic.title
        guard !fragments.isEmpty else {
            state = .idle; message = "В этой теме нет доступного текста для чтения."; return
        }
        chooseVoice()
        currentIndex = 0
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
        guard state != .playing && state != .loading, let id = topicID else { return }
        guard !interrupted else { message = "Дождитесь окончания системного аудио или звонка."; return }
        if fragments.isEmpty { onRequestTopic?(id); return }
        if state == .paused {
            guard activate() else { return }
            state = .playing
            if activeUtterance != nil, synthesizer.continueSpeaking() { updateNowPlaying(); return }
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
        guard state == .playing else { return }
        state = .paused
        if !synthesizer.pauseSpeaking(at: .immediate) { cancelUtterance() }
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
        stop(); topicID = nil; title = ""; fragments = []; message = nil; voiceName = ""
    }

    func previous() { if hasPrevious { move(to: currentIndex - 1) } }
    func next() { if hasNext { move(to: currentIndex + 1) } }
    private func move(to index: Int) {
        resumeAfterInterruption = false
        let shouldPlay = state == .playing
        cancelUtterance(); currentIndex = index; spokenOffset = 0
        if shouldPlay { speakCurrent() }
        else { state = .paused; highlightCurrent(); updateNowPlaying() }
    }

    func setSpeed(_ value: Double) {
        guard Self.speeds.contains(value), value != speed else { return }
        speed = value; defaults.set(value, forKey: "speech.speed")
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
        min(AVSpeechUtteranceMaximumSpeechRate,
            max(AVSpeechUtteranceMinimumSpeechRate, 0.46 * Float(speed)))
    }

    func setVoice(_ identifier: String?) {
        guard identifier == nil || availableVoices.contains(where: { $0.identifier == identifier }) else { return }
        defaults.set(identifier, forKey: "speech.voiceIdentifier")
        chooseVoice()
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
        voiceName = voice?.name ?? "Системный голос"
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
        // Invalidate before stop: delayed callbacks from old utterances must be harmless.
        activeUtterance = nil
        _ = synthesizer.stopSpeaking(at: .immediate)
    }
    private func speakCurrent(offset: Int = 0) {
        guard fragments.indices.contains(currentIndex), !interrupted else { return }
        cancelUtterance()
        guard activate() else { return }
        let text = fragments[currentIndex].text as NSString
        utteranceOffset = min(max(0, offset), max(0, text.length - 1))
        spokenOffset = utteranceOffset
        let utterance = AVSpeechUtterance(string: text.substring(from: utteranceOffset))
        utterance.voice = voice
        utterance.rate = Self.speechRate(for: speed)
        utterance.pitchMultiplier = 1.0
        utterance.preUtteranceDelay = 0
        utterance.postUtteranceDelay = fragments[currentIndex].postDelay
        activeUtterance = utterance; state = .playing
        persistBookmark(); highlightCurrent(); updateNowPlaying()
        synthesizer.speak(utterance)
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

    // All delegate work is serialized with UI actions on the main actor.
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor [weak self] in
            guard let self = self, self.activeUtterance === utterance, self.state == .playing else { return }
            self.activeUtterance = nil
            if self.currentIndex + 1 < self.fragments.count {
                self.currentIndex += 1; self.speakCurrent()
            } else {
                self.state = .finished; self.spokenOffset = 0
                self.persistBookmark(); self.clearHighlight(); self.releaseSession(); self.updateNowPlaying()
            }
        }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        Task { @MainActor [weak self] in
            guard let self = self, self.activeUtterance === utterance else { return }
            self.activeUtterance = nil; self.state = .paused; self.releaseSession(); self.updateNowPlaying()
        }
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, willSpeakRangeOfSpeechString range: NSRange, utterance: AVSpeechUtterance) {
        Task { @MainActor [weak self] in
            guard let self = self, self.activeUtterance === utterance, self.state == .playing else { return }
            self.spokenOffset = self.utteranceOffset + range.location
            if range.location == 0 { self.highlightCurrent() }
        }
    }

    func interruptionBegan() {
        interrupted = true
        resumeAfterInterruption = state == .playing
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
        stop(); interrupted = false; synthesizer = makeSynthesizer(); configureSynthesizer()
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
        let active = state == .playing || state == .paused
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
