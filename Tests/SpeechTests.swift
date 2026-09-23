import AVFoundation
import Foundation

final class FakeSpeech: SpeechSynthesizing {
    weak var delegate: AVSpeechSynthesizerDelegate?
    var utterances: [AVSpeechUtterance] = []
    var pauseSucceeds = true
    var resumeSucceeds = true
    var stops = 0
    func speak(_ utterance: AVSpeechUtterance) { utterances.append(utterance) }
    func stopSpeaking(at boundary: AVSpeechBoundary) -> Bool { stops += 1; return true }
    func pauseSpeaking(at boundary: AVSpeechBoundary) -> Bool { pauseSucceeds }
    func continueSpeaking() -> Bool { resumeSucceeds }
}
final class FakeSession: SpeechAudioSession {
    var active = false
    var shouldFail = false
    func activate() throws { if shouldFail { throw NSError(domain: "test", code: 1) }; active = true }
    func deactivate() { active = false }
}

@main
struct SpeechTests {
    @MainActor static func main() async {
        func check(_ condition: @autoclosure () -> Bool, _ label: String) {
            guard condition() else { print("FAIL: \(label)"); exit(1) }
            print("PASS: \(label)")
        }
        func callbacks() async { try? await Task.sleep(nanoseconds: 30_000_000) }
        let processor = SpeechTextProcessor()
        check(processor.normalize("REST API, HTTPS, SQL и CI/CD") == "рэст эй пи ай, эйч ти ти пи эс, эс кью эль и си ай си ди", "technical pronunciations")
        check(processor.normalize("capital UI UX PostgreSQL Kafka JSON XML") == "capital ю ай ю икс постгрес кафка джейсон икс эм эль", "word boundaries and long terms")
        check(!processor.normalize("Источник https://example.org/a?q=1 и yandex.ru/jobs").contains("example"), "URLs removed")
        check(processor.normalize(" ").isEmpty, "empty paragraphs omitted")
        let long = String(repeating: "Длинное предложение про Kubernetes. ", count: 80)
        let chunks = processor.split(processor.normalize(long))
        check(chunks.count > 1 && chunks.allSatisfy { $0.count <= 1200 }, "bounded utterances")
        check(chunks.joined(separator: " ") == processor.normalize(long), "splitting preserves text")
        check(processor.split(String(repeating: "🙂", count: 1500)).allSatisfy { $0.count <= 1200 }, "Unicode long token does not break splitting")

        let sentence = String(repeating: "слово ", count: 130) + "завершено."
        check(processor.split(sentence) == [sentence], "sentence longer than old 600 limit stays intact")
        check(processor.split("Первое предложение. Второе предложение!").count == 2, "natural sentence utterances")
        let prosody = processor.fragments(from: SpeechTopic(id: "p", title: "", blocks: [
            .init(id: "h", text: "Заголовок", kind: "heading"),
            .init(id: "p", text: "Первое предложение. Второе предложение."),
            .init(id: "l", text: "Элемент", kind: "list")]))
        check(prosody.map(\.postDelay) == [0.45, 0.10, 0.30, 0.20], "semantic pauses")
        check(prosody[1].blockID == prosody[2].blockID, "sentences preserve block highlighting")
        let rates = SpeechReaderManager.speeds.map { SpeechReaderManager.speechRate(for: $0) }
        check(zip(rates, rates.dropFirst()).allSatisfy { $0 < $1 } && rates.last! <= AVSpeechUtteranceMaximumSpeechRate, "rates ordered and bounded")
        let suite = "SpeechTests." + UUID().uuidString
        let defaults = UserDefaults(suiteName: suite)!
        defer { defaults.removePersistentDomain(forName: suite) }
        let engine = FakeSpeech(), session = FakeSession()
        let reader = SpeechReaderManager(defaults: defaults, session: session, makeSynthesizer: { engine }, observeSystem: false)
        let topic = SpeechTopic(id: "t-1", title: "Тема", blocks: [
            .init(id: "p1", text: "Первый API блок."), .init(id: "p2", text: "Второй SQL блок."), .init(id: "p3", text: "Третий блок.")
        ])
        var highlights: [String?] = []
        reader.onHighlight = { _, block in highlights.append(block) }
        let cancelled = reader.beginLoading(id: topic.id, title: topic.title)
        reader.contextChanged(to: "t-2")
        reader.finishLoading(topic, request: cancelled)
        check(engine.utterances.isEmpty && reader.topicID == nil, "navigation discards pending extraction")
        let request = reader.beginLoading(id: topic.id, title: topic.title)
        reader.finishLoading(topic, request: request)
        check(reader.state == .playing && engine.utterances.count == 1 && session.active, "play creates one utterance")
        check(engine.utterances.last?.pitchMultiplier == 1 && engine.utterances.last?.preUtteranceDelay == 0 && engine.utterances.last?.postUtteranceDelay == 0.30, "utterance pitch and pauses")
        reader.play(); reader.play()
        check(engine.utterances.count == 1, "repeated play does not enqueue duplicates")
        reader.pause()
        check(reader.state == .paused && !session.active, "pause releases audio session")
        reader.play()
        check(reader.state == .playing && engine.utterances.count == 1, "resume continues current utterance")
        let old = engine.utterances.last!
        reader.setSpeed(1.5)
        check(reader.speed == 1.5 && defaults.double(forKey: "speech.speed") == 1.5 && engine.utterances.count == 2, "speed changes and persists")
        let source = AVSpeechSynthesizer()
        reader.speechSynthesizer(source, didFinish: old)
        reader.speechSynthesizer(source, didCancel: old)
        await callbacks()
        check(reader.currentIndex == 0 && reader.state == .playing, "stale callbacks cannot advance or pause new speech")
        reader.next()
        check(reader.currentIndex == 1 && engine.utterances.last?.speechString.contains("Второй") == true, "next block")
        reader.pause(); reader.previous()
        check(reader.currentIndex == 0 && reader.state == .paused, "previous while paused stays paused")
        reader.play()
        reader.interruptionBegan()
        check(reader.state == .paused && !session.active, "system interruption pauses")
        reader.interruptionEnded(shouldResume: true)
        check(reader.state == .playing, "system-permitted resume")
        reader.interruptionBegan(); reader.pause(); reader.interruptionEnded(shouldResume: true)
        check(reader.state == .paused, "user pause cancels automatic interruption resume")
        reader.play(); reader.next(); reader.next()
        let final = engine.utterances.last!
        reader.speechSynthesizer(source, didFinish: final)
        await callbacks()
        check(reader.state == .finished && !session.active && highlights.last! == nil, "topic completion stops audio and clears highlight")
        reader.play()
        check(reader.currentIndex == 0 && reader.state == .playing, "replay starts at beginning")
        let stopped = engine.utterances.last!
        reader.stop(); reader.speechSynthesizer(source, didFinish: stopped); await callbacks()
        check(reader.state == .idle && reader.currentIndex == 0 && !session.active, "stop ignores late finish")
        reader.play(); reader.contextChanged(to: "t-2")
        check(reader.state == .idle && reader.topicID == nil && reader.fragments.isEmpty, "topic change clears old content")
        reader.finishLoading(topic, request: reader.beginLoading(id: topic.id, title: topic.title))
        reader.contextChanged(to: topic.id, invalidate: true)
        check(reader.topicID == nil, "filter/visibility change invalidates speech snapshot")
        session.shouldFail = true
        reader.finishLoading(topic, request: reader.beginLoading(id: topic.id, title: topic.title))
        check(reader.state == .paused && reader.message != nil, "audio session failure is recoverable")
        session.shouldFail = false; reader.play()
        check(reader.state == .playing, "play retries after session failure")
        engine.pauseSucceeds = false; engine.resumeSucceeds = false
        for _ in 0..<20 { reader.pause(); reader.play() }
        check(reader.state == .playing, "rapid pause/resume fallback remains usable")
        reader.reset()
        check(reader.topicID == nil && reader.state == .idle, "reader cleanup")
        let restored = SpeechReaderManager(defaults: defaults, session: session, makeSynthesizer: { FakeSpeech() }, observeSystem: false)
        check(restored.speed == 1.5 && restored.state == .idle, "speed restores without automatic playback")
        if let candidate = reader.availableVoices.first {
            reader.finishLoading(topic, request: reader.beginLoading(id: topic.id, title: topic.title))
            reader.pause()
            reader.setVoice(candidate.identifier)
            check(defaults.string(forKey: "speech.voiceIdentifier") == candidate.identifier && reader.preferredVoiceID == candidate.identifier, "manual voice saved")
            check(reader.state == .paused, "voice change preserves pause")
            reader.setVoice(nil)
            check(defaults.string(forKey: "speech.voiceIdentifier") == nil, "automatic voice clears preference")
            reader.play()
        }
        defaults.set("missing.voice", forKey: "speech.voiceIdentifier")
        let fallback = SpeechReaderManager(defaults: defaults, session: session, makeSynthesizer: { FakeSpeech() }, observeSystem: false)
        check(fallback.preferredVoiceID == nil && !fallback.voiceName.isEmpty, "missing saved voice falls back automatically")
        print("PASS: SpeechTextProcessor and SpeechReaderManager")
    }
}
