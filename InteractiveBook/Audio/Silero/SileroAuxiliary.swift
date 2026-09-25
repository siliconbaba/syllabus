import Foundation
func integerTensor(_ values:[Int64],_ shape:[Int])throws->Tensor {try Tensor(data:values.withUnsafeBytes{Data($0)},dtype:.int64,shape:shape)}
func auxRun(_ session:POCSession,_ inputs:[String:Tensor])throws->Tensor {try Tensor(output:session.run(withInputs:inputs.mapValues(\.value)))}
struct HomoResult {let text:String;let stages:[String:Any];let logits:[Float]}
final class SileroHomographProcessor {
    let data:SileroData;let session:POCSession
    init(data:SileroData,root:URL)throws {self.data=data;session=try POCSession(modelPath:root.appendingPathComponent("homograph.onnx").path,threads:4)}
    func process(_ sentence:String)throws->HomoResult {
        let re=try NSRegularExpression(pattern:#"(?i)(?=.*[а-яё])[а-яё+]+"#)
        var tags:[[Any]]=[];var starts:[Int64]=[],ends:[Int64]=[];var batches:[[Int64]]=[];var pieces:[[String]]=[]
        var replacements:[(Int,Int,String)]=[];let tokenizer=SileroTokenizer(data:data);let original=scalars(sentence)
        for m in re.matches(in:sentence,range:NSRange(sentence.startIndex...,in:sentence)) {
            let range=Range(m.range,in:sentence)!;let word=String(sentence[range]);let start=sentence[..<range.lowerBound].unicodeScalars.count;let end=start+word.unicodeScalars.count
            let homo=data.homodict[word.lowercased()] != nil
            let mark=original[..<start].joined()+" [HOMO] "+word+" [/HOMO] "+original[end...].joined()
            tags.append([start,end,word,homo,homo ? mark as Any : NSNull()])
            if homo {
                let wp=tokenizer.wordpieces(mark);let ids=tokenizer.bertIDs(wp);pieces.append(wp);batches.append(ids)
                starts.append(Int64(ids.firstIndex(of:Int64(data.vocab["[HOMO]"]!))!));ends.append(Int64(ids.firstIndex(of:Int64(data.vocab["[/HOMO]"]!))!));replacements.append((start,end,word))
            }
        }
        let width=batches.map(\.count).max() ?? 0
        batches=batches.map{$0+Array(repeating:0,count:width-$0.count)}
        var logits:[Float]=[];var text=original;var offset=0
        if !batches.isEmpty {
            let result=try auxRun(session,["input_ids":integerTensor(batches.flatMap{$0},[batches.count,width]),"homo_start_ids":integerTensor(starts,[starts.count]),"homo_end_ids":integerTensor(ends,[ends.count])]);logits=try result.floats()
            for (i,item) in replacements.enumerated(){
                // sigmoid then round-to-even: an exact 0 logit chooses class 0.
                let probability:Float=1/(1+expf(-logits[i]));let prediction=Int(probability.rounded(.toNearestOrEven))
                let variant=data.homodict[item.2.lowercased()]!.sorted()[prediction];let chars=scalars(variant);let stress=chars.firstIndex(of:"+")!;var word=chars.filter{$0 != "+"}
                let source=scalars(item.2);word=zip(source,word).map{a,b in a == a.lowercased() ? b.lowercased():b.uppercased()}
                word.insert("+",at:stress);text.replaceSubrange((item.0+offset)..<(item.1+offset),with:word);offset+=1
            }
        }
        return HomoResult(text:text.joined(),stages:["homograph_tags":tags,"wordpieces":pieces,"homo_ids":batches,"homo_starts":starts,"homo_ends":ends,"homograph_resolved":text.joined()],logits:logits)
    }
}
struct StressResult {let text:String;let stages:[String:Any];let logits:[Float]}
final class SileroStressProcessor {
    let data:SileroData;let session:POCSession;let vowels=Set(scalars("аоуыэиеяёю"))
    init(data:SileroData,root:URL)throws{self.data=data;session=try POCSession(modelPath:root.appendingPathComponent("accent.onnx").path,threads:4)}
    func tokenize(_ s:String)->([String],[String],[Bool]) {
        var raw:[String]=[],clean:[String]=[],mask:[Bool]=[]
        for word in splitRE(#"[\s.,!?;:<>=()/\\]+"#,s,capture:true) {
            let parts=word.components(separatedBy:"-")
            for (i,part) in parts.enumerated(){
                let token=part+(i<parts.count-1 ? "-":"");let normalized=sub("[^А-Яа-яёЁ]",token.lowercased(),"")
                raw.append(token);clean.append(normalized);mask.append(!normalized.isEmpty && (parts.count==1 || i<parts.count-1 || part != "то"))
            }
        }
        return(raw,clean,mask)
    }
    func ngrams(_ words:[String])->([Int64],[Int64]) {
        var indices:[Int64]=[],offsets:[Int64]=[]
        for word in words {
            offsets.append(Int64(indices.count));let bytes=Array(("<"+word+">").utf8);var subindices:[Int64]=[]
            // TorchScript string slicing is UTF-8 byte based; preserve ngram ordering.
            for n in 1...(word.utf8.count+3) where n<=bytes.count {
                for j in 0...(bytes.count-n){if let gram=String(bytes:bytes[j..<j+n],encoding:.utf8),let id=data.ngrams[gram]{subindices.append(Int64(id))}}
            }
            if subindices.isEmpty{subindices=[Int64(data.ngrams["UNK"]!)]};indices+=subindices
        }
        return(indices,offsets)
    }
    func prediction(_ logits:ArraySlice<Float>)->(Int,Float){
        let values=Array(logits);let maximum=values.max()!;let index=values.firstIndex(of:maximum)!
        let exps=values.map{expf($0-maximum)};return(index,exps[index]/exps.reduce(0,+))
    }
    func process(_ sentence:String)throws->StressResult {
        let(raw,clean,mask)=tokenize(sentence);let(indices,offsets)=ngrams(clean)
        let result=try auxRun(session,["indices":integerTensor(indices,[indices.count]),"offsets":integerTensor(offsets,[offsets.count])]);let logits=try result.floats();var output:[String]=[]
        guard result.shape == [clean.count,17] else{throw ResearchError("Accent logits shape")}
        for i in raw.indices {
            var chars=scalars(raw[i]);let lower=scalars(raw[i].lowercased());let word=clean[i];let haveStress=lower.contains("+"),haveYo=lower.contains("ё")
            if !mask[i] || (haveStress && haveYo){output.append(raw[i]);continue}
            if !haveStress && haveYo {
                var shift=0;for p in lower.indices where lower[p]=="ё"{chars.insert("+",at:p+shift);shift+=1};output.append(chars.joined());continue
            }
            if let exception=data.exceptions[word] {
                let stress=exception[0],yo=exception[1]
                if haveStress {
                    let positions=chars.indices.filter{chars[$0]=="+"};chars=chars.filter{$0 != "+"}
                    if yo != -1 && positions.contains(yo+1){chars[yo]=chars[yo] == chars[yo].lowercased() ? "ё":"Ё"}
                    for p in positions{chars.insert("+",at:p)}
                } else {
                    if yo != -1 {chars[yo]=chars[yo] == chars[yo].lowercased() ? "ё":"Ё"};chars.insert("+",at:stress)
                }
                output.append(chars.joined());continue
            }
            let(stressIndex,stressProb)=prediction(logits[(i*17)..<(i*17+10)]);let(yoIndex,yoProb)=prediction(logits[(i*17+10)..<(i*17+17)])
            var stressed=[stressIndex];var setStress=stressProb>0.5 && !haveStress
            if haveStress{stressed=raw[i].lowercased().components(separatedBy:"+").map{scalars($0).filter{vowels.contains($0)}.count}}
            let vowelPositions=lower.indices.filter{vowels.contains(lower[$0])};let yePositions=lower.indices.filter{lower[$0]=="е"}
            var positions=stressed.filter{$0<vowelPositions.count}.map{vowelPositions[$0]}
            if vowelPositions.isEmpty{output.append(raw[i]);continue}
            if yoIndex>0 && yoIndex-1<yePositions.count && yoProb>0.5 {
                let p=yePositions[yoIndex-1];if positions.contains(p){chars[p]=chars[p] == chars[p].lowercased() ? "ё":"Ё"}
            }
            if vowelPositions.count==1{positions=[vowelPositions[0]];setStress=true}
            if !haveStress && setStress{for (shift,p) in positions.enumerated(){chars.insert("+",at:p+shift)}}
            output.append(chars.joined())
        }
        let text=output.joined()
        return StressResult(text:text,stages:["stress_raw":raw,"stress_clean":clean,"stress_mask":mask,"ngram_indices":indices,"ngram_offsets":offsets,"stressed":text,"final_text":text],logits:logits)
    }
}
