import Foundation
import AVFoundation

@MainActor final class TestEngine:SpeechEngine {
    var onEvent:((SpeechEngineEvent)->Void)?
    var requiresPreparation:Bool
    var requests:[SpeechRequest]=[]
    var ahead:[SpeechRequest?]=[]
    var paused=false,stopped=false,shut=false,failPreparation=false
    var active:SpeechRequest?
    var waiter:CheckedContinuation<Void,Error>?
    init(cold:Bool=false){requiresPreparation=cold}
    func prepare()async throws{if failPreparation{throw SpeechEngineUnavailable()};if requiresPreparation{try await withCheckedThrowingContinuation{waiter=$0}}}
    func ready(){requiresPreparation=false;waiter?.resume();waiter=nil}
    func speak(_ r:SpeechRequest,next:SpeechRequest?){requests.append(r);ahead.append(next);active=r;stopped=false;paused=false}
    func began(){if let r=active{onEvent?(.started(r.id))}}
    func ended(){if let r=active{onEvent?(.finished(r.id))}}
    func pause(){paused=true}
    func resume()->Bool{guard active != nil else{return false};paused=false;return true}
    func setSpeed(_ value:Double){}
    func stop(){stopped=true;active=nil}
    func shutdown(){stop();shut=true}
}
struct TestSession:SpeechAudioSession{func activate()throws{};func deactivate(){}}
@main struct EngineTests {
 @MainActor static func main()async {
    func check(_ ok:@autoclosure()->Bool,_ label:String){if !ok(){print("FAIL: \(label)");exit(1)};print("PASS: \(label)")}
    func tick()async{try? await Task.sleep(nanoseconds:30_000_000)}
    let suite="EngineTests."+UUID().uuidString;let defaults=UserDefaults(suiteName:suite)!;defer{defaults.removePersistentDomain(forName:suite)}
    var created:[SpeechEngineKind:[TestEngine]]=[:]
    let factory:(SpeechEngineKind)->SpeechEngine={kind in let e=TestEngine(cold:kind == .neural);created[kind,default:[]].append(e);return e}
    let reader=SpeechReaderManager(defaults:defaults,session:TestSession(),observeSystem:false,makeEngine:factory)
    let topic=SpeechTopic(id:"a",title:"Technical",blocks:(0..<6).map{.init(id:"b\($0)",text:"API вернул HTTP 500. Блок \($0).")})
    check(reader.engineKind == .system,"default system engine")
    reader.finishLoading(topic,request:reader.beginLoading(id:topic.id,title:topic.title));let system=created[.system]!.last!;system.began()
    reader.setEngine(.neural);let neural=created[.neural]!.last!;await tick()
    check(system.shut && reader.engineKind == .neural && reader.state == .loading,"Apple to Silero stops previous and lazy prepares")
    check(defaults.string(forKey:"speech.engine")=="neural","engine selection persistence")
    neural.ready();await tick();check(neural.requests.count==1,"prepared neural starts exactly once")
    check(neural.requests[0].fragment.text.contains("API"),"neural queue retains visible source")
    let technical=try! TechnicalSpeechNormalizer().normalize(neural.requests[0].fragment.text)
    check(technical=="эй пи ай вернул эйч ти ти пи пятьсот.","technical normalization before neural preprocessing")
    let old=neural.requests[0];reader.stop();neural.onEvent?(.started(old.id));neural.onEvent?(.finished(old.id))
    check(reader.state == .idle && reader.currentIndex==0,"Stop during generation rejects late start and finish")
    reader.play();let pending=neural.requests.last!;reader.next();let next=neural.requests.last!
    neural.onEvent?(.started(pending.id));neural.onEvent?(.finished(pending.id))
    check(reader.currentIndex==1 && next.id != pending.id,"Next during generation cancels stale result")
    neural.began();reader.pause();check(reader.state == .paused && neural.paused,"PCM Pause delegates without moving queue")
    let count=neural.requests.count;reader.play();check(neural.requests.count==count && !neural.paused,"PCM Resume does not duplicate synthesis")
    reader.play();reader.play();check(neural.requests.count==count,"no duplicate play")
    reader.interruptionBegan();reader.stop();reader.interruptionEnded(shouldResume:true)
    check(reader.state == .idle,"interruption must not resurrect stopped session")
    reader.play();neural.began();reader.interruptionBegan();reader.interruptionEnded(shouldResume:true)
    check(reader.state == .playing,"system permitted interruption resume")
    let before=neural.requests.count;reader.setSpeed(2);check(neural.requests.count==before,"neural tempo does not resynthesize")
    reader.stop();reader.play();neural.began()
    var ordered=true
    while reader.currentIndex+1<reader.fragments.count{
        let expected=neural.ahead.last!!;neural.ended()
        ordered = ordered && neural.requests.last!.id==expected.id
        neural.began()
    }
    neural.ended();check(ordered && reader.state == .finished,"one-ahead request ordering and end-of-topic")
    reader.play();let stale=neural.requests.last!;reader.contextChanged(to:"b");neural.onEvent?(.started(stale.id))
    check(reader.topicID==nil && reader.state == .idle,"topic change invalidates pending playback")
    reader.finishLoading(topic,request:reader.beginLoading(id:topic.id,title:topic.title));neural.began();reader.pause();reader.setEngine(.system)
    check(neural.shut && reader.state == .paused,"Silero to Apple preserves pause and releases neural engine")
    let system2=created[.system]!.last!;reader.play();system2.began();reader.setEngine(.neural);await tick()
    let cold=created[.neural]!.last!;reader.stop();cold.ready();await tick()
    check(cold.requests.isEmpty && reader.state == .idle,"Stop during model preparation rejects completion")
    reader.setEngine(.system);reader.play();created[.system]!.last!.began()
    let missingFactory:(SpeechEngineKind)->SpeechEngine={kind in if kind == .neural{let e=TestEngine(cold:true);e.failPreparation=true;return e};return TestEngine()}
    let fallback=SpeechReaderManager(defaults:defaults,session:TestSession(),observeSystem:false,makeEngine:missingFactory)
    fallback.finishLoading(topic,request:fallback.beginLoading(id:topic.id,title:topic.title));fallback.setEngine(.neural);await tick()
    check(fallback.engineKind == .system && fallback.message != nil && fallback.currentIndex==0,"missing neural resources fallback retries same logical block")
    reader.setEngine(.neural);await tick();let mem=created[.neural]!.last!;mem.ready();await tick();mem.began()
    reader.memoryPressure();check(mem.shut && reader.state == .paused,"memory pressure cancels work and releases neural resources")
    reader.contextChanged(to:topic.id,invalidate:true);check(reader.topicID==nil,"filter invalidation stops both engine modes")
    let restored=SpeechReaderManager(defaults:defaults,session:TestSession(),observeSystem:false,makeEngine:factory)
    check(restored.engineKind == .neural && restored.state == .idle,"selection restores without automatic model loading or reading")
    for kind in SpeechEngineKind.allCases {
        let isolated = UserDefaults(suiteName:"FromBlock."+UUID().uuidString)!
        isolated.set(kind.rawValue,forKey:"speech.engine")
        let playback = TestEngine()
        let from = SpeechReaderManager(defaults:isolated,session:TestSession(),observeSystem:false,makeEngine:{_ in playback})
        let blocks = [SpeechTopic.Block(id:"first",text:"Первый.",kind:"paragraph"),SpeechTopic.Block(id:"middle",text:"Середина.",kind:"paragraph"),SpeechTopic.Block(id:"list",text:"Пункт.",kind:"list"),SpeechTopic.Block(id:"last",text:"Последний.",kind:"paragraph")]
        let selectedTopic = SpeechTopic(id:"t-10-1",title:"Тема",blocks:blocks)
        var highlight:String?
        from.onHighlight={_, block in highlight=block}
        for (index, block) in blocks.enumerated() {
            from.finishLoading(selectedTopic,request:from.beginLoading(id:selectedTopic.id,title:selectedTopic.title),startBlockID:block.id)
            playback.began()
            check(from.currentIndex==index && playback.requests.last?.fragment.blockID==block.id && highlight==block.id,"\(kind): start block \(block.id), highlight")
            let stale=playback.requests.last!
            from.pause()
            from.finishLoading(selectedTopic,request:from.beginLoading(id:selectedTopic.id,title:selectedTopic.title),startBlockID:block.id)
            playback.onEvent?(.finished(stale.id));playback.onEvent?(.started(stale.id))
            check(from.currentIndex==index,"\(kind): restart from pause cancels old generation/prebuffer")
            playback.began()
        }
        playback.ended();check(from.state == .finished,"\(kind): selected last block completes topic")
        from.finishLoading(selectedTopic,request:from.beginLoading(id:selectedTopic.id,title:selectedTopic.title),startBlockID:"missing")
        check(from.state == .idle && from.message != nil,"\(kind): missing block explicit error")
    }
    print("PASS: production engine state transitions")
 }
}
struct ResearchError:Error{let description:String;init(_ text:String){description=text}}
