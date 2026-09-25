"""Independent host DSP; no Silero imports and no TorchScript waveform calls."""
import numpy as np

def reconstruct(spectral, window, n_fft=2400, hop=600):
    spectral=np.asarray(spectral,dtype=np.float32)
    log_mag,phase=np.split(spectral,2,axis=1)
    mag=np.minimum(np.exp(log_mag),np.float32(100))
    spec=mag*(np.cos(phase)+np.complex64(1j)*np.sin(phase))
    frames=np.fft.irfft(spec,n=n_fft,axis=1,norm='backward').astype(np.float32)
    frames*=np.asarray(window,dtype=np.float32)[None,:,None]
    count=frames.shape[2];length=(count-1)*hop+n_fft
    out=np.zeros((frames.shape[0],length),dtype=np.float32)
    envelope=np.zeros(length,dtype=np.float32)
    for t in range(count):
        start=t*hop
        out[:,start:start+n_fft]+=frames[:,:,t]
        envelope[start:start+n_fft]+=window*window
    pad=(n_fft-hop)//2
    out=out[:,pad:-pad];envelope=envelope[pad:-pad]
    if np.min(envelope)<=1e-11:raise ValueError('Invalid window envelope')
    return out/envelope

def metrics(ref,test):
    ref=np.asarray(ref).reshape(-1).astype(np.float64);test=np.asarray(test).reshape(-1).astype(np.float64)
    if ref.shape!=test.shape:return {'length_ref':len(ref),'length_test':len(test),'length_equal':False}
    d=test-ref;error=np.linalg.norm(d);signal=np.linalg.norm(ref)
    # RMS log-magnitude distance in dB, Hann 1024, hop 256, -100 dB relative floor.
    from numpy.lib.stride_tricks import sliding_window_view
    def spectrum(x):
        frames=sliding_window_view(x,1024)[::256]
        return np.abs(np.fft.rfft(frames*np.hanning(1024)))
    sr,st=spectrum(ref),spectrum(test);floor=max(sr.max()*1e-5,1e-12)
    lsd=np.sqrt(np.mean((20*np.log10(np.maximum(sr,floor))-20*np.log10(np.maximum(st,floor)))**2))
    return {'length_ref':len(ref),'length_test':len(test),'length_equal':True,'max_abs':float(abs(d).max()),'rmse':float(np.sqrt(np.mean(d*d))),'relative_l2':float(error/max(signal,1e-30)),'snr_db':float(20*np.log10(signal/error)) if error else 'inf','log_spectral_distance_db':float(lsd)}
