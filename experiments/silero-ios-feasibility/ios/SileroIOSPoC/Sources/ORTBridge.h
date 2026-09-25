#import <Foundation/Foundation.h>
NS_ASSUME_NONNULL_BEGIN
@interface POCValue : NSObject
- (nullable instancetype)initWithData:(NSData*)data elementType:(int32_t)type shape:(NSArray<NSNumber*>*)shape error:(NSError**)error;
@property(nonatomic,readonly) NSArray<NSNumber*>* shape;
@property(nonatomic,readonly) NSData* data;
@end
@interface POCSession : NSObject
- (nullable instancetype)initWithModelPath:(NSString*)path threads:(int32_t)threads error:(NSError**)error;
- (nullable POCValue*)runWithInputs:(NSDictionary<NSString*,POCValue*>*)inputs error:(NSError**)error;
@property(nonatomic,readonly) NSArray<NSString*>* inputNames;
@end
#ifdef __cplusplus
extern "C" {
#endif
const char* POCORTVersion(void);
#ifdef __cplusplus
}
#endif
NS_ASSUME_NONNULL_END
