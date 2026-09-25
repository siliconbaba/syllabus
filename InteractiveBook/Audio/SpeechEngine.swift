import AVFoundation
import Foundation

enum SpeechEngineKind:String,CaseIterable {case system,neural
    var label:String {self == .system ? "Системный":"Нейросетевой"}
}
struct SpeechRequest {
    let id:UUID
    let fragment:SpeechFragment
    let offset:Int
    let speed:Double
    let voiceIdentifier:String?
}
enum SpeechEngineEvent {
    case started(UUID), finished(UUID), progress(UUID,Int), failed(UUID,Error)
}
@MainActor protocol SpeechEngine:AnyObject {
    var onEvent:((SpeechEngineEvent)->Void)? {get set}
    var requiresPreparation:Bool {get}
    func prepare() async throws
    func speak(_ request:SpeechRequest,next:SpeechRequest?)
    func pause()
    func resume()->Bool
    func setSpeed(_ value:Double)
    func stop()
    func shutdown()
}
struct SpeechEngineUnavailable:Error {}
@MainActor final class UnavailableSpeechEngine:SpeechEngine {
    var onEvent:((SpeechEngineEvent)->Void)?
    var requiresPreparation:Bool {true}
    func prepare()async throws{throw SpeechEngineUnavailable()}
    func speak(_ request:SpeechRequest,next:SpeechRequest?){onEvent?(.failed(request.id,SpeechEngineUnavailable()))}
    func pause(){};func resume()->Bool{false};func setSpeed(_ value:Double){};func stop(){};func shutdown(){}
}
