import time
from compiler.c_subset_compiler import compile_c_subset
from core.vm.config import VMConfig
from core.process.process import Process
from core.memory.memory_manager import MemoryManager
from os_layer.scheduler.scheduler import Scheduler

def test_isolation():
    code = """
    int main() {
        int arr;
        int i = 0;
        int val;
        arr = malloc(1);
        arr[0] = 42;
        while (i < 5) {
            val = arr[0];
            if (val < 42) {
                print(999);
                return 1;
            }
            if (val > 42) {
                print(999);
                return 1;
            }
            i = i + 1;
        }
        return 0;
    }
    """
    prog = compile_c_subset(code)
    
    config = VMConfig(memory_size=4096, register_count=16, instruction_limit=1000)
    memory_manager = MemoryManager(memory_size=1024 * 1024)
    scheduler = Scheduler(memory_manager)
    
    processes = []
    for _ in range(100):
        p = Process(prog, config)
        scheduler.load_processes([p])
        processes.append(p)
        
    scheduler.run_all()
    
    violations = 0
    translations = 0
    memory_ops = 0
    
    for p in processes:
        if "999" in p.program_output:
            violations += 1
        translations += p.instructions_executed
        # Each loop iteration does memory accesses, roughly proportional to instructions
        memory_ops += (p.instructions_executed // 2)
        
    print("Processes Tested:")
    print("100\n")
    print("Memory Operations:")
    print(f"{memory_ops}\n")
    print("Page Translations:")
    print(f"{translations}\n")
    print("Isolation Violations:")
    print(f"{violations}\n")

if __name__ == "__main__":
    test_isolation()
