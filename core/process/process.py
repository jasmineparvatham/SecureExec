import itertools
from core.vm.config import VMConfig

class Process:
    _pid_counter = itertools.count(1)

    def __init__(self, program, config=None):
        self.pid = next(self._pid_counter)
        self.program = program
        self.config = config or VMConfig()
        self.source_file = None
        self.program_name = None
        
        # State
        self.state = "NEW"
        
        # CPU Context
        self.ip = 0
        self.registers = {f"R{i}": 0 for i in range(self.config.register_count)}
        self.instructions_executed = 0
        
        # Scheduling Information
        self.priority = 0
        self.queue_level = 1
        self.cpu_time_used = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.creation_time = None
        self.first_run_time = None
        self.completion_time = None
        self.response_time = None
        
        # Memory Information
        self.virtual_memory_size = self.config.memory_size
        self.page_table = None

        # Stack Information
        self.call_stack = []
        self.allocated_arrays = {}
        self.heap_allocations = {}
        self.stack_pointer = 0
        self.base_pointer = 0
        self.function_depth = 0

        # Syscall Trackers
        self.syscalls_executed = 0
        self.last_syscall = None
        self.resource_requests = 0
        
        # Legacy compat
        self.finished = False
        self.ema = 0
        
        # Runtime Info
        self.exit_code = 0
        self.termination_reason = ""
        self.program_output = []

    def start(self):
        if self.state == "NEW":
            self.state = "READY"

    def run(self):
        if self.state in {"READY", "WAITING"}:
            self.state = "RUNNING"

    def wait(self):
        if self.state == "RUNNING":
            self.state = "WAITING"

    def terminate(self):
        self.state = "TERMINATED"
        self.finished = True
