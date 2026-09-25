import Foundation
import Accelerate

struct ResearchError: Error, CustomStringConvertible {
    let description: String
    init(_ text: String) { description = text }
}

final class FixtureDSP {
    let window: [Float]
    let setup: kiss_fftr_cfg
    let n = 2400, hop = 600, pad = 900
    init(window: [Float]) throws {
        guard window.count == 2400, let plan = kiss_fftr_alloc(2400, 1, nil, nil) else { throw ResearchError("FFT setup failed") }
        self.window = window; setup = plan
    }
    deinit { free(UnsafeMutableRawPointer(setup)) }
    func inverse(_ spectrum: [kiss_fft_cpx]) -> [Float] {
        var samples = [Float](repeating: 0, count: n)
        spectrum.withUnsafeBufferPointer { ptr in kiss_fftri(setup, ptr.baseAddress!, &samples) }
        // KissFFT inverse is unnormalized: NumPy norm=backward requires exactly 1/N.
        for i in samples.indices { samples[i] /= Float(n) }
        return samples
    }
    func scalingProbe() throws -> [String: Double] {
        var bins = [kiss_fft_cpx](repeating: kiss_fft_cpx(r: 0, i: 0), count: 1201)
        bins[0].r = 1
        let dc = inverse(bins)
        var dcError: Double = 0
        for value in dc { dcError = max(dcError, abs(Double(value) - 1.0 / 2400)) }
        bins[0].r = 0; bins[1200].r = 1
        let ny = inverse(bins)
        var nyError: Double = 0
        for i in ny.indices { nyError = max(nyError, abs(Double(ny[i]) - (i % 2 == 0 ? 1.0 : -1.0) / 2400)) }
        bins[1200].r = 0; bins[37].r = 1
        let cosine = inverse(bins)
        var cosineError: Double = 0
        for i in cosine.indices { cosineError = max(cosineError, abs(Double(cosine[i]) - 2 * cos(2 * .pi * 37 * Double(i) / 2400) / 2400)) }
        guard max(dcError, max(nyError, cosineError)) < 1e-8 else { throw ResearchError("FFT scaling regression") }
        let split = vDSP_DFT_zop_CreateSetup(nil, 2400, .INVERSE)
        let interleaved = vDSP_DFT_Interleaved_CreateSetup(nil, 2400, .INVERSE, vDSP_DFT_RealtoComplex(rawValue: false)!)
        let real = vDSP_DFT_Interleaved_CreateSetup(nil, 1200, .INVERSE, vDSP_DFT_RealtoComplex(rawValue: true)!)
        let availability: [String: Double] = ["accelerate_split_2400": split == nil ? 0 : 1, "accelerate_interleaved_2400": interleaved == nil ? 0 : 1, "accelerate_real_1200": real == nil ? 0 : 1]
        if let split = split { vDSP_DFT_DestroySetup(split) }
        if let interleaved = interleaved { vDSP_DFT_Interleaved_DestroySetup(interleaved) }
        if let real = real { vDSP_DFT_Interleaved_DestroySetup(real) }
        return availability.merging(["dc_max_abs": dcError, "nyquist_max_abs": nyError, "cosine_max_abs": cosineError, "inverse_scale": 1.0 / 2400]) { _, new in new }
    }
    func reconstruct(_ spectral: [Float], frames: Int) throws -> [Float] {
        guard frames > 0, spectral.count == 2402 * frames else { throw ResearchError("Spectral shape mismatch") }
        let count = (frames - 1) * hop + n
        var audio = [Float](repeating: 0, count: count)
        var envelope = [Float](repeating: 0, count: count)
        var bins = [kiss_fft_cpx](repeating: kiss_fft_cpx(r: 0, i: 0), count: 1201)
        for frame in 0..<frames {
            for k in 0..<1201 {
                let magnitude = min(expf(spectral[k * frames + frame]), 100)
                let phase = spectral[(k + 1201) * frames + frame]
                bins[k] = kiss_fft_cpx(r: magnitude * cosf(phase), i: magnitude * sinf(phase))
            }
            // irfft ignores imaginary components of the DC and Nyquist bins.
            bins[0].i = 0; bins[1200].i = 0
            let block = inverse(bins)
            let start = frame * hop
            for i in 0..<n {
                audio[start + i] += block[i] * window[i]
                envelope[start + i] += window[i] * window[i]
            }
        }
        var result = [Float](repeating: 0, count: count - 2 * pad)
        for i in result.indices {
            guard envelope[i + pad] > 1e-11 else { throw ResearchError("Invalid window envelope") }
            result[i] = audio[i + pad] / envelope[i + pad]
        }
        guard result.count == 600 * frames else { throw ResearchError("Waveform length mismatch") }
        return result
    }
}

func difference(_ reference: [Float], _ actual: [Float]) throws -> [String: Double] {
    guard reference.count == actual.count else { throw ResearchError("Comparison length mismatch: \(reference.count) vs \(actual.count)") }
    var maximum = 0.0, error = 0.0, signal = 0.0
    for i in reference.indices {
        let a = Double(reference[i]), b = Double(actual[i])
        guard a.isFinite, b.isFinite else { throw ResearchError("Non-finite sample") }
        let d = b - a; maximum = max(maximum, abs(d)); error += d * d; signal += a * a
    }
    return ["samples": Double(actual.count), "max_abs": maximum, "rmse": sqrt(error / Double(actual.count)), "relative_l2": sqrt(error / max(signal, 1e-30)), "snr_db": error == 0 ? 999 : 10 * log10(signal / error)]
}
