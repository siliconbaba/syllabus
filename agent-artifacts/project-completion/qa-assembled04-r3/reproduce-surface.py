from pathlib import Path
root=Path.cwd()
src=(root/'agent-artifacts/qa/batch-03-r3/reproduce-surface-independent.py').read_text().splitlines()
src[1]="root=pathlib.Path.cwd();out=pathlib.Path('agent-artifacts/project-completion/qa-assembled04-r3');out.mkdir(exist_ok=True);new=json.load(open('agent-artifacts/test-bank/batch-04-completion03-r3/cases.json'))['cases'];old=json.load(open('InteractiveBook/TrainerContent/cases.json'))['cases'][:100];assert hashlib.sha256(json.dumps(old,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()=='7af3d84b3d808ec3305b306c41ca7e83fda17b0d0c28cff4142d401e422e67f5' and len(new)==25"
i=next(i for i,s in enumerate(src) if s.startswith('corpora='))
src[i]="corpora={name:scan(rows) for name,rows in [('batch04',new),('combined125',old+new)]}"
exec('\n'.join(src).replace("out/'surface-leakage-independent.json'", "out/'surface.json'"))
