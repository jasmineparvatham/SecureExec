from core.errors import VMError
from core.memory.memory_manager import MemoryManager

class Virtual_Machine:

    def __init__(self, memory_manager=None, kernel=None):
        self.memory_manager = memory_manager or MemoryManager()
        self.kernel = kernel

    def validate_register(self, process, reg):
        if not reg.startswith("R"):
            raise VMError(f"Invalid register format: {reg}")
        try:
            reg_idx = int(reg[1:])
            if reg_idx < 0 or reg_idx >= process.config.register_count:
                raise VMError(f"Invalid register index: {reg}")
        except ValueError:
            raise VMError(f"Invalid register format: {reg}")

    def run(self, process):
        # Run until finished
        while not process.finished:
            self.run_step(process, 1)

    def run_step(self, process, instruction_limit):
        instructions_run_this_step = 0

        while instructions_run_this_step < instruction_limit:

            if process.finished:
                break

            if process.instructions_executed > process.config.instruction_limit:
                process.finished = True
                raise VMError(f"Instruction limit exceeded: {process.config.instruction_limit}")

            if process.ip < 0 or process.ip >= len(process.program):
                raise VMError(
                    f"Instruction pointer out of bounds: {process.ip}")

            instruction = process.program[process.ip]
            opcode = instruction[0]

            # ---------------- Arithmetic (Binary) ----------------
            if opcode in {"ADD", "SUB", "MUL", "DIV", "MOD",
                          "AND", "OR", "XOR",
                          "SHL", "SHR",
                          "EQ", "LT", "GT", "LE", "GE"}:

                _, dest, r1, r2 = instruction

                self.validate_register(process, dest)
                self.validate_register(process, r1)
                self.validate_register(process, r2)

                a = process.registers[r1]
                b = process.registers[r2]

                if opcode == "ADD":
                    process.registers[dest] = a + b
                elif opcode == "SUB":
                    process.registers[dest] = a - b
                elif opcode == "MUL":
                    process.registers[dest] = a * b
                elif opcode == "DIV":
                    if b == 0:
                        raise VMError("Division by zero")
                    process.registers[dest] = a // b
                elif opcode == "MOD":
                    if b == 0:
                        raise VMError("Modulo by zero")
                    process.registers[dest] = a % b
                elif opcode == "AND":
                    process.registers[dest] = a & b
                elif opcode == "OR":
                    process.registers[dest] = a | b
                elif opcode == "XOR":
                    process.registers[dest] = a ^ b
                elif opcode == "SHL":
                    process.registers[dest] = a << b
                elif opcode == "SHR":
                    process.registers[dest] = a >> b
                elif opcode == "EQ":
                    process.registers[dest] = int(a == b)
                elif opcode == "LT":
                    process.registers[dest] = int(a < b)
                elif opcode == "GT":
                    process.registers[dest] = int(a > b)
                elif opcode == "LE":
                    process.registers[dest] = int(a <= b)
                elif opcode == "GE":
                    process.registers[dest] = int(a >= b)

            # ---------------- Unary ----------------
            elif opcode in {"NEG", "NOT"}:
                _, dest, r1 = instruction
                self.validate_register(process, dest)
                self.validate_register(process, r1)

                val = process.registers[r1]
                process.registers[dest] = -val if opcode == "NEG" else ~val

            elif opcode in {"INC", "DEC"}:
                _, reg = instruction
                self.validate_register(process, reg)

                if opcode == "INC":
                    process.registers[reg] += 1
                else:
                    process.registers[reg] -= 1

            # ---------------- Memory ----------------
            elif opcode == "LOAD":
                _, reg, value = instruction
                self.validate_register(process, reg)
                process.registers[reg] = value

            elif opcode == "LOADM":
                _, reg, mem_index = instruction
                self.validate_register(process, reg)

                virtual_address = process.base_pointer + mem_index
                if virtual_address >= process.stack_pointer:
                    process.stack_pointer = virtual_address + 1

                process.registers[reg] = self.memory_manager.read(process, virtual_address)

            elif opcode == "STORE":
                _, reg, mem_index = instruction
                self.validate_register(process, reg)

                virtual_address = process.base_pointer + mem_index
                if virtual_address >= process.stack_pointer:
                    process.stack_pointer = virtual_address + 1

                self.memory_manager.write(process, virtual_address, process.registers[reg])

            elif opcode == "ALLOC_ARRAY":
                _, name, base_idx, size = instruction
                v_start = process.base_pointer + base_idx
                process.allocated_arrays[name] = {"start": v_start, "end": v_start + size - 1}
                if v_start + size > process.stack_pointer:
                    process.stack_pointer = v_start + size
            elif opcode == "LOAD_INDEX":
                _, reg, base_idx, offset_arg, size = instruction
                if isinstance(offset_arg, str):
                    offset = process.registers.get(offset_arg, 0)
                else:
                    offset = offset_arg
                if offset < 0 or offset >= size:
                    raise VMError("Array index out of bounds")
                v_addr = process.base_pointer + base_idx + offset
                process.registers[reg] = self.memory_manager.read(process, v_addr)
            elif opcode == "STORE_INDEX":
                _, base_idx, offset_arg, reg, size = instruction
                if isinstance(offset_arg, str):
                    offset = process.registers.get(offset_arg, 0)
                else:
                    offset = offset_arg
                if offset < 0 or offset >= size:
                    raise VMError("Array index out of bounds")
                v_addr = process.base_pointer + base_idx + offset
                val = process.registers.get(reg, 0)
                self.memory_manager.write(process, v_addr, val)

            elif opcode == "LOAD_HEAP":
                _, dest_reg, ptr_reg, offset_arg = instruction
                ptr = process.registers.get(ptr_reg, 0)
                offset = process.registers.get(offset_arg, 0) if isinstance(offset_arg, str) else offset_arg
                valid = False
                for block in process.heap_allocations.values():
                    if block["start_address"] == ptr and 0 <= offset < block["size"]:
                        valid = True
                        break
                if not valid:
                    raise VMError(f"Invalid heap access at {ptr} + {offset}")
                self.validate_register(process, dest_reg)
                process.registers[dest_reg] = self.memory_manager.read(process, ptr + offset)

            elif opcode == "STORE_HEAP":
                _, ptr_reg, offset_arg, src_reg = instruction
                ptr = process.registers.get(ptr_reg, 0)
                offset = process.registers.get(offset_arg, 0) if isinstance(offset_arg, str) else offset_arg
                valid = False
                for block in process.heap_allocations.values():
                    if block["start_address"] == ptr and 0 <= offset < block["size"]:
                        valid = True
                        break
                if not valid:
                    raise VMError(f"Invalid heap access at {ptr} + {offset}")
                val = process.registers.get(src_reg, 0)
                self.memory_manager.write(process, ptr + offset, val)

            # ---------------- Control Flow ----------------
            elif opcode == "CALL":
                _, target = instruction
                if target < 0 or target >= len(process.program):
                    raise VMError(f"Invalid CALL target: {target}")
                
                max_depth = getattr(process.config, 'max_call_depth', 256)
                if process.function_depth >= max_depth:
                    raise VMError("Stack overflow: maximum call depth exceeded")
                
                from core.memory.stack import StackFrame
                frame = StackFrame(process.ip, process.base_pointer)
                process.call_stack.append(frame)
                
                process.base_pointer = process.stack_pointer
                process.function_depth += 1
                
                process.ip = target
                instructions_run_this_step += 1
                process.instructions_executed += 1
                continue
                
            elif opcode == "RET":
                if not process.call_stack:
                    raise VMError("RET without matching CALL")
                
                frame = process.call_stack.pop()
                
                process.stack_pointer = process.base_pointer
                process.base_pointer = frame.base_pointer
                process.ip = frame.return_ip + 1
                process.function_depth -= 1
                
                instructions_run_this_step += 1
                process.instructions_executed += 1
                continue

            elif opcode == "JMP":
                _, target = instruction
                if target < 0 or target >= len(process.program):
                    raise VMError(f"Invalid jump target: {target}")
                process.ip = target
                instructions_run_this_step += 1
                process.instructions_executed += 1
                continue

            elif opcode in {"JZ", "JNZ"}:
                _, reg, target = instruction
                self.validate_register(process, reg)

                condition = (process.registers[reg] == 0) if opcode == "JZ" else (
                    process.registers[reg] != 0
                )

                if condition:
                    if target < 0 or target >= len(process.program):
                        raise VMError(f"Invalid jump target: {target}")
                    process.ip = target
                    instructions_run_this_step += 1
                    process.instructions_executed += 1
                    continue

            elif opcode == "SYSCALL":
                if not self.kernel:
                    raise VMError("Syscalls are not supported without a Kernel")
                syscall_name = instruction[1]
                args = instruction[2:]
                result = self.kernel.handle_syscall(process, syscall_name, *args)
                if result is not None:
                    process.registers["R0"] = result

            elif opcode == "NOP":
                pass

            elif opcode == "HALT":
                process.finished = True
                instructions_run_this_step += 1
                process.instructions_executed += 1
                break

            else:
                raise VMError(f"Unknown instruction: {opcode}")

            process.ip += 1
            instructions_run_this_step += 1
            process.instructions_executed += 1

        return process, instructions_run_this_step, process.finished
