class IRInstruction: pass
class IRLoadConst(IRInstruction):
    def __init__(self, dest, val): self.dest = dest; self.val = val
class IRLoadVar(IRInstruction):
    def __init__(self, dest, var_name): self.dest = dest; self.var_name = var_name
class IRStoreVar(IRInstruction):
    def __init__(self, var_name, src): self.var_name = var_name; self.src = src
class IRBinOp(IRInstruction):
    def __init__(self, op, dest, left, right): self.op = op; self.dest = dest; self.left = left; self.right = right
class IRPrint(IRInstruction):
    def __init__(self, src): self.src = src
class IRReturn(IRInstruction):
    def __init__(self, src): self.src = src
class IREntryStub(IRInstruction): pass

class IRAllocateArray(IRInstruction):
    def __init__(self, name, size): self.name = name; self.size = size
class IRLoadArray(IRInstruction):
    def __init__(self, name, index, dest, size): self.name = name; self.index = index; self.dest = dest; self.size = size
class IRStoreArray(IRInstruction):
    def __init__(self, name, index, src, size): self.name = name; self.index = index; self.src = src; self.size = size

class IRMalloc(IRInstruction):
    def __init__(self, size, dest): self.size = size; self.dest = dest
class IRFree(IRInstruction):
    def __init__(self, ptr): self.ptr = ptr

class IRLoadHeap(IRInstruction):
    def __init__(self, ptr, index, dest): self.ptr = ptr; self.index = index; self.dest = dest
class IRStoreHeap(IRInstruction):
    def __init__(self, ptr, index, src): self.ptr = ptr; self.index = index; self.src = src

class IRFuncPrologue(IRInstruction):
    def __init__(self, params): self.params = params
class IRCall(IRInstruction):
    def __init__(self, name, args, dest): self.name = name; self.args = args; self.dest = dest
class IRJmp(IRInstruction):
    def __init__(self, label): self.label = label
class IRJz(IRInstruction):
    def __init__(self, cond, label): self.cond = cond; self.label = label
class IRLabel(IRInstruction):
    def __init__(self, name): self.name = name
class IRHalt(IRInstruction): pass
