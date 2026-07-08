from core.errors import VMError
from core.process.process import Process

class SyscallHandler:
    def __init__(self, kernel):
        self.kernel = kernel

    def dispatch(self, process, syscall_name, *args):
        if syscall_name == "PRINT":
            return self.sys_print(process, *args)
        elif syscall_name == "EXIT":
            return self.sys_exit(process, *args)
        elif syscall_name == "GET_TIME":
            return self.sys_get_time(process)
        elif syscall_name == "ALLOCATE_MEMORY":
            return self.sys_allocate_memory(process, *args)
        elif syscall_name == "CREATE_PROCESS":
            return self.sys_create_process(process, *args)
        elif syscall_name == "MALLOC":
            return self.sys_malloc(process, *args)
        elif syscall_name == "FREE":
            return self.sys_free(process, *args)
        else:
            raise VMError(f"Unknown syscall: {syscall_name}")

    def sys_print(self, process, value):
        if isinstance(value, str) and value.startswith("R") and value in process.registers:
            value = process.registers[value]
        process.program_output.append(str(value))
        return 0

    def sys_exit(self, process, code):
        if isinstance(code, str) and code.startswith("R") and code in process.registers:
            code = process.registers[code]
        process.exit_code = code
        process.termination_reason = "Exited via syscall"
        process.finished = True
        return 0

    def sys_get_time(self, process):
        return self.kernel.scheduler.current_time

    def sys_allocate_memory(self, process, size):
        process.virtual_memory_size += size
        
        page_size = self.kernel.memory_manager.page_size
        num_pages = (size + page_size - 1) // page_size
        if len(self.kernel.memory_manager.free_frames) < num_pages:
            raise VMError("Out of physical memory")
        
        current_pages = len(process.page_table.mapping)
        for i in range(num_pages):
            p_frame = self.kernel.memory_manager.free_frames.pop(0)
            process.page_table.mapping[current_pages + i] = p_frame

    def sys_create_process(self, process, program):
        new_p = Process(program, process.config)
        self.kernel.scheduler.load_processes([new_p])
        return new_p.pid

    def sys_malloc(self, process, size_reg, dest_reg):
        size = process.registers.get(size_reg, 0)
        addr = self.kernel.heap_manager.allocate(process, size)
        process.registers[dest_reg] = addr
        process.total_allocations = getattr(process, "total_allocations", 0) + 1
        return addr
        
    def sys_free(self, process, ptr_reg):
        ptr = process.registers.get(ptr_reg, 0)
        self.kernel.heap_manager.free(process, ptr)
        process.total_freed = getattr(process, "total_freed", 0) + 1
        return 0
