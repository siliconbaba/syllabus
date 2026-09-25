import AVFoundation
import Foundation

/// One current PCM packet + at most one next packet. Manager owns the logical queue.
@MainActor final class SileroSpeechEngine:SpeechEngine {
    var onEvent:((SpeechEngineEvent)->Void)?
    private(set) var requiresPreparation=true
    private let worker=SileroWorker()
    private let audio=AVAudioEngine()
    private let player=AVAudioPlayerNode()
    private let timePitch=AVAudioUnitTimePitch()
    private let format=AVAudioFormat(standardFormatWithSampleRate:48000,channels:1)!
    private var epoch=UUID()
    private var current:SpeechRequest?
    private var nextRequest:SpeechRequest?
    private var jobs:[UUID:Task<Void,Never>]=[:]
    private var ready:[UUID:AVAudioPCMBuffer]=[:]
    private var failures:[UUID:Error]=[:]
    private var activeBuffer:AVAudioPCMBuffer?
    private var paused=false
    init(){audio.attach(player);audio.attach(timePitch);audio.connect(player,to:timePitch,format:format);audio.connect(timePitch,to:audio.mainMixerNode,format:format);timePitch.pitch=0}
    func prepare()async throws{try await worker.prepare();try Task.checkCancellation();requiresPreparation=false}
    func speak(_ request:SpeechRequest,next:SpeechRequest?) {
        current=request;nextRequest=next;paused=false;timePitch.rate=Float(request.speed)
        if let failure=failures.removeValue(forKey:request.id){onEvent?(.failed(request.id,failure));return}
        if ready[request.id] != nil{playReady();if let next=next{generate(next)}}
        else{generate(request)}
    }
    private func generate(_ request:SpeechRequest) {
        guard jobs[request.id]==nil,ready[request.id]==nil,failures[request.id]==nil else{return}
        let token=epoch;let worker=self.worker
        jobs[request.id]=Task { [weak self] in
            do {
                let samples=try await worker.render(request.fragment.text);try Task.checkCancellation()
                guard let self=self,self.epoch==token else{return}
                let silence=Int(48000*request.fragment.postDelay)
                guard samples.count+silence<Int(UInt32.max),let buffer=AVAudioPCMBuffer(pcmFormat:self.format,frameCapacity:AVAudioFrameCount(samples.count+silence)) else{throw SpeechEngineUnavailable()}
                buffer.frameLength=buffer.frameCapacity
                samples.withUnsafeBufferPointer{buffer.floatChannelData![0].update(from:$0.baseAddress!,count:samples.count)}
                buffer.floatChannelData![0].advanced(by:samples.count).initialize(repeating:0,count:silence)
                self.jobs[request.id]=nil;self.ready[request.id]=buffer
                #if DEBUG
                NSLog("Silero buffer ready %@ current=%@",request.id.uuidString,self.current?.id.uuidString ?? "none")
                #endif
                if self.current?.id==request.id{self.playReady();if let next=self.nextRequest{self.generate(next)}}
            } catch {
                guard let self=self,self.epoch==token,!Task.isCancelled else{return}
                self.jobs[request.id]=nil
                if self.current?.id==request.id{self.onEvent?(.failed(request.id,error))}
                else{self.failures[request.id]=error} // Never skip a failed prefetched fragment.
            }
        }
    }
    private func playReady(){
        guard !paused,activeBuffer==nil,let request=current,let buffer=ready.removeValue(forKey:request.id) else{return}
        do {
            if !audio.isRunning{try audio.start()}
            activeBuffer=buffer;let token=epoch
            player.scheduleBuffer(buffer,completionCallbackType:.dataPlayedBack){[weak self] _ in Task{@MainActor in
                guard let self=self,self.epoch==token,self.current?.id==request.id else{return}
                self.activeBuffer=nil
                // A completion already queued when Pause arrived must wait for Resume.
                if self.paused{self.finishedWhilePaused=request.id;return}
                self.complete(request.id)
            }}
            player.play();onEvent?(.started(request.id))
            #if DEBUG
            NSLog("Silero PCM start %@ aheadReady=%@",request.id.uuidString,nextRequest.flatMap{ready[$0.id]} == nil ? "false":"true")
            #endif
        }catch{onEvent?(.failed(request.id,error))}
    }
    private var finishedWhilePaused:UUID?
    private func complete(_ id:UUID){current=nil;onEvent?(.finished(id))}
    func pause(){paused=true;player.pause();audio.pause()}
    func resume()->Bool{
        guard let request=current else{return false};paused=false
        if let id=finishedWhilePaused{finishedWhilePaused=nil;complete(id);return true}
        do{if activeBuffer != nil{if !audio.isRunning{try audio.start()};player.play();onEvent?(.started(request.id))}else{playReady()};return true}
        catch{onEvent?(.failed(request.id,error));return true}
    }
    func setSpeed(_ value:Double){timePitch.rate=Float(value)}
    func stop(){epoch=UUID();jobs.values.forEach{$0.cancel()};jobs.removeAll();ready.removeAll();failures.removeAll();current=nil;nextRequest=nil;finishedWhilePaused=nil;activeBuffer=nil;paused=false;player.stop();audio.stop()}
    func shutdown(){stop();requiresPreparation=true;let worker=self.worker;Task{await worker.unload()}}
}
