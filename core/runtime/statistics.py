class StatisticsCollector:
    def __init__(self):
        self.stats = {
            "compilation": {"instruction_count": 0},
            "verification": {"checks_performed": 0},
            "execution": {
                "instructions_executed": 0,
                "syscalls_used": 0,
                "memory_allocated": 0,
                "memory_freed": 0
            },
            "process": {
                "cpu_time": 0.0,
                "context_switches": 0,
                "exit_status": "UNKNOWN"
            }
        }
        
    def record_compilation(self, inst_count):
        self.stats["compilation"]["instruction_count"] = inst_count
        
    def record_verification(self, checks):
        self.stats["verification"]["checks_performed"] = checks
        
    def record_execution(self, process, scheduler_stats):
        self.stats["execution"]["instructions_executed"] = process.instructions_executed
        self.stats["execution"]["memory_allocated"] = getattr(process, "total_allocations", 0)
        self.stats["execution"]["memory_freed"] = getattr(process, "total_freed", 0)
        self.stats["execution"]["syscalls_used"] = getattr(process, "successful_syscalls", 0) # approximation if kernel not accessible
        
        self.stats["process"]["context_switches"] = scheduler_stats.get("context_switches", 0)
        self.stats["process"]["cpu_time"] = scheduler_stats.get("cpu_utilization", 0)
        
        if process.termination_reason and process.termination_reason != "Exited via syscall":
            self.stats["process"]["exit_status"] = "FAILED"
        elif process.exit_code != 0:
            self.stats["process"]["exit_status"] = "FAILED"
        elif process.finished or process.state == "TERMINATED":
            self.stats["process"]["exit_status"] = "SUCCESS"
        else:
            self.stats["process"]["exit_status"] = "FAILED"
