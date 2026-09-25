import torch

def dense_fp32_graph(module):
    """Specialize only tensor representation and precision, never lengths or predictions."""
    module=torch.jit.freeze(torch.jit.script(module.eval()))
    graph=module.forward.graph
    torch._C._jit_pass_inline(graph)
    def walk(block):
        for node in list(block.nodes()):
            for child in node.blocks(): walk(child)
            if node.kind() in ('prim::is_nested','aten::is_autocast_enabled'):
                value=graph.insertConstant(False)
                value.node().moveBefore(node)
                node.output().replaceAllUsesWith(value)
                node.destroy()
    walk(graph)
    torch._C._jit_pass_constant_propagation(graph)
    torch._C._jit_pass_peephole(graph)
    torch._C._jit_pass_dce(graph)
    graph.lint()
    return module
