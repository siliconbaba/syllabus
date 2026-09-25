import Foundation
import CryptoKit
import Darwin

func neuralFootprint()->UInt64 {
    var info=task_vm_info_data_t();var count=mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size/MemoryLayout<integer_t>.size)
    let result=withUnsafeMutablePointer(to:&info){p in p.withMemoryRebound(to:integer_t.self,capacity:Int(count)){task_info(mach_task_self_,task_flavor_t(TASK_VM_INFO),$0,&count)}}
    return result==KERN_SUCCESS ? info.phys_footprint:0
}
actor SileroWorker {
    private var preprocessor:SileroPreprocessor?
    private var synthesis:SileroSynthesisRuntime?
    private let technical=TechnicalSpeechNormalizer()
    private var observed:UInt64=0
    func prepare()throws {
        if synthesis != nil{return}
        let start=CFAbsoluteTimeGetCurrent()
        guard let root=Bundle.main.url(forResource:"SileroResources",withExtension:nil) else{throw SpeechEngineUnavailable()}
        guard let manifest=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("manifest.json"))) as? [String:Any] else{throw SpeechEngineUnavailable()}
        guard let files=manifest["files"] as? [String:[String:Any]],files.count==9 else{throw SpeechEngineUnavailable()}
        for (name,entry) in files {
            try Task.checkCancellation()
            let data=try Data(contentsOf:root.appendingPathComponent(name),options:.mappedIfSafe)
            let sha=SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined()
            guard sha==entry["sha256"] as? String,data.count==entry["bytes"] as? Int else{throw ResearchError("Resource integrity: \(name)")}
        }
        let pre=try SileroPreprocessor(root:root);try Task.checkCancellation()
        let synth=try SileroSynthesisRuntime(root:root);try Task.checkCancellation()
        preprocessor=pre;synthesis=synth;observed=neuralFootprint()
        #if DEBUG
        NSLog("Silero load %.3fs footprint=%llu",CFAbsoluteTimeGetCurrent()-start,observed)
        #endif
    }
    func render(_ text:String)throws->[Float] {
        try Task.checkCancellation();try prepare();let start=CFAbsoluteTimeGetCurrent()
        let spoken=try technical.normalize(text)
        try Task.checkCancellation();let prepared=try preprocessor!.prepare(spoken)
        try Task.checkCancellation();let result=try synthesis!.synthesize(prepared.tensors)
        try Task.checkCancellation();observed=max(observed,neuralFootprint())
        #if DEBUG
        let seconds=Double(result.audio.count)/48000,elapsed=CFAbsoluteTimeGetCurrent()-start
        NSLog("Silero render %.3fs audio=%.3fs RTF=%.3f footprint=%llu observed=%llu",elapsed,seconds,elapsed/max(seconds,0.001),neuralFootprint(),observed)
        #endif
        return result.audio
    }
    func unload(){preprocessor=nil;synthesis=nil}
}
