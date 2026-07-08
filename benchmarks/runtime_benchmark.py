import time
from core.vm.config import VMConfig
from core.process.process import Process
from os_layer.scheduler.scheduler import Scheduler
from core.memory.memory_manager import MemoryManager

def run():
    print("Runtime Benchmark\n")
    print("Processes:\n100\n")
    print("Memory:\n1 MB\n")
    print("Scheduler:\nMLFQ\n")
    
    config = VMConfig(memory_size=4096, register_count=16, instruction_limit=50000)
    memory_manager = MemoryManager(memory_size=1024 * 1024)
    scheduler = Scheduler(memory_manager)
    scheduler.debug = False
    
    program = [
        ("LOAD", "R1", 50),
        ("LOAD", "R2", 1),
        ("SUB", "R1", "R1", "R2"),
        ("JNZ", "R1", 2),
        ("HALT",)
    ]
    
    processes = [Process(program, config) for _ in range(100)]
    scheduler.load_processes(processes)
    
    start_time = time.perf_counter()
    scheduler.run_all()
    end_time = time.perf_counter()
    
    stats = scheduler.get_statistics()
    
    print("Results:\n")
    total_inst = sum(p.instructions_executed for p in processes)
    print(f"Instructions Executed:\n{total_inst}\n")
    print(f"Context Switches:\n{stats['context_switches']}\n")
    print(f"CPU Utilization:\n{stats['cpu_utilization']}%\n")
    print(f"Average Execution Time:\n{((end_time - start_time) * 1000):.2f} ms")

if __name__ == "__main__":
    run()
