from pathlib import Path
import json,hashlib,importlib.util,tempfile,subprocess,zipfile,plistlib,stat
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('packager',root/'scripts/package_sidestore.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
results={}
with tempfile.TemporaryDirectory() as td:
 p=Path(td);app=p/'Fixture.app';app.mkdir();bad=app/'bad.ipa'
 r=subprocess.run(['bash',str(root/'scripts/build-sidestore.sh'),str(bad)],capture_output=True,text=True)
 results['wrapperSourceContainedPath']={'exit':r.returncode,'error':r.stderr.strip(),'noSourceFilesCreated':list(app.iterdir())==[]}
 assert r.returncode!=0 and not list(app.iterdir())
 (app/'Info.plist').write_bytes(plistlib.dumps({'CFBundleDisplayName':'Назва базова','CFBundleName':'Original'}));ru=app/'ru.lproj';ru.mkdir();localized=ru/'InfoPlist.strings'
 localized.write_text('"CFBundleDisplayName" = "Русское имя";\n"Other" = "Сохранить";\n')
 m.localize_name(app,'InteractiveBook');result=plistlib.loads(localized.read_bytes());assert result=={'CFBundleDisplayName':'Русское имя','Other':'Сохранить'}
 results['openStepLocalizationPreserved']='PASS'
 source=root/'build/sidestore-release/Build/Products/Release-iphoneos/InteractiveBook.app';before=m.inspect_bundle(source,allow_signed_frameworks=True)
 vendor=source/'Frameworks/onnxruntime.framework';v=subprocess.run(['/usr/bin/codesign','--verify','--strict',str(vendor)],capture_output=True,text=True)
 results['sourceVendorSigningVerification']={'exit':v.returncode,'output':v.stderr.strip(),'note':'Presence of vendor signature does not imply validity; final IPA must be unsigned for SideStore.'}
 ipa=root/'agent-artifacts/releases/checkpoint-100-2026-10-26/InteractiveBook-checkpoint-100.ipa'
 sourceHashes={str(f.relative_to(source)):m.digest(f) for f in source.rglob('*') if f.is_file()}
 with zipfile.ZipFile(ipa) as z:
  assert z.testzip() is None
  unpack=p/'unpack';z.extractall(unpack)
  for e in z.infolist():(unpack/e.filename).chmod(stat.S_IMODE(e.external_attr>>16))
  app=unpack/'Payload/InteractiveBook.app';after=m.inspect_bundle(app)
  assert after['CFBundleIdentifier']==before['CFBundleIdentifier']
  assert after['CFBundleDisplayName']=='InteractiveBook'
  new={str(f.relative_to(app)):m.digest(f) for f in app.rglob('*') if f.is_file()}
  changed=[k for k in sourceHashes if k in new and sourceHashes[k]!=new[k]]
  removed=[k for k in sourceHashes if k not in new];added=[k for k in new if k not in sourceHashes]
  assert set(changed)=={'Info.plist','Frameworks/onnxruntime.framework/onnxruntime'},changed
  assert all('/_CodeSignature/' in k for k in removed),removed
  assert added==['ru.lproj/InfoPlist.strings'],added
  bank=json.loads((app/'TrainerContent/cases.json').read_text());assert len(bank['cases'])==100
  results['realUnsignedDeviceIPA']={'status':'PASS','changedFiles':changed,'removedSignatureFiles':removed,'added':added,'cases':100,'sha256':m.digest(ipa),'sourceBankBytesPreserved':True,'mainExecutableBytesPreserved':True}
 assert sourceHashes=={str(f.relative_to(source)):m.digest(f) for f in source.rglob('*') if f.is_file()}
 results['sourceReadOnlyDuringReview']=True
results['currentSourceHashes']={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in ['scripts/package_sidestore.py','scripts/build-sidestore.sh','Tests/test_sidestore_packaging.py']}
(out/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False,indent=2))
