from pathlib import Path
import importlib.util
import tempfile
import subprocess
import plistlib
import json
import hashlib

root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('packager', root/'scripts/package_sidestore.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results={}
with tempfile.TemporaryDirectory() as td:
 p=Path(td);app=p/'Fixture.app';app.mkdir()
 # Reproduce exact redirection order at build-sidestore.sh's package step.
 output=app/'bad-location.ipa';report=Path(str(output)+'.json')
 with report.open('w') as sink:
  r=subprocess.run(['python3',str(root/'scripts/package_sidestore.py'),'--app',str(app),'--output',str(output)],stdout=sink,stderr=subprocess.PIPE,text=True)
 results['reportFailure']={'packagerExit':r.returncode,'sourceModifiedByWrapperReport':report.exists(),'emptyReportBytes':report.stat().st_size,'retryBlockedByExistingReport':report.exists(),'pythonError':r.stderr.strip().splitlines()[-1]}
 info={'CFBundleName':'Original','CFBundleDisplayName':'Назва базова','CFBundleIdentifier':'com.example.fixture'}
 (app/'Info.plist').write_bytes(plistlib.dumps(info))
 ru=app/'ru.lproj';ru.mkdir();strings=ru/'InfoPlist.strings'
 strings.write_bytes(plistlib.dumps({'CFBundleDisplayName':'Русское локализованное имя','Other':'Сохранить'}))
 m.localize_name(app,'InteractiveBook')
 results['localization']={'originalRussianDisplayName':'Русское локализованное имя','afterRussianDisplayName':plistlib.loads(strings.read_bytes())['CFBundleDisplayName'],'otherKey':plistlib.loads(strings.read_bytes())['Other']}
print(json.dumps(results,ensure_ascii=False,indent=2))
