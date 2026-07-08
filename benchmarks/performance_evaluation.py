import time
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.vm.config import VMConfig
from core.process.process import Process
from core.memory.memory_manager import MemoryManager
from os_layer.scheduler.scheduler import Scheduler

def evaluate_performance():
    code = """
    int main() {
        int arr;
        arr = malloc(10);
        arr[0] = 5;
        free(arr);
        return 0;
    }
    """
    
    print("SecureExec Performance Benchmark\n")
    
    t0 = time.perf_counter()
    for _ in range(100):
        prog = compile_c_subset(code)
    t1 = time.perf_counter()
    avg_compile = (t1 - t0) / 100 * 1000
    print(f"Compiler (Average compilation time): {avg_compile:.4f} ms")
    
    config = VMConfig(memory_size=4096, register_count=16, instruction_limit=1000)
    verifier = Verifier(config)
    t0 = time.perf_counter()
    for _ in range(100):
        verifier.verify(prog)
    t1 = time.perf_counter()
    avg_verify = (t1 - t0) / 100 * 1000
    print(f"Verifier (Average verification time): {avg_verify:.4f} ms")
    
    memory_manager = MemoryManager(memory_size=1024 * 1024)
    scheduler = Scheduler(memory_manager)
    
    for _ in range(100):
        p = Process(prog, config)
        scheduler.load_processes([p])
        
    t0 = time.perf_counter()
    scheduler.run_all()
    t1 = time.perf_counter()
    avg_exec = (t1 - t0) / 100 * 1000
    print(f"Runtime (Average execution time): {avg_exec:.4f} ms")
    
    stats = scheduler.get_statistics()
    print(f"\nScheduler Statistics:")
    print(f"Context switches: {stats['context_switches']}")
    print(f"CPU utilization: {stats['cpu_utilization']}%")

if __name__ == "__main__":
    evaluate_performance()
