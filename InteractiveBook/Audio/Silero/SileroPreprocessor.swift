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
