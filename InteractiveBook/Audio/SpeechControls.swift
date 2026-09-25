import SwiftUI

struct SpeechControls: View {
    @ObservedObject var reader: SpeechReaderManager

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(reader.title.isEmpty ? "Аудиочтение" : reader.title)
                        .font(.caption.weight(.semibold)).lineLimit(1)
                    Text(reader.statusText).font(.caption2).foregroundStyle(.secondary)
                        .accessibilityIdentifier("speech.status")
                }
                Spacer(minLength: 0)
                Button { reader.reset() } label: {
                    Image(systemName: "xmark").frame(width: 44, height: 44)
                }.accessibilityLabel("Закрыть аудиочтение")
            }
            if let message = reader.message {
                Text(message).font(.caption2).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
            }
            HStack(spacing: 10) {
                control("Предыдущий блок", "backward.end.fill", enabled: reader.hasPrevious) { reader.previous() }
                Button {
                    if reader.state == .playing { reader.pause() } else { reader.play() }
                } label: {
                    Group {
                        if reader.state == .loading { ProgressView() }
                        else { Image(systemName: reader.state == .playing ? "pause.fill" : "play.fill") }
                    }.frame(width: 48, height: 44)
                }
                .disabled(reader.state == .loading)
                .accessibilityLabel(reader.state == .playing ? "Пауза" : reader.state == .paused ? "Продолжить чтение" : "Слушать")
                .accessibilityIdentifier("speech.playPause")
                control("Остановить чтение", "stop.fill", enabled: reader.state != .idle) { reader.stop() }
                control("Следующий блок", "forward.end.fill", enabled: reader.hasNext) { reader.next() }
                Spacer(minLength: 0)
                Menu {
                    Menu("Озвучивание") {
                        ForEach(SpeechEngineKind.allCases,id: \.rawValue) { kind in
                            Button { reader.setEngine(kind) } label: {
                                if reader.engineKind == kind { Label(kind.label,systemImage:"checkmark") }
                                else { Text(kind.label) }
                            }
                        }
                    }
                    if reader.engineKind == .system { Menu("Голос: " + reader.voiceName) {
                        Button { reader.setVoice(nil) } label: {
                            if reader.preferredVoiceID == nil { Label("Автоматически", systemImage: "checkmark") }
                            else { Text("Автоматически") }
                        }
                        ForEach(reader.availableVoices, id: \.identifier) { voice in
                            Button { reader.setVoice(voice.identifier) } label: {
                                let label = voice.name + " — " + SpeechReaderManager.qualityLabel(voice)
                                if reader.preferredVoiceID == voice.identifier { Label(label, systemImage: "checkmark") }
                                else { Text(label) }
                            }
                        }
                    }
                    }
                    ForEach(SpeechReaderManager.speeds, id: \.self) { speed in
                        Button { reader.setSpeed(speed) } label: {
                            if reader.speed == speed { Label(speedLabel(speed), systemImage: "checkmark") }
                            else { Text(speedLabel(speed)) }
                        }
                    }
                } label: {
                    Text(speedLabel(reader.speed)).font(.subheadline.monospacedDigit()).frame(minWidth: 44, minHeight: 44)
                }
                .accessibilityLabel("Скорость чтения")
                .accessibilityValue(speedLabel(reader.speed))
            }
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(.regularMaterial)
        .overlay(alignment: .top) { Divider() }
        .tint(Color(red: 0.78, green: 0.06, blue: 0.18))
    }

    private func speedLabel(_ speed: Double) -> String { String(format: "%.1f×", speed) }
    private func control(_ label: String, _ icon: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) { Image(systemName: icon).frame(width: 44, height: 44) }
            .disabled(!enabled).accessibilityLabel(label)
    }
}
