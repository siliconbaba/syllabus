import Foundation
import Darwin
enum TensorElement: Int32 { case float = 1, int64 = 7, bool = 9 }
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

// Numerical path copied from the verified fixture runtime; no fixture IO in production.
final class SileroSynthesisRuntime {
    var sessions:[String:POCSession]=[:]
    var inputNames:[String:[String]]=[:]
    let dsp:FixtureDSP
    init(root:URL)throws {
        let wd=try Data(contentsOf:root.appendingPathComponent("window.bin"))
        dsp=try FixtureDSP(window:wd.withUnsafeBytes{Array($0.bindMemory(to:Float.self))})
        for name in ["duration","pitch","encoder","decoder","spectral"] {
            try Task.checkCancellation()
            sessions[name]=try POCSession(modelPath:root.appendingPathComponent(name+".onnx").path,threads:4)
            inputNames[name]=sessions[name]!.inputNames
        }
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
            try Task.checkCancellation()
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
}
