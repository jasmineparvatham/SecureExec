from core.vm.config import VMConfig
from core.process.process import Process
from core.memory.memory_manager import MemoryManager

def run():
    print("Virtual Memory Benchmark\n")
    
    config = VMConfig(memory_size=4096, register_count=16)
    memory_manager = MemoryManager(memory_size=1024 * 1024)
    
    processes = []
    for i in range(100):
        p = Process([], config)
        p.pid = i
        memory_manager.create_process_memory(p)
        processes.append(p)
    
    memory_manager.write(processes[0], 100, 42)
    
    violations = 0
    translations = 0
    
    for i in range(1, 100):
        try:
            translations += 1
            val = memory_manager.read(processes[i], 100)
            if val == 42:
                violations += 1
        except Exception:
            pass

    print(f"Processes tested:\n100\n")
    print(f"Isolation violations:\n{violations}\n")
    print(f"Page translations:\n{translations}\n")

    print("Heap Benchmark\n")
    import time
    from core.memory.heap import HeapManager
    heap_manager = HeapManager(memory_manager)
    
    alloc_times = []
    free_times = []
    
    ptrs = {p.pid: [] for p in processes}
    for p in processes:
        for _ in range(10):
            t0 = time.perf_counter()
            ptr = heap_manager.allocate(p, 50)
            t1 = time.perf_counter()
            alloc_times.append(t1 - t0)
            ptrs[p.pid].append(ptr)
            
    peak_heap = len(heap_manager.heap_table)
    
    for p in processes:
        for ptr in ptrs[p.pid]:
            t0 = time.perf_counter()
            heap_manager.free(p, ptr)
            t1 = time.perf_counter()
            free_times.append(t1 - t0)
            
    avg_alloc = sum(alloc_times) / len(alloc_times) * 1000
    avg_free = sum(free_times) / len(free_times) * 1000
    memory_reclaimed = 1000 - len([b for b in heap_manager.heap_table.values() if b["allocated"]])
    
    print(f"Processes: 100")
    print(f"Allocations: 1000")
    print(f"Average allocation time: {avg_alloc:.4f} ms")
    print(f"Average free time: {avg_free:.4f} ms")
    print(f"Peak heap usage: {peak_heap} blocks")
    print(f"Memory reclaimed: {memory_reclaimed} blocks\n")

if __name__ == "__main__":
    run()
