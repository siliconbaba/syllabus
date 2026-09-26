from pathlib import Path
R=Path(__file__).resolve().parent
files=['App.swift','TechnicalLexicon.swift','EnglishPronunciation.swift','TechnicalNumbers.swift','TechnicalSpeechNormalizer.swift','TechnicalHarness.swift','SileroTextRules.swift','SileroAuxiliary.swift','SileroPreprocessor.swift','Harness.swift','DSP.swift','ORTBridge.mm','kiss_fft.c','kiss_fftr.c']
objs={};counter=0
def add(value):
 global counter
 counter+=1;k=f'{counter:024X}';objs[k]=value;return k
refs=[];builds=[]
for name in files:
 ref=add('{isa=PBXFileReference; lastKnownFileType='+('sourcecode.swift' if name.endswith('.swift') else 'sourcecode.cpp.objcpp' if name.endswith('.mm') else 'sourcecode.c.c')+'; path="SileroIOSPoC/'+('Sources/' if name.endswith(('.swift','.mm')) else 'Vendor/')+name+'"; sourceTree="<group>";}');refs.append(ref);builds.append(add('{isa=PBXBuildFile; fileRef='+ref+';}'))
sharedRef=add('{isa=PBXFileReference; lastKnownFileType=sourcecode.swift; path="../../../InteractiveBook/Audio/SpeechTextProcessor.swift"; sourceTree="<group>";}');refs.append(sharedRef);builds.append(add('{isa=PBXBuildFile; fileRef='+sharedRef+';}'))
resource=add('{isa=PBXFileReference; lastKnownFileType=folder; path="SileroIOSPoC/Fixtures"; sourceTree="<group>";}');rb=add('{isa=PBXBuildFile; fileRef='+resource+';}')
preResource=add('{isa=PBXFileReference; lastKnownFileType=folder; path="SileroIOSPoC/Preprocessing"; sourceTree="<group>";}');preBuild=add('{isa=PBXBuildFile; fileRef='+preResource+';}')
product=add('{isa=PBXFileReference; explicitFileType=wrapper.application; path=SileroIOSPoC.app; sourceTree=BUILT_PRODUCTS_DIR;}')
package=add('{isa=XCRemoteSwiftPackageReference; repositoryURL="https://github.com/microsoft/onnxruntime-swift-package-manager"; requirement={kind=exactVersion; version=1.24.2;};}')
dep=add('{isa=XCSwiftPackageProductDependency; package='+package+'; productName=onnxruntime;}');pb=add('{isa=PBXBuildFile; productRef='+dep+';}')
sources=add('{isa=PBXSourcesBuildPhase; buildActionMask=2147483647; files=('+','.join(builds)+',); runOnlyForDeploymentPostprocessing=0;}')
resources=add('{isa=PBXResourcesBuildPhase; buildActionMask=2147483647; files=('+rb+','+preBuild+',); runOnlyForDeploymentPostprocessing=0;}')
frameworks=add('{isa=PBXFrameworksBuildPhase; buildActionMask=2147483647; files=('+pb+',); runOnlyForDeploymentPostprocessing=0;}')
group=add('{isa=PBXGroup; children=('+','.join(refs+[resource,preResource,product])+',); sourceTree="<group>";}')
base='IPHONEOS_DEPLOYMENT_TARGET=16.0; SDKROOT=iphoneos; SWIFT_VERSION=5.0; CLANG_ENABLE_MODULES=YES; CLANG_ENABLE_OBJC_ARC=YES; CLANG_CXX_LANGUAGE_STANDARD="c++17";'
app='PRODUCT_BUNDLE_IDENTIFIER=ai.research.SileroIOSPoC; PRODUCT_NAME="$(TARGET_NAME)"; GENERATE_INFOPLIST_FILE=YES; INFOPLIST_KEY_UILaunchScreen_Generation=YES; INFOPLIST_KEY_UIApplicationSceneManifest_Generation=YES; INFOPLIST_KEY_CFBundleDisplayName="Silero Fixture PoC"; TARGETED_DEVICE_FAMILY=1; CODE_SIGN_STYLE=Automatic; SWIFT_OBJC_BRIDGING_HEADER="SileroIOSPoC/Sources/Bridge.h"; HEADER_SEARCH_PATHS="$(SRCROOT)/SileroIOSPoC/Vendor"; SWIFT_OPTIMIZATION_LEVEL="-O"; GCC_OPTIMIZATION_LEVEL=2;'
def configs(settings):
 a=add('{isa=XCBuildConfiguration; buildSettings={'+settings+'}; name=Debug;}');b=add('{isa=XCBuildConfiguration; buildSettings={'+settings+'}; name=Release;}');return add('{isa=XCConfigurationList; buildConfigurations=('+a+','+b+',); defaultConfigurationIsVisible=0; defaultConfigurationName=Debug;}')
pc=configs(base);tc=configs(app)
target=add('{isa=PBXNativeTarget; buildConfigurationList='+tc+'; buildPhases=('+','.join([sources,frameworks,resources])+',); buildRules=(); dependencies=(); name=SileroIOSPoC; productName=SileroIOSPoC; productReference='+product+'; productType="com.apple.product-type.application"; packageProductDependencies=('+dep+',);}')
project=add('{isa=PBXProject; attributes={LastUpgradeCheck=1600;}; buildConfigurationList='+pc+'; compatibilityVersion="Xcode 14.0"; developmentRegion=en; knownRegions=(en,Base,); mainGroup='+group+'; projectDirPath=""; projectRoot=""; targets=('+target+',); packageReferences=('+package+',);}')
(R/'SileroIOSPoC.xcodeproj/project.pbxproj').write_text('// !$*UTF8*$!\n{archiveVersion=1;classes={};objectVersion=56;objects={\n'+'\n'.join(k+' = '+v+';' for k,v in objs.items())+'\n};rootObject='+project+';}')
(R/'SileroIOSPoC.xcodeproj/xcshareddata/xcschemes/SileroIOSPoC.xcscheme').write_text(f'''<?xml version="1.0" encoding="UTF-8"?><Scheme LastUpgradeVersion="1600" version="1.3"><BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{target}" BuildableName="SileroIOSPoC.app" BlueprintName="SileroIOSPoC" ReferencedContainer="container:SileroIOSPoC.xcodeproj"/></BuildActionEntry></BuildActionEntries></BuildAction><LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{target}" BuildableName="SileroIOSPoC.app" BlueprintName="SileroIOSPoC" ReferencedContainer="container:SileroIOSPoC.xcodeproj"/></BuildableProductRunnable></LaunchAction></Scheme>''')
