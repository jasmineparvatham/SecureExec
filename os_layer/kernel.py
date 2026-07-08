import time
from core.memory.memory_manager import MemoryManager
from core.memory.heap import HeapManager
from os_layer.syscalls.handlers import SyscallHandler

class Kernel:
    def __init__(self, memory_manager, scheduler):
        self.memory_manager = memory_manager
        self.scheduler = scheduler
        self.syscall_handler = SyscallHandler(self)
        self.heap_manager = HeapManager(self.memory_manager)
        self.successful_syscalls = 0
        self.rejected_syscalls = 0
        self.syscall_time_total = 0.0

    def handle_syscall(self, process, syscall_name, *args):
        t0 = time.perf_counter()
        process.syscalls_executed += 1
        process.last_syscall = syscall_name
        process.resource_requests += 1

        try:
            result = self.syscall_handler.dispatch(process, syscall_name, *args)
            self.successful_syscalls += 1
            self.syscall_time_total += time.perf_counter() - t0
            return result
        except Exception as e:
            self.rejected_syscalls += 1
            self.syscall_time_total += time.perf_counter() - t0
            raise e
