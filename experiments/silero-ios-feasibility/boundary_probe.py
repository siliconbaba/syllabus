from pathlib import Path
import torch
R=Path(__file__).resolve().parent
torch.set_num_threads(4)
c=torch.jit.load(str(R/'artifacts/neural-core.jit.pt')).eval()
g=c.forward.graph.copy();torch._C._jit_pass_inline(g)
(R/'artifacts/onnx-dsp/inlined.txt').write_text(str(g))
for n in g.nodes():
 if n.kind() in ['aten::chunk','aten::complex','aten::fft_irfft','aten::linear']:
  print(n.kind(),n.scopeName(),str(n)[:350])
print('top outputs',[(x.debugName(),str(x.type())) for x in c.forward.graph.nodes() for x in x.outputs()][-20:])
