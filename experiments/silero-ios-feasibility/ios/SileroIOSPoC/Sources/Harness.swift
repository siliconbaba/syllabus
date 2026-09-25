import Foundation
enum TensorElement: Int32 { case float = 1, int64 = 7, bool = 9 }
import Darwin

struct TensorFile: Decodable { let file: String; let shape: [Int]; let dtype: String }
struct FixtureCase: Decodable {
    let id: String
    let inputs: [String: TensorFile]
    let reference: TensorFile
    let mac: TensorFile
    let durations: TensorFile
    let mac_spectral: TensorFile
    let intermediate: [String: TensorFile]
}
struct FixtureManifest: Decodable { let cases: [FixtureCase]; let window: TensorFile }
struct Tensor {
    let value: POCValue
    let shape: [Int]
    init(data: Data, dtype: TensorElement, shape: [Int]) throws {
        self.shape = shape
        value = try POCValue(data: data, elementType: dtype.rawValue, shape: shape.map { NSNumber(value: $0) })
    }
    init(_ floats: [Float], _ shape: [Int]) throws {
        try self.init(data: floats.withUnsafeBytes { Data($0) }, dtype: .float, shape: shape)
    }
    init(output: POCValue) throws { value = output; shape = output.shape.map(\.intValue) }
    func floats() throws -> [Float] {
        let data = value.data as NSData
        return Array(UnsafeBufferPointer(start: data.bytes.assumingMemoryBound(to: Float.self), count: data.length / 4))
    }
}

final class FixtureHarness {
    let root: URL
    let output: URL
    let manifest: FixtureManifest
    var sessions: [String: POCSession] = [:]
    var inputNames: [String: [String]] = [:]
    var initialization: [String: Double] = [:]
    let dsp: FixtureDSP
    let scaling: [String: Double]
    init() throws {
        root = Bundle.main.resourceURL!.appendingPathComponent("Fixtures")
        output = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("Results")
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        manifest = try JSONDecoder().decode(FixtureManifest.self, from: Data(contentsOf: root.appendingPathComponent("manifest.json")))
        let wd = try Data(contentsOf: root.appendingPathComponent(manifest.window.file))
        let window = wd.withUnsafeBytes { Array($0.bindMemory(to: Float.self)) }
        dsp = try FixtureDSP(window: window); scaling = try dsp.scalingProbe()
        for name in ["duration", "pitch", "encoder", "decoder", "spectral"] {
            // CPU EP is the default. No EP append calls, no custom operators.
            let start = CFAbsoluteTimeGetCurrent()
            sessions[name] = try POCSession(modelPath: root.appendingPathComponent(name + ".onnx").path, threads: 4)
            initialization[name] = CFAbsoluteTimeGetCurrent() - start
            inputNames[name] = sessions[name]!.inputNames
            print("SESSION \(name) \(initialization[name]!) seconds")
        }
    }
    func load(_ descriptor: TensorFile) throws -> Tensor {
        let type: TensorElement = descriptor.dtype == "int64" ? .int64 : .float
        return try Tensor(data: Data(contentsOf: root.appendingPathComponent(descriptor.file)), dtype: type, shape: descriptor.shape)
    }
    func floats(_ descriptor: TensorFile) throws -> [Float] {
        let data = try Data(contentsOf: root.appendingPathComponent(descriptor.file))
        return data.withUnsafeBytes { Array($0.bindMemory(to: Float.self)) }
    }
    func run(_ name: String, _ inputs: [String: Tensor]) throws -> Tensor {
        var values: [String: POCValue] = [:]
        for key in inputNames[name]! {
            guard let tensor = inputs[key] else { throw ResearchError("Missing input \(name).\(key)") }
            values[key] = tensor.value
        }
        let output = try sessions[name]!.run(withInputs: values)
        return try Tensor(output: output)
    }
    struct Synthesis {
        let audio:[Float];let durations:[Float];let tokens:Int;let frames:Int
        let shapes:[String:[Int]];let timings:[String:Double]
        let spectral:Tensor;let spectralValues:[Float];let log:Tensor;let pitch:[Float];let mel:Tensor
    }
    func synthesize(_ prepared:[String:Tensor]) throws -> Synthesis {
        var x=prepared
        let t = x["sequence"]!.shape[1]
        guard x["sequence"]!.shape == [1,t], try x["pitch_coefs"]!.floats().allSatisfy({ $0 == 1 }) else { throw ResearchError("Not baseline input") }
        let seqData = x["sequence"]!.value.data as Data
        let seq = seqData.withUnsafeBytes { Array($0.bindMemory(to: Int64.self)) }
        let mask = seq.map { UInt8($0 == 0 ? 1 : 0) }
        x["mask"] = try Tensor(data: Data(mask), dtype: .bool, shape: [1,t])
        var timings: [String: Double] = [:]
        var shapes: [String: [Int]] = [:]
        let start = CFAbsoluteTimeGetCurrent()
        func measured(_ name: String, _ inputs: [String: Tensor]) throws -> Tensor {
            let ts = CFAbsoluteTimeGetCurrent(); let out = try run(name, inputs)
            timings[name] = CFAbsoluteTimeGetCurrent() - ts; shapes[name] = out.shape
            return out
        }
        let log = try measured("duration", x)
        var durations = try log.floats()
        let rate = try x["durs_rate"]!.floats()
        let hostStart = CFAbsoluteTimeGetCurrent()
        for i in durations.indices { durations[i] = max(expf(durations[i]) - 1, 0).rounded(.toNearestOrEven) }
        durations[0] = min(durations[0],5)
        for i in durations.indices { durations[i] = (durations[i] / rate[i]).rounded(.toNearestOrEven) }
        durations[0] = min(durations[0],5); durations[t-1] = min(durations[t-1],7)
        durations[t-2] = 13; durations[t-3] = min(durations[t-3],13)
        timings["duration_host"] = CFAbsoluteTimeGetCurrent() - hostStart
        let rawPitch = try measured("pitch", x)
        var pitch = try rawPitch.floats()
        for i in pitch.indices where abs(pitch[i]) < 0.001 { pitch[i] = 0 }
        x["pitch"] = try Tensor(pitch, rawPitch.shape)
        let encoded = try measured("encoder", x)
        let encodedValues = try encoded.floats()
        let repeatStart = CFAbsoluteTimeGetCurrent()
        let channels = encoded.shape[2]
        let frames = durations.reduce(0) { $0 + Int(max($1,0) + 0.5) }
        var expanded = [Float](); expanded.reserveCapacity(frames * channels)
        for token in 0..<t {
            let repeats = Int(max(durations[token],0) + 0.5)
            for _ in 0..<repeats { expanded.append(contentsOf: encodedValues[(token*channels)..<((token+1)*channels)]) }
        }
        let expansion = try Tensor(expanded, [1,frames,channels])
        timings["repeat_expansion"] = CFAbsoluteTimeGetCurrent() - repeatStart
        let mel = try measured("decoder", ["expanded": expansion])
        let spectral = try measured("spectral", ["mel": mel])
        guard spectral.shape == [1,2402,frames] else { throw ResearchError("Spectral shape mismatch \(spectral.shape)") }
        let spectralValues = try spectral.floats()
        let dspStart = CFAbsoluteTimeGetCurrent()
        let audio = try dsp.reconstruct(spectralValues, frames: frames)
        timings["dsp"] = CFAbsoluteTimeGetCurrent() - dspStart
        timings["total"] = CFAbsoluteTimeGetCurrent() - start
        return Synthesis(audio:audio,durations:durations,tokens:t,frames:frames,shapes:shapes,timings:timings,spectral:spectral,spectralValues:spectralValues,log:log,pitch:pitch,mel:mel)
    }
    func runCase(_ fixture: FixtureCase, prepared: [String: Tensor]? = nil) throws -> [String: Any] {
        var x: [String: Tensor] = [:]
        if let prepared = prepared { x = prepared } else { for (key, file) in fixture.inputs { x[key] = try load(file) } }
        let result=try synthesize(x)
        let audio=result.audio,durations=result.durations,t=result.tokens,frames=result.frames
        let shapes=result.shapes,timings=result.timings,spectral=result.spectral,spectralValues=result.spectralValues
        let log=result.log,pitch=result.pitch,mel=result.mel
        let original = try floats(fixture.reference), mac = try floats(fixture.mac)
        let referenceDurations = try floats(fixture.durations)
        let macSpectral = try floats(fixture.mac_spectral)
        let isolatedDSP = try dsp.reconstruct(macSpectral, frames: frames)
        let dspMetrics = try difference(mac, isolatedDSP)
        let macMetrics = try difference(mac, audio), goldenMetrics = try difference(original, audio)
        let exactDurations = durations == referenceDurations
        let shapeEqual = fixture.mac_spectral.shape == spectral.shape
        let pass = exactDurations && shapeEqual && dspMetrics["relative_l2"]! < 1e-5 && macMetrics["relative_l2"]! < 0.001 && goldenMetrics["relative_l2"]! < 0.001
        var intermediate: [String: Any] = ["spectral": try difference(macSpectral, spectralValues)]
        for (key, value) in [("duration_log", try log.floats()), ("pitch", pitch), ("mel", try mel.floats())] {
            intermediate[key] = try difference(try floats(fixture.intermediate[key]!), value)
        }
        try audio.withUnsafeBytes { try Data($0).write(to: output.appendingPathComponent(fixture.id + ".f32"), options: .atomic) }
        // Make WAV only after numerical regression passes; no autoplay.
        if pass { try writeWAV(audio, to: output.appendingPathComponent(fixture.id + ".wav")) }
        return ["id":fixture.id,"pass":pass,"tokens":t,"frames":frames,"samples":audio.count,"durations_equal":exactDurations,"durations":durations,"shapes_equal":shapeEqual,"shapes":shapes,"vs_mac":macMetrics,"vs_golden":goldenMetrics,"dsp_only_vs_mac":dspMetrics,"intermediate_vs_mac":intermediate,"timings_seconds":timings,"process_footprint_bytes":footprint()]
    }
    func all(_ progress: (String) -> Void) throws -> [String: Any] {
        var cases: [[String: Any]] = []
        for fixture in manifest.cases {
            progress(fixture.id)
            let result = try autoreleasepool { try runCase(fixture) }
            cases.append(result); print("FIXTURE \(fixture.id) pass=\(result["pass"]!)")
        }
        let report: [String: Any] = ["ort_version":String(cString: POCORTVersion()),"provider":"CPU","sample_rate":48000,"initialization_seconds":initialization,"scaling":scaling,"cases":cases,"all_pass":cases.allSatisfy { $0["pass"] as? Bool == true },"device":ProcessInfo.processInfo.operatingSystemVersionString,"footprint_bytes":footprint()]
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted,.sortedKeys]).write(to: output.appendingPathComponent("report.json"), options: .atomic)
        return report
    }
}

func footprint() -> UInt64 {
    var info = task_vm_info_data_t()
    var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<integer_t>.size)
    let result = withUnsafeMutablePointer(to: &info) { p in
        p.withMemoryRebound(to: integer_t.self, capacity: Int(count)) { task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count) }
    }
    return result == KERN_SUCCESS ? info.phys_footprint : 0
}
func writeWAV(_ samples: [Float], to url: URL) throws {
    var pcm = samples.map { Int16((min(max($0,-1),1) * 32767).rounded(.towardZero)) }
    var data = Data()
    func text(_ s: String) { data.append(s.data(using: .ascii)!) }
    func u32(_ x: UInt32) { var x=x.littleEndian; withUnsafeBytes(of:&x) { data.append(contentsOf:$0) } }
    func u16(_ x: UInt16) { var x=x.littleEndian; withUnsafeBytes(of:&x) { data.append(contentsOf:$0) } }
    text("RIFF");u32(UInt32(36+pcm.count*2));text("WAVEfmt ");u32(16);u16(1);u16(1);u32(48000);u32(96000);u16(2);u16(16);text("data");u32(UInt32(pcm.count*2))
    pcm.withUnsafeMutableBytes { data.append(contentsOf:$0) }; try data.write(to:url,options:.atomic)
}
