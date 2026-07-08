from compiler.ir import *

class CodeGenerator:
    def __init__(self):
        self.ir = []
        self.temp_count = 0
        self.label_count = 0
        self.var_map = {}
        self.array_map = {}
        self.function_labels = {}

    def get_temp(self):
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def get_label(self):
        name = f"L{self.label_count}"
        self.label_count += 1
        return name

    def generate_ir(self, node):
        if type(node).__name__ == "Program":
            for func in node.functions:
                self.function_labels[func.name] = self.get_label() + f"_{func.name}"
            
            self.ir.append(IREntryStub())
            
            for func in node.functions:
                self.generate_ir(func)
                
        elif type(node).__name__ == "FunctionDefinition":
            self.var_map = {}
            self.array_map = {}
            self.ir.append(IRLabel(self.function_labels[node.name]))
            
            for param in node.params:
                self.var_map[param] = True
                
            self.ir.append(IRFuncPrologue(node.params))
            
            for stmt in node.body:
                self.generate_ir(stmt)
                
            # Implicit return 0
            t = self.get_temp()
            self.ir.append(IRLoadConst(t, 0))
            self.ir.append(IRReturn(t))
        
        elif type(node).__name__ == "VarDecl":
            res = self.generate_expr(node.expr)
            self.var_map[node.name] = True
            self.ir.append(IRStoreVar(node.name, res))

        elif type(node).__name__ == "ArrayDeclaration":
            self.array_map[node.name] = node.size
            self.ir.append(IRAllocateArray(node.name, node.size))

        elif type(node).__name__ == "ArrayAssignment":
            if type(node.index).__name__ == "Num":
                idx = node.index.val
            else:
                idx = self.generate_expr(node.index)
            res = self.generate_expr(node.expr)
            
            if node.name in self.array_map:
                self.ir.append(IRStoreArray(node.name, idx, res, self.array_map[node.name]))
            elif node.name in self.var_map:
                self.ir.append(IRStoreHeap(node.name, idx, res))
            else:
                raise Exception(f"Undefined array or pointer {node.name}")

        elif type(node).__name__ == "Assign":
            res = self.generate_expr(node.expr)
            if node.name not in self.var_map:
                raise Exception(f"Undefined variable {node.name}")
            self.ir.append(IRStoreVar(node.name, res))

        elif type(node).__name__ == "Print":
            res = self.generate_expr(node.expr)
            self.ir.append(IRPrint(res))

        elif type(node).__name__ == "Return":
            res = self.generate_expr(node.expr)
            self.ir.append(IRReturn(res))

        elif type(node).__name__ == "FreeStatement":
            res = self.generate_expr(node.ptr_expr)
            self.ir.append(IRFree(res))

        elif type(node).__name__ == "If":
            res = self.generate_expr(node.cond)
            if getattr(node, 'else_body', None) is not None:
                l_else = self.get_label()
                l_end = self.get_label()
                self.ir.append(IRJz(res, l_else))
                for stmt in node.body:
                    self.generate_ir(stmt)
                self.ir.append(IRJmp(l_end))
                self.ir.append(IRLabel(l_else))
                for stmt in node.else_body:
                    self.generate_ir(stmt)
                self.ir.append(IRLabel(l_end))
            else:
                l_end = self.get_label()
                self.ir.append(IRJz(res, l_end))
                for stmt in node.body:
                    self.generate_ir(stmt)
                self.ir.append(IRLabel(l_end))

        elif type(node).__name__ == "While":
            l_start = self.get_label()
            l_end = self.get_label()
            self.ir.append(IRLabel(l_start))
            res = self.generate_expr(node.cond)
            self.ir.append(IRJz(res, l_end))
            for stmt in node.body:
                self.generate_ir(stmt)
            self.ir.append(IRJmp(l_start))
            self.ir.append(IRLabel(l_end))

    def generate_expr(self, node):
        if type(node).__name__ == "Num":
            t = self.get_temp()
            self.ir.append(IRLoadConst(t, node.val))
            return t
        elif type(node).__name__ == "Var":
            if node.name not in self.var_map:
                raise Exception(f"Undefined variable {node.name}")
            t = self.get_temp()
            self.ir.append(IRLoadVar(t, node.name))
            return t
        elif type(node).__name__ == "FunctionCall":
            arg_temps = []
            for arg in node.args:
                arg_temps.append(self.generate_expr(arg))
            t_res = self.get_temp()
            self.ir.append(IRCall(node.name, arg_temps, t_res))
            return t_res
        elif type(node).__name__ == "ArrayAccess":
            if node.name in self.array_map:
                t = self.get_temp()
                if type(node.index).__name__ == "Num":
                    self.ir.append(IRLoadArray(node.name, node.index.val, t, self.array_map[node.name]))
                else:
                    idx = self.generate_expr(node.index)
                    self.ir.append(IRLoadArray(node.name, idx, t, self.array_map[node.name]))
                return t
            elif node.name in self.var_map:
                t = self.get_temp()
                if type(node.index).__name__ == "Num":
                    self.ir.append(IRLoadHeap(node.name, node.index.val, t))
                else:
                    idx = self.generate_expr(node.index)
                    self.ir.append(IRLoadHeap(node.name, idx, t))
                return t
            else:
                raise Exception(f"Undefined array or pointer {node.name}")
        elif type(node).__name__ == "MallocExpression":
            t = self.get_temp()
            size = self.generate_expr(node.size_expr)
            self.ir.append(IRMalloc(size, t))
            return t
        elif type(node).__name__ == "BinOp":
            left = self.generate_expr(node.left)
            right = self.generate_expr(node.right)
            t = self.get_temp()
            op_map = {"+": "ADD", "-": "SUB", "<": "LT", ">": "GT", "==": "EQ", "*": "MUL", "/": "DIV"}
            self.ir.append(IRBinOp(op_map[node.op], t, left, right))
            return t

    def to_bytecode(self):
        bytecode = []
        labels = {}
        
        mem_alloc = {}
        mem_idx = 0
        def get_mem(temp):
            nonlocal mem_idx
            if temp not in mem_alloc:
                mem_alloc[temp] = mem_idx
                mem_idx += 1
            return mem_alloc[temp]

        for instr in self.ir:
            if type(instr).__name__ == "IRLabel":
                if instr.name in self.function_labels.values():
                    mem_alloc = {}
                    mem_idx = 0
                labels[instr.name] = len(bytecode)
            elif type(instr).__name__ == "IREntryStub":
                bytecode.append(("CALL", self.function_labels.get("main", "L_main")))
                bytecode.append(("SYSCALL", "EXIT", "R0"))
            elif type(instr).__name__ == "IRFuncPrologue":
                for i, param in enumerate(instr.params):
                    bytecode.append(("STORE", f"R{i+1}", get_mem(param)))
            elif type(instr).__name__ == "IRCall":
                for i, arg in enumerate(instr.args):
                    bytecode.append(("LOADM", f"R{i+1}", get_mem(arg)))
                bytecode.append(("CALL", self.function_labels[instr.name]))
                bytecode.append(("STORE", "R0", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRLoadConst":
                bytecode.append(("LOAD", "R0", instr.val))
                bytecode.append(("STORE", "R0", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRLoadVar":
                bytecode.append(("LOADM", "R0", get_mem(instr.var_name)))
                bytecode.append(("STORE", "R0", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRStoreVar":
                bytecode.append(("LOADM", "R0", get_mem(instr.src)))
                bytecode.append(("STORE", "R0", get_mem(instr.var_name)))
            elif type(instr).__name__ == "IRAllocateArray":
                mem_alloc[instr.name] = mem_idx
                bytecode.append(("ALLOC_ARRAY", instr.name, mem_idx, instr.size))
                mem_idx += instr.size
            elif type(instr).__name__ == "IRLoadArray":
                if isinstance(instr.index, int):
                    bytecode.append(("LOAD_INDEX", "R0", get_mem(instr.name), instr.index, instr.size))
                    bytecode.append(("STORE", "R0", get_mem(instr.dest)))
                else:
                    bytecode.append(("LOADM", "R1", get_mem(instr.index)))
                    bytecode.append(("LOAD_INDEX", "R0", get_mem(instr.name), "R1", instr.size))
                    bytecode.append(("STORE", "R0", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRStoreArray":
                bytecode.append(("LOADM", "R2", get_mem(instr.src)))
                if isinstance(instr.index, int):
                    bytecode.append(("STORE_INDEX", get_mem(instr.name), instr.index, "R2", instr.size))
                else:
                    bytecode.append(("LOADM", "R1", get_mem(instr.index)))
                    bytecode.append(("STORE_INDEX", get_mem(instr.name), "R1", "R2", instr.size))
            elif type(instr).__name__ == "IRLoadHeap":
                bytecode.append(("LOADM", "R1", get_mem(instr.ptr)))
                if isinstance(instr.index, int):
                    bytecode.append(("LOAD_HEAP", "R0", "R1", instr.index))
                else:
                    bytecode.append(("LOADM", "R2", get_mem(instr.index)))
                    bytecode.append(("LOAD_HEAP", "R0", "R1", "R2"))
                bytecode.append(("STORE", "R0", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRStoreHeap":
                bytecode.append(("LOADM", "R1", get_mem(instr.ptr)))
                bytecode.append(("LOADM", "R2", get_mem(instr.src)))
                if isinstance(instr.index, int):
                    bytecode.append(("STORE_HEAP", "R1", instr.index, "R2"))
                else:
                    bytecode.append(("LOADM", "R3", get_mem(instr.index)))
                    bytecode.append(("STORE_HEAP", "R1", "R3", "R2"))
            elif type(instr).__name__ == "IRMalloc":
                bytecode.append(("LOADM", "R0", get_mem(instr.size)))
                bytecode.append(("SYSCALL", "MALLOC", "R0", "R1"))
                bytecode.append(("STORE", "R1", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRFree":
                bytecode.append(("LOADM", "R0", get_mem(instr.ptr)))
                bytecode.append(("SYSCALL", "FREE", "R0"))
            elif type(instr).__name__ == "IRBinOp":
                bytecode.append(("LOADM", "R1", get_mem(instr.left)))
                bytecode.append(("LOADM", "R2", get_mem(instr.right)))
                bytecode.append((instr.op, "R0", "R1", "R2"))
                bytecode.append(("STORE", "R0", get_mem(instr.dest)))
            elif type(instr).__name__ == "IRPrint":
                bytecode.append(("LOADM", "R0", get_mem(instr.src)))
                bytecode.append(("SYSCALL", "PRINT", "R0"))
            elif type(instr).__name__ == "IRReturn":
                bytecode.append(("LOADM", "R0", get_mem(instr.src)))
                bytecode.append(("RET",))
            elif type(instr).__name__ == "IRJmp":
                bytecode.append(("JMP", instr.label))
            elif type(instr).__name__ == "IRJz":
                bytecode.append(("LOADM", "R0", get_mem(instr.cond)))
                bytecode.append(("JZ", "R0", instr.label))
            elif type(instr).__name__ == "IRHalt":
                bytecode.append(("HALT",))
                
        resolved_bytecode = []
        for instr in bytecode:
            if instr[0] == "JMP":
                resolved_bytecode.append(("JMP", labels[instr[1]]))
            elif instr[0] == "JZ":
                resolved_bytecode.append(("JZ", instr[1], labels[instr[2]]))
            elif instr[0] == "CALL":
                if isinstance(instr[1], str):
                    resolved_bytecode.append(("CALL", labels[instr[1]]))
                else:
                    resolved_bytecode.append(instr)
            else:
                resolved_bytecode.append(instr)
                
        return resolved_bytecode
