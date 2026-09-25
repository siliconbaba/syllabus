import Foundation
struct TechnicalExample:Decodable {let id:String;let category:String;let source:String;let expected:String;let audio:Bool}
final class TechnicalHarness {
    let root:URL;let output:URL;let examples:[TechnicalExample]
    init()throws {
        root=Bundle.main.resourceURL!.appendingPathComponent("Preprocessing")
        examples=try JSONDecoder().decode([TechnicalExample].self,from:Data(contentsOf:root.appendingPathComponent("technical-corpus.json")))
        output=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0].appendingPathComponent("TechnicalResults")
        try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
    }
    func run(_ progress:(String)->Void)throws->[String:Any] {
        let normalizer=TechnicalSpeechNormalizer();let data=try SileroData(root:root);let sileroNormalizer=SileroNormalizer(data:data)
        var cases:[[String:Any]]=[];var spoken:[String:String]=[:]
        for item in examples {
            let start=CFAbsoluteTimeGetCurrent();let text=try normalizer.normalize(item.source);let elapsed=CFAbsoluteTimeGetCurrent()-start
            let normalized=try sileroNormalizer.normalize(text)
            let exact=text==item.expected;let survives=normalized==text.lowercased()
            let pass=exact && survives
            cases.append(["id":item.id,"category":item.category,"source":item.source,"expected":item.expected,"actual":text,"after_silero_whitelist":normalized,"expected_equal":exact,"whitelist_survives":survives,"pass":pass,"normalization_seconds":elapsed])
            spoken[item.id]=text
        }
        // Measure string-only work for a theme-sized batch, excluding models and disk.
        let topic=examples.map(\.source).joined(separator:" ");var topicTimes:[Double]=[]
        for _ in 0..<5 {let t=CFAbsoluteTimeGetCurrent();_ = try normalizer.normalize(topic);topicTimes.append(CFAbsoluteTimeGetCurrent()-t)}
        var report:[String:Any]=["cases":cases,"text_pass":cases.allSatisfy{$0["pass"] as! Bool},"topic_characters":topic.count,"topic_seconds":topicTimes,"inherited_terms":SpeechTextProcessor.pronunciations.count,"additional_terms":TechnicalLexicon.additions.count,"total_terms":TechnicalLexicon.entries.count]
        func save()throws{try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"),options:.atomic)}
        try save();guard cases.allSatisfy({$0["pass"] as! Bool}) else{throw ResearchError("Technical text mismatch: TechnicalResults/report.json")}
        let preprocessor=try SileroPreprocessor(root:root);let engine=try FixtureHarness();var audioRows:[[String:Any]]=[]
        for item in examples where item.audio {
            progress(item.source)
            let row=try autoreleasepool {()->[String:Any] in
                let start=CFAbsoluteTimeGetCurrent();let prepared=try preprocessor.prepare(spoken[item.id]!);let result=try engine.synthesize(prepared.tensors)
                guard !result.audio.isEmpty,result.audio.allSatisfy(\.isFinite),result.audio.count==600*result.frames else{throw ResearchError("Invalid technical waveform")}
                try result.audio.withUnsafeBytes{try Data($0).write(to:output.appendingPathComponent(item.id+".f32"))}
                try writeWAV(result.audio,to:output.appendingPathComponent(item.id+".wav"))
                return ["id":item.id,"source":item.source,"speakable":spoken[item.id]!,"stressed":prepared.stages["stressed"]!,"samples":result.audio.count,"seconds":Double(result.audio.count)/48000,"tokens":result.tokens,"frames":result.frames,"shapes":result.shapes,"synthesis_seconds":result.timings,"total_seconds":CFAbsoluteTimeGetCurrent()-start,"finite":true,"peak":result.audio.map{abs($0)}.max()!,"pass":true]
            }
            audioRows.append(row)
        }
        report["audio"]=audioRows;report["all_pass"]=audioRows.count==examples.filter(\.audio).count;try save();return report
    }
}
