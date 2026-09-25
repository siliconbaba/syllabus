import AVFoundation
import Foundation

protocol SpeechSynthesizing:AnyObject {
    var delegate:AVSpeechSynthesizerDelegate? {get set}
    func speak(_ utterance:AVSpeechUtterance)
    func stopSpeaking(at boundary:AVSpeechBoundary)->Bool
    func pauseSpeaking(at boundary:AVSpeechBoundary)->Bool
    func continueSpeaking()->Bool
}
extension AVSpeechSynthesizer:SpeechSynthesizing {}

@MainActor final class AppleSpeechEngine:NSObject,SpeechEngine,AVSpeechSynthesizerDelegate {
    var onEvent:((SpeechEngineEvent)->Void)?
    let requiresPreparation=false
    private let synthesizer:SpeechSynthesizing
    private var active:AVSpeechUtterance?
    private var request:SpeechRequest?
    private var playing=false
    init(makeSynthesizer:()->SpeechSynthesizing){synthesizer=makeSynthesizer();super.init();synthesizer.delegate=self
        #if os(iOS)
        (synthesizer as? AVSpeechSynthesizer)?.usesApplicationAudioSession=true
        #endif
    }
    deinit {synthesizer.delegate=nil;_ = synthesizer.stopSpeaking(at:.immediate)}
    func prepare()async throws{}
    func speak(_ request:SpeechRequest,next:SpeechRequest?) {
        stop();self.request=request;playing=true
        let text=request.fragment.text as NSString
        let offset=min(max(0,request.offset),max(0,text.length-1))
        let utterance=AVSpeechUtterance(string:text.substring(from:offset))
        utterance.voice=request.voiceIdentifier.flatMap(AVSpeechSynthesisVoice.init(identifier:))
        utterance.rate=Self.rate(for:request.speed);utterance.pitchMultiplier=1
        utterance.preUtteranceDelay=0;utterance.postUtteranceDelay=request.fragment.postDelay
        active=utterance;onEvent?(.started(request.id));synthesizer.speak(utterance)
    }
    static func rate(for speed:Double)->Float{min(AVSpeechUtteranceMaximumSpeechRate,max(AVSpeechUtteranceMinimumSpeechRate,0.46*Float(speed)))}
    func pause(){playing=false;if !synthesizer.pauseSpeaking(at:.immediate){active=nil;_ = synthesizer.stopSpeaking(at:.immediate)}}
    func resume()->Bool {guard active != nil else{return false};playing=true;return synthesizer.continueSpeaking()}
    func setSpeed(_ value:Double){} // Manager restarts system speech at last reported UTF-16 offset.
    func stop(){active=nil;request=nil;playing=false;_ = synthesizer.stopSpeaking(at:.immediate)}
    func shutdown(){stop();synthesizer.delegate=nil}
    nonisolated func speechSynthesizer(_ synthesizer:AVSpeechSynthesizer,didFinish utterance:AVSpeechUtterance){Task{@MainActor [weak self] in
        guard let self=self,self.active === utterance,self.playing,let r=self.request else{return}
        self.active=nil;self.onEvent?(.finished(r.id))
    }}
    nonisolated func speechSynthesizer(_ synthesizer:AVSpeechSynthesizer,didCancel utterance:AVSpeechUtterance){Task{@MainActor [weak self] in
        guard let self=self,self.active === utterance,let r=self.request else{return}
        self.active=nil;self.onEvent?(.failed(r.id,SpeechEngineUnavailable()))
    }}
    nonisolated func speechSynthesizer(_ synthesizer:AVSpeechSynthesizer,willSpeakRangeOfSpeechString range:NSRange,utterance:AVSpeechUtterance){Task{@MainActor [weak self] in
        guard let self=self,self.active === utterance,self.playing,let r=self.request else{return}
        self.onEvent?(.progress(r.id,r.offset+range.location))
    }}
}
