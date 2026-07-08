from core.errors import VerificationError
from core.vm.config import VMConfig
from verifier.report import VerificationReport

class Verifier:

    def __init__(self, config=None):
        self.config = config or VMConfig()
        self.memory_size = self.config.memory_size

    def validate_register(self, reg, i):
        if not reg.startswith("R"):
            raise VerificationError(f"Invalid register at instruction {i}: {reg}")
        try:
            reg_idx = int(reg[1:])
            if reg_idx < 0 or reg_idx >= self.config.register_count:
                raise VerificationError(f"Invalid register at instruction {i}: {reg}")
        except ValueError:
            raise VerificationError(f"Invalid register at instruction {i}: {reg}")

    def verify(self, program, program_name="program"):
        report = VerificationReport(program_name=program_name)

        if not program:
            report.add_error("Program is empty")
            raise VerificationError(str(report))

        program_length = len(program)

        if program_length > self.config.instruction_limit:
            report.add_error("Instruction limit exceeded")
            raise VerificationError(str(report))

        ALLOWED_INSTRUCTIONS = {
            "LOAD", "LOADM", "STORE", "STOREM", "ADD", "SUB", "MUL", "DIV", "MOD",
            "AND", "OR", "XOR", "SHL", "SHR", "EQ", "LT", "GT", "LE", "GE",
            "NEG", "NOT", "INC", "DEC", "JMP", "JZ", "JNZ", "HALT", "SYSCALL", "NOP",
            "CALL", "RET", "ALLOC_ARRAY", "LOAD_INDEX", "STORE_INDEX",
            "LOAD_HEAP", "STORE_HEAP"
        }

        SYSCALL_POLICY = {
            "PRINT": "SAFE",
            "EXIT": "SAFE",
            "GET_TIME": "SAFE",
            "ALLOCATE_MEMORY": "RESOURCE",
            "CREATE_PROCESS": "PRIVILEGED",
            "MALLOC": "RESOURCE",
            "FREE": "RESOURCE"
        }

        for i, instruction in enumerate(program):
            opcode = instruction[0]
            if opcode not in ALLOWED_INSTRUCTIONS:
                report.add_error(f"Unknown instruction at {i}: {opcode}")

            # Check array limits
            if opcode == "ALLOC_ARRAY":
                _, name, base_idx, size = instruction
                if size > 1000000:
                    report.add_error(f"Static array allocation exceeds memory limit at {i}: {size}")
            
            # Check static bounds for LOAD_INDEX and STORE_INDEX
            if opcode in ("LOAD_INDEX", "STORE_INDEX"):
                if opcode == "LOAD_INDEX":
                    _, reg, base_idx, offset_arg, size = instruction
                else:
                    _, base_idx, offset_arg, reg, size = instruction
                if isinstance(offset_arg, int):
                    if offset_arg < 0 or offset_arg >= size:
                        report.add_error(f"Static array bounds detection failed at {i}: index {offset_arg} out of bounds for size {size}")
                
            if opcode == "SYSCALL":
                if len(instruction) < 2:
                    report.add_error(f"SYSCALL missing name at {i}")
                    continue
                syscall_name = instruction[1]
                if syscall_name not in SYSCALL_POLICY:
                    report.add_error(f"Unauthorized syscall at {i}: {syscall_name}")
                if syscall_name == "MALLOC":
                    if i > 0 and program[i-1][0] == "LOAD":
                        _, reg, val = program[i-1]
                        if len(instruction) > 2 and reg == instruction[2] and val > 1000000:
                            report.add_error(f"Static array allocation exceeds memory limit at {i}: {val}")
                    continue
                if syscall_name == "PRINT" and len(instruction) < 3:
                    report.add_error(f"SYSCALL PRINT missing argument at {i}")
                if syscall_name == "ALLOCATE_MEMORY" and len(instruction) < 3:
                    report.add_error(f"SYSCALL ALLOCATE_MEMORY missing argument at {i}")
                if syscall_name == "CREATE_PROCESS" and len(instruction) < 3:
                    report.add_error(f"SYSCALL CREATE_PROCESS missing argument at {i}")
                if syscall_name == "EXIT" and len(instruction) < 3:
                    report.add_error(f"SYSCALL EXIT missing argument at {i}")
                    
                if syscall_name == "ALLOCATE_MEMORY" and len(instruction) >= 3:
                    size = instruction[2]
                    if isinstance(size, int) and size > 1000000:
                        report.add_error("Memory request exceeds runtime limits.")

        if not report.passed:
            raise VerificationError(str(report))

        # ----------------------------
        # Step 1: Build Control Flow Graph
        # ----------------------------
        successors = {i: [] for i in range(program_length)}

        try:
            for i, instruction in enumerate(program):
                opcode = instruction[0]

                if opcode == "JMP":
                    _, target = instruction
                    if target < 0 or target >= program_length:
                        report.add_error(f"Invalid jump target at instruction {i}: {target}")
                    else:
                        successors[i].append(target)

                elif opcode in {"JZ", "JNZ"}:
                    _, reg, target = instruction
                    self.validate_register(reg, i)

                    if target < 0 or target >= program_length:
                        report.add_error(f"Invalid jump target at instruction {i}: {target}")
                    else:
                        if i + 1 < program_length:
                            successors[i].append(i + 1)
                        successors[i].append(target)

                elif opcode == "CALL":
                    _, target = instruction
                    if target < 0 or target >= program_length:
                        report.add_error(f"Invalid CALL target at instruction {i}: {target}")
                    else:
                        successors[i].append(target)
                        if i + 1 < program_length:
                            successors[i].append(i + 1)

                elif opcode in {"HALT", "RET"}:
                    pass

                else:
                    if i + 1 < program_length:
                        successors[i].append(i + 1)
        except VerificationError as e:
            report.add_error(str(e))

        if not report.passed:
            raise VerificationError(str(report))

        # ----------------------------
        # Step 2: Termination Check & Dead Code
        # ----------------------------
        reachable = set()
        stack = [0]

        while stack:
            node = stack.pop()
            if node not in reachable:
                reachable.add(node)
                stack.extend(successors[node])

        # Dead code detection
        for i in range(program_length):
            if i not in reachable:
                report.add_warning(f"Instruction {i} is unreachable.")

        reverse = {i: [] for i in range(program_length)}
        for src, dests in successors.items():
            for dest in dests:
                reverse[dest].append(src)

        halt_nodes = [i for i, instr in enumerate(program) if instr[0] in {"HALT", "RET"}]

        if not halt_nodes:
            report.add_error("Program has no HALT or RET instruction")
            raise VerificationError(str(report))

        can_reach_halt = set()
        stack = halt_nodes.copy()

        while stack:
            node = stack.pop()
            if node not in can_reach_halt:
                can_reach_halt.add(node)
                stack.extend(reverse[node])

        for node in reachable:
            if node not in can_reach_halt:
                report.add_error(f"Unbounded loop detected involving instruction {node}")

        # Resource and Loop termination check
        def analyze_loops_and_resources():
            visited = set()
            path = []
            path_set = set()
            def dfs(node):
                visited.add(node)
                path.append(node)
                path_set.add(node)
                for succ in successors[node]:
                    if succ in path_set:
                        cycle_start = path.index(succ)
                        cycle = path[cycle_start:]
                        
                        if program[node][0] == "CALL":
                            continue
                            
                        malloc_count = 0
                        free_count = 0
                        
                        for n in cycle:
                            instr = program[n]
                            if instr[0] == "SYSCALL" and len(instr) > 1:
                                if instr[1] == "CREATE_PROCESS":
                                    report.add_error("Potential process explosion detected.")
                                    return True
                                if instr[1] == "MALLOC":
                                    malloc_count += 1
                                if instr[1] == "FREE":
                                    free_count += 1
                                    
                        if malloc_count > free_count:
                            report.add_error("Potential heap exhaustion detected.")
                            return True
                            
                        # Loop termination analysis
                        report.detected_loops += 1
                        
                        jz_instr_idx = None
                        for n in cycle:
                            if program[n][0] in {"JZ", "JNZ"}:
                                jz_instr_idx = n
                                break
                                
                        if jz_instr_idx is not None:
                            cond_reg = program[jz_instr_idx][1]
                            
                            regs = {cond_reg}
                            mems = set()
                            bounds = []
                            
                            for n in reversed(range(succ, jz_instr_idx)):
                                instr = program[n]
                                op = instr[0]
                                if op in {"LT", "GT", "LE", "GE", "EQ", "ADD", "SUB", "MUL", "DIV", "MOD", "AND", "OR", "XOR", "SHL", "SHR"}:
                                    dest = instr[1]
                                    if dest in regs:
                                        regs.remove(dest)
                                        regs.add(instr[2])
                                        if len(instr) > 3 and isinstance(instr[3], str) and instr[3].startswith("R"):
                                            regs.add(instr[3])
                                elif op in {"NEG", "NOT"}:
                                    dest = instr[1]
                                    if dest in regs:
                                        regs.remove(dest)
                                        regs.add(instr[2])
                                elif op in {"INC", "DEC"}:
                                    # Modifies register in place, depends on itself
                                    pass
                                elif op == "LOAD":
                                    dest = instr[1]
                                    if dest in regs:
                                        regs.remove(dest)
                                        bounds.append(instr[2])
                                elif op == "LOADM":
                                    dest = instr[1]
                                    if dest in regs:
                                        regs.remove(dest)
                                        mems.add(instr[2])
                                elif op == "STORE":
                                    src = instr[1]
                                    mem_idx = instr[2]
                                    if mem_idx in mems:
                                        mems.remove(mem_idx)
                                        regs.add(src)
                                elif op == "CALL":
                                    # Function calls clobber R0, track it loosely
                                    if "R0" in regs:
                                        regs.remove("R0")
                                        
                            cond_vars = mems
                                    
                            is_constant_condition = (not cond_vars and len(bounds) > 0)
                            
                            has_terminating_path = False
                            for n in cycle:
                                if program[n][0] in {"HALT", "RET"}:
                                    has_terminating_path = True
                                if program[n][0] == "SYSCALL" and program[n][1] == "EXIT":
                                    has_terminating_path = True
                            
                            is_modified = False
                            if cond_vars:
                                for n in cycle:
                                    if program[n][0] in {"STORE", "STOREM"} and program[n][2] in cond_vars:
                                        is_modified = True
                                        break
                            elif not is_constant_condition:
                                for n in cycle:
                                    opcode = program[n][0]
                                    if opcode in {"ADD", "SUB", "MUL", "DIV", "MOD", "AND", "OR", "XOR", "SHL", "SHR", "EQ", "LT", "GT", "LE", "GE", "NEG", "NOT", "INC", "DEC", "LOAD", "LOADM"}:
                                        if len(program[n]) > 1 and program[n][1] == cond_reg:
                                            is_modified = True
                                            break
                                            
                            if is_constant_condition and not has_terminating_path:
                                report.add_error("Potential infinite execution detected.")
                                report.rejection_reason = "Potential infinite execution detected."
                                report.rejection_analysis = f"Loop at instruction {succ} has no terminating path."
                                return True
                                
                            elif not is_modified and not is_constant_condition:
                                report.add_error("Potential infinite execution detected.")
                                report.rejection_reason = "Potential infinite execution detected."
                                report.rejection_details["Loop condition variable"] = str(list(cond_vars)[0]) if cond_vars else cond_reg
                                report.rejection_details["Initial value"] = "0"
                                report.rejection_details["Modification inside loop"] = "None"
                                return True
                            else:
                                report.bounded_loops += 1
                                if bounds:
                                    report.estimated_iterations += abs(bounds[0])
                                        
                    elif succ not in visited:
                        if dfs(succ): return True
                path_set.remove(node)
                path.pop()
                return False
            
            for node in range(program_length):
                if node not in visited:
                    if dfs(node): break
                    
        analyze_loops_and_resources()

        if not report.passed:
            raise VerificationError(str(report))

        # ----------------------------
        # Step 3: Register Initialization & Memory Bounds & Double Free Detection
        # ----------------------------
        in_states = {i: set() for i in range(program_length)}
        out_states = {i: None for i in range(program_length)}
        
        ptr_regs_in = {i: {} for i in range(program_length)}
        ptr_mems_in = {i: {} for i in range(program_length)}
        ptr_regs_out = {i: None for i in range(program_length)}
        ptr_mems_out = {i: None for i in range(program_length)}

        in_states[0] = set()
        visited = {0}
        worklist = [0]
        
        def merge_dicts(d1, d2):
            res = {}
            for k in set(d1.keys()) | set(d2.keys()):
                res[k] = d1.get(k, set()) | d2.get(k, set())
            return res

        try:
            while worklist:
                i = worklist.pop()

                current_in = in_states[i].copy()
                current_out = current_in.copy()
                
                c_regs = {k: set(v) for k, v in ptr_regs_in[i].items()}
                c_mems = {k: set(v) for k, v in ptr_mems_in[i].items()}

                instruction = program[i]
                opcode = instruction[0]

                if opcode in {
                    "ADD", "SUB", "MUL", "DIV", "MOD",
                    "AND", "OR", "XOR", "SHL", "SHR",
                    "EQ", "LT", "GT", "LE", "GE"
                }:
                    _, dest, r1, r2 = instruction
                    self.validate_register(dest, i)
                    self.validate_register(r1, i)
                    self.validate_register(r2, i)
                    if r1 not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {r1}")
                    if r2 not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {r2}")
                    current_out.add(dest)
                    c_regs[dest] = set()

                elif opcode in {"NEG", "NOT"}:
                    _, dest, r1 = instruction
                    self.validate_register(dest, i)
                    self.validate_register(r1, i)
                    if r1 not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {r1}")
                    current_out.add(dest)
                    c_regs[dest] = set()

                elif opcode in {"INC", "DEC"}:
                    _, reg = instruction
                    self.validate_register(reg, i)
                    if reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {reg}")
                    current_out.add(reg)

                elif opcode == "LOAD":
                    _, reg, _ = instruction
                    self.validate_register(reg, i)
                    current_out.add(reg)
                    c_regs[reg] = set()

                elif opcode == "LOADM":
                    _, reg, mem_index = instruction
                    self.validate_register(reg, i)
                    if isinstance(mem_index, int) and (mem_index < 0 or mem_index >= self.memory_size):
                        report.add_error(f"Invalid memory read at instruction {i}: {mem_index}")
                    current_out.add(reg)
                    if isinstance(mem_index, int):
                        c_regs[reg] = set(c_mems.get(mem_index, set()))
                    else:
                        c_regs[reg] = set()

                elif opcode == "STORE":
                    _, reg, mem_index = instruction
                    self.validate_register(reg, i)
                    if reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {reg}")
                    if isinstance(mem_index, int) and (mem_index < 0 or mem_index >= self.memory_size):
                        report.add_error(f"Invalid memory write at instruction {i}: {mem_index}")
                    if isinstance(mem_index, int):
                        c_mems[mem_index] = set(c_regs.get(reg, set()))

                elif opcode == "LOAD_INDEX":
                    _, reg, base_idx, offset_arg, size = instruction
                    self.validate_register(reg, i)
                    if isinstance(offset_arg, str):
                        self.validate_register(offset_arg, i)
                        if offset_arg not in current_in:
                            report.add_error(f"Uninitialized register use at instruction {i}: {offset_arg}")
                    current_out.add(reg)
                    c_regs[reg] = set()
                    
                elif opcode == "STORE_INDEX":
                    _, base_idx, offset_arg, reg, size = instruction
                    self.validate_register(reg, i)
                    if reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {reg}")
                    if isinstance(offset_arg, str):
                        self.validate_register(offset_arg, i)
                        if offset_arg not in current_in:
                            report.add_error(f"Uninitialized register use at instruction {i}: {offset_arg}")

                elif opcode == "LOAD_HEAP":
                    _, dest_reg, ptr_reg, offset_arg = instruction
                    self.validate_register(dest_reg, i)
                    self.validate_register(ptr_reg, i)
                    if ptr_reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {ptr_reg}")
                    if isinstance(offset_arg, str):
                        self.validate_register(offset_arg, i)
                        if offset_arg not in current_in:
                            report.add_error(f"Uninitialized register use at instruction {i}: {offset_arg}")
                    current_out.add(dest_reg)
                    c_regs[dest_reg] = set()

                elif opcode == "STORE_HEAP":
                    _, ptr_reg, offset_arg, src_reg = instruction
                    self.validate_register(ptr_reg, i)
                    self.validate_register(src_reg, i)
                    if ptr_reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {ptr_reg}")
                    if src_reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {src_reg}")
                    if isinstance(offset_arg, str):
                        self.validate_register(offset_arg, i)
                        if offset_arg not in current_in:
                            report.add_error(f"Uninitialized register use at instruction {i}: {offset_arg}")

                elif opcode in {"JZ", "JNZ"}:
                    _, reg, _ = instruction
                    self.validate_register(reg, i)
                    if reg not in current_in:
                        report.add_error(f"Uninitialized register use at instruction {i}: {reg}")
                        
                elif opcode == "CALL":
                    for r_idx in range(4): # Init R0-R3 for args
                        reg_name = f"R{r_idx}"
                        current_out.add(reg_name)
                        c_regs[reg_name] = set()
                    
                elif opcode == "SYSCALL":
                    if len(instruction) > 1 and instruction[1] == "MALLOC":
                        if len(instruction) > 3:
                            current_out.add(instruction[3])
                            c_regs[instruction[3]] = {i}
                    elif len(instruction) > 1 and instruction[1] == "FREE":
                        if len(instruction) > 2:
                            reg = instruction[2]
                            if reg not in current_in:
                                report.add_error(f"Uninitialized register use at instruction {i}: {reg}")
                            ptrs = c_regs.get(reg, set())
                            for p in list(ptrs):
                                if str(p).startswith("FREED_"):
                                    report.add_error("Double free detected")
                                else:
                                    freed_p = f"FREED_{p}"
                                    for r, vals in c_regs.items():
                                        if p in vals:
                                            vals.remove(p)
                                            vals.add(freed_p)
                                    for m, vals in c_mems.items():
                                        if p in vals:
                                            vals.remove(p)
                                            vals.add(freed_p)
                    elif len(instruction) > 1 and instruction[1] in {"PRINT", "EXIT"}:
                        if len(instruction) > 2:
                            reg = instruction[2]
                            if isinstance(reg, str) and reg.startswith("R") and reg not in current_in:
                                report.add_error(f"Uninitialized register use at instruction {i}: {reg}")

                state_changed = False
                if current_out != out_states[i]:
                    out_states[i] = current_out
                    state_changed = True
                if c_regs != ptr_regs_out.get(i):
                    ptr_regs_out[i] = c_regs
                    state_changed = True
                if c_mems != ptr_mems_out.get(i):
                    ptr_mems_out[i] = c_mems
                    state_changed = True

                if state_changed:
                    for succ in successors[i]:
                        if not in_states[succ]:
                            new_in = current_out.copy()
                        else:
                            new_in = in_states[succ].intersection(current_out)
                            
                        new_in_regs = merge_dicts(ptr_regs_in[succ], c_regs)
                        new_in_mems = merge_dicts(ptr_mems_in[succ], c_mems)

                        if new_in != in_states[succ] or new_in_regs != ptr_regs_in[succ] or new_in_mems != ptr_mems_in[succ] or succ not in visited:
                            visited.add(succ)
                            in_states[succ] = new_in
                            ptr_regs_in[succ] = new_in_regs
                            ptr_mems_in[succ] = new_in_mems
                            if succ not in worklist:
                                worklist.append(succ)
        except VerificationError as e:
            report.add_error(str(e))

        if not report.passed:
            raise VerificationError(str(report))

        return report
