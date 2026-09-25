"""Fetch the pinned official artifact and extract source for read-only inspection."""
from pathlib import Path
import hashlib, urllib.request, zipfile, json
R=Path(__file__).resolve().parent
URL='https://models.silero.ai/models/tts/ru/v5_5_ru.pt'
SHA='50081637b602126ee06cb3bc8a744d25651d2da149ee8864b9a379bfdd934437'
a=R/'artifacts';a.mkdir(exist_ok=True);(R/'reports').mkdir(exist_ok=True)
p=a/'v5_5_ru.pt'
if not p.exists():urllib.request.urlretrieve(URL,p)
actual=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
if actual!=SHA:raise RuntimeError(f'Model changed: expected {SHA}, got {actual}; do not silently update baseline')
(R/'reports/model.sha256').write_text(f'{actual}  artifacts/v5_5_ru.pt\n')
with zipfile.ZipFile(p) as z:
 names=z.namelist();prefix=names[0].split('/')[0]+'/'
 (R/'reports/package-files.json').write_text(json.dumps([{'name':x.filename.removeprefix(prefix),'bytes':x.file_size} for x in z.infolist()],indent=2))
 for name in names:
  if name.endswith('.py') or name.endswith('extern_modules'):
   relative=Path(name.removeprefix(prefix))
   if relative.is_absolute() or '..' in relative.parts:raise ValueError(name)
   target=a/'package'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
print(actual,p.stat().st_size)
