#import "ORTBridge.h"
#include <onnxruntime/onnxruntime_cxx_api.h>
#include <vector>

static void fail(NSError** error, const std::exception& e) {
    if (error) *error=[NSError errorWithDomain:@"SileroPoC.ORT" code:1 userInfo:@{NSLocalizedDescriptionKey:@(e.what())}];
}
@interface POCValue () {
@public
    Ort::Value* _value;
    NSData* _backing;
}
- (instancetype)initWithValue:(Ort::Value&&)value;
@end
@implementation POCValue
- (instancetype)initWithData:(NSData*)data elementType:(int32_t)type shape:(NSArray<NSNumber*>*)shape error:(NSError**)error {
    if (!(self=[super init])) return nil;
    try {
        _backing=[data copy];
        std::vector<int64_t> dimensions;
        for (NSNumber* n in shape) dimensions.push_back(n.longLongValue);
        auto memory=Ort::MemoryInfo::CreateCpu(OrtArenaAllocator,OrtMemTypeDefault);
        _value=new Ort::Value(Ort::Value::CreateTensor(memory,const_cast<void*>(_backing.bytes),_backing.length,dimensions.data(),dimensions.size(),static_cast<ONNXTensorElementDataType>(type)));
    } catch(const std::exception& e) { fail(error,e);return nil; }
    return self;
}
- (instancetype)initWithValue:(Ort::Value&&)value {
    if ((self=[super init])) _value=new Ort::Value(std::move(value));return self;
}
- (void)dealloc { delete _value; }
- (NSArray<NSNumber*>*)shape {
    NSMutableArray* result=[NSMutableArray array];
    for(auto n:_value->GetTensorTypeAndShapeInfo().GetShape()) [result addObject:@(n)];
    return result;
}
- (NSData*)data {
    auto info=_value->GetTensorTypeAndShapeInfo();
    size_t width=info.GetElementType()==ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64 ? 8 : info.GetElementType()==ONNX_TENSOR_ELEMENT_DATA_TYPE_BOOL ? 1 : 4;
    return [NSData dataWithBytes:_value->GetTensorRawData() length:info.GetElementCount()*width];
}
@end
@interface POCSession () {
    Ort::Env* _env;
    Ort::Session* _session;
    NSArray<NSString*>* _inputNames;
}
@end
@implementation POCSession
- (instancetype)initWithModelPath:(NSString*)path threads:(int32_t)threads error:(NSError**)error {
    if (!(self=[super init])) return nil;
    try {
        _env=new Ort::Env(ORT_LOGGING_LEVEL_WARNING,"SileroIOSPoC");
        Ort::SessionOptions options;
        options.SetIntraOpNumThreads(threads);options.SetInterOpNumThreads(1);options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
        // No provider append calls: default CPU EP only.
        _session=new Ort::Session(*_env,path.fileSystemRepresentation,options);
        Ort::AllocatorWithDefaultOptions allocator;
        NSMutableArray* names=[NSMutableArray array];
        for(size_t i=0;i<_session->GetInputCount();i++) { auto n=_session->GetInputNameAllocated(i,allocator);[names addObject:@(n.get())]; }
        _inputNames=names;
    } catch(const std::exception& e) { fail(error,e);return nil; }
    return self;
}
- (void)dealloc { delete _session;delete _env; }
- (NSArray<NSString*>*)inputNames { return _inputNames; }
- (POCValue*)runWithInputs:(NSDictionary<NSString*,POCValue*>*)inputs error:(NSError**)error {
    try {
        std::vector<const char*> names; std::vector<Ort::Value> values;
        for(NSString* name in _inputNames) {
            POCValue* input=inputs[name]; if(!input) throw std::runtime_error("Missing tensor input");
            names.push_back(name.UTF8String);
            // Borrow a view, retain dictionary owners for entire synchronous Run.
            auto shape=input->_value->GetTensorTypeAndShapeInfo().GetShape();
            auto info=input->_value->GetTensorTypeAndShapeInfo();
            size_t width=info.GetElementType()==ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64 ? 8 : info.GetElementType()==ONNX_TENSOR_ELEMENT_DATA_TYPE_BOOL ? 1 : 4;
            auto memory=Ort::MemoryInfo::CreateCpu(OrtArenaAllocator,OrtMemTypeDefault);
            values.push_back(Ort::Value::CreateTensor(memory,input->_value->GetTensorMutableRawData(),info.GetElementCount()*width,shape.data(),shape.size(),info.GetElementType()));
        }
        const char* outputs[]={"output"};
        auto result=_session->Run(Ort::RunOptions{nullptr},names.data(),values.data(),values.size(),outputs,1);
        return [[POCValue alloc] initWithValue:std::move(result[0])];
    } catch(const std::exception& e) { fail(error,e);return nil; }
}
@end
const char* POCORTVersion(void) { return OrtGetApiBase()->GetVersionString(); }
