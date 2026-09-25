import Foundation
struct PreparedText {let tensors:[String:Tensor];let stages:[String:Any];let homoLogits:[Float];let accentLogits:[Float]}
final class SileroPreprocessor {
    let data:SileroData;let normalizer:SileroNormalizer;let homographs:SileroHomographProcessor;let stress:SileroStressProcessor;let tokenizer:SileroTokenizer;let questions:SileroQuestionClassifier
    init(root:URL)throws {
        data=try SileroData(root:root);normalizer=SileroNormalizer(data:data);tokenizer=SileroTokenizer(data:data);questions=SileroQuestionClassifier(data:data)
        homographs=try SileroHomographProcessor(data:data,root:root);stress=try SileroStressProcessor(data:data,root:root)
    }
    // Golden outputs are deliberately absent from this API.
    func prepare(_ text:String,speaker:String="xenia")throws->PreparedText {
        guard let speakerID=(data.values["speaker_ids"] as! [String:Int])[speaker] else{throw ResearchError("Unknown speaker")}
        let normalized=try normalizer.normalize(text);let homo=try homographs.process(normalized);let accented=try stress.process(homo.text)
        let characters=try tokenizer.characters(accented.text);let seq=try tokenizer.sequence(accented.text);let classification=questions.classify(text);let types=questions.typeIDs(text,classification,seq.count);let ones=[Float](repeating:1,count:seq.count)
        var stages:[String:Any]=["normalized":normalized,"character_ids":characters,"classification":classification,"sequence":[seq],"type_ids":[types],"speaker_ids":[speakerID],"durs_rate":[ones],"pitch_coefs":[ones]]
        stages.merge(homo.stages){_,b in b};stages.merge(accented.stages){_,b in b}
        let tensors:[String:Tensor]=try ["sequence":integerTensor(seq,[1,seq.count]),"type_ids":integerTensor(types,[1,seq.count]),"speaker_ids":integerTensor([Int64(speakerID)],[1]),"durs_rate":Tensor(ones,[1,seq.count]),"pitch_coefs":Tensor(ones,[1,seq.count])]
        return PreparedText(tensors:tensors,stages:stages,homoLogits:homo.logits,accentLogits:accented.logits)
    }
}
final class PreprocessingHarness {
    let root:URL;let output:URL;let preprocessor:SileroPreprocessor;let golden:[[String:Any]]
    init()throws {
        root=Bundle.main.resourceURL!.appendingPathComponent("Preprocessing")
        output=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0].appendingPathComponent("PreprocessingResults")
        try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
        preprocessor=try SileroPreprocessor(root:root)
        golden=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("golden.json"))) as! [[String:Any]]
    }
    func json(_ x:Any)throws->Data {try JSONSerialization.data(withJSONObject:x,options:[.sortedKeys,.fragmentsAllowed])}
    func run(_ progress:(String)->Void)throws->[String:Any] {
        var rows:[[String:Any]]=[];var prepared:[String:PreparedText]=[:]
        for reference in golden {
            let id=reference["id"] as! String;progress("preprocessing "+id)
            let result=try preprocessor.prepare(reference["text"] as! String);var checks:[String:Bool]=[:];var mismatches:[String:Any]=[:]
            for (key,value) in result.stages {
                let equal=try json(value)==json(reference[key]!);checks[key]=equal
                if !equal{mismatches[key]=["expected":reference[key]!,"actual":value]}
            }
            let referenceHomo=(reference["homo_logits"] as! [[NSNumber]]).flatMap{$0}.map(\.floatValue)
            let referenceAccent=(reference["accent_logits"] as! [[NSNumber]]).flatMap{$0}.map(\.floatValue)
            var metrics:[String:Any]=["accent":try difference(referenceAccent,result.accentLogits)]
            if !referenceHomo.isEmpty{metrics["homograph"]=try difference(referenceHomo,result.homoLogits)}
            let shapes=result.tensors.mapValues(\.shape)
            let sequenceLength=(reference["sequence"] as! [[Int]])[0].count
            let shapePass=shapes == ["sequence":[1,sequenceLength],"type_ids":[1,sequenceLength],"speaker_ids":[1],"durs_rate":[1,sequenceLength],"pitch_coefs":[1,sequenceLength]]
            checks["tensor_shapes"]=shapePass
            let pass=checks.values.allSatisfy{$0};rows.append(["id":id,"pass":pass,"checks":checks,"mismatches":mismatches,"auxiliary_metrics":metrics,"shapes":shapes,"actual_stages":result.stages])
            if !id.hasPrefix("extra_"){prepared[id]=result}
        }
        var report:[String:Any]=["cases":rows,"preprocessing_pass":rows.allSatisfy{$0["pass"] as! Bool},"ort_version":String(cString:POCORTVersion())]
        try json(report).write(to:output.appendingPathComponent("preprocessing.json"),options:.atomic)
        guard rows.allSatisfy({$0["pass"] as! Bool}) else{throw ResearchError("Preprocessing mismatch: see PreprocessingResults/preprocessing.json")}
        // Only after all stages pass, run the proven synthesizer on Swift-produced tensors.
        let synthesis=try FixtureHarness();var waveforms:[[String:Any]]=[]
        for fixture in synthesis.manifest.cases {
            progress("raw → waveform "+fixture.id)
            let result=try synthesis.runCase(fixture,prepared:prepared[fixture.id]!.tensors);waveforms.append(result)
        }
        report["waveforms"]=waveforms;report["all_pass"]=waveforms.allSatisfy{$0["pass"] as! Bool}
        try json(report).write(to:output.appendingPathComponent("preprocessing.json"),options:.atomic)
        return report
    }
}
