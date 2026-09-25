import Accelerate
print("split", vDSP_DFT_zop_CreateSetup(nil,2400,.INVERSE) as Any)
print("interleaved", vDSP_DFT_Interleaved_CreateSetup(nil,2400,.INVERSE,vDSP_DFT_RealtoComplex(rawValue: false)!) as Any)
print("real", vDSP_DFT_Interleaved_CreateSetup(nil,1200,.INVERSE,vDSP_DFT_RealtoComplex(rawValue: true)!) as Any)
