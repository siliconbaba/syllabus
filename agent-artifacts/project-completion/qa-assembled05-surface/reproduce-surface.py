from pathlib import Path
root=Path.cwd()
src=(root/'agent-artifacts/qa/batch-03-r3/reproduce-surface-independent.py').read_text().splitlines()
src[1]="root=pathlib.Path.cwd();out=root/'agent-artifacts/project-completion/qa-assembled05-surface';new=json.load(open('agent-artifacts/test-bank/batch-05-completion05/cases.json'))['cases'];old=json.load(open('InteractiveBook/TrainerContent/cases.json'))['cases'][:125];assert [r['id'] for r in old]==[f'TC-{i:03}' for i in range(1,126)] and [r['id'] for r in new]==[f'TC-{i:03}' for i in range(126,151)]"
i=next(i for i,s in enumerate(src) if s.startswith('corpora='))
src[i]="corpora={name:scan(rows) for name,rows in [('batch05',new),('production125',old),('combined150',old+new)]}"
exec('\n'.join(src).replace("out/'surface-leakage-independent.json'", "out/'surface.json'"))
