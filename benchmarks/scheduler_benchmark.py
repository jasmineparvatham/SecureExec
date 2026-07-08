import time
from core.vm.config import VMConfig
from core.process.process import Process
from os_layer.scheduler.scheduler import Scheduler
from core.memory.memory_manager import MemoryManager

def run():
    print("Scheduler Benchmark\n")
    print("Queues:\nMLFQ (3 levels)\n")
    
    config = VMConfig(memory_size=4096, register_count=16)
    memory_manager = MemoryManager(memory_size=1024 * 1024)
    scheduler = Scheduler(memory_manager)
    scheduler.debug = False
    
    cpu_prog = [("LOAD", "R0", 1), ("ADD", "R0", "R0", "R0")] * 10 + [("HALT",)]
    io_prog = [("SYSCALL", "GET_TIME")] * 5 + [("HALT",)]
    
    processes = []
    for _ in range(50):
        processes.append(Process(cpu_prog, config))
        processes.append(Process(io_prog, config))
        
    scheduler.load_processes(processes)
    scheduler.run_all()
    stats = scheduler.get_statistics()
    
    print("Results:\n")
    print(f"Context Switches:\n{stats['context_switches']}\n")
    print(f"Average Waiting Time:\n{stats['average_waiting_time']} ms\n")
    print(f"Average Turnaround Time:\n{stats['average_turnaround_time']} ms\n")
    print(f"CPU Utilization:\n{stats['cpu_utilization']}%\n")

if __name__ == "__main__":
    run()
