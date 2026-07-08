import time
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier

def run():
    print("Compiler Benchmark\n")
    print("Programs:\n100\n")
    
    code = """
    int main() {
        int x = 10;
        int y = 20;
        print(x + y);
    }
    """
    
    start_time = time.perf_counter()
    bytecodes = []
    for _ in range(100):
        bytecodes.append(compile_c_subset(code))
    end_time = time.perf_counter()
    
    avg_compile_time = (end_time - start_time) * 1000 / 100
    avg_size = sum(len(b) for b in bytecodes) / 100
    
    verifier = Verifier()
    success = 0
    for b in bytecodes:
        if verifier.verify(b).passed:
            success += 1
            
    print(f"Average Compilation Time:\n{avg_compile_time:.2f} ms\n")
    print(f"Average Bytecode Size:\n{avg_size:.0f} instructions\n")
    print(f"Successful Verification:\n{success / 100 * 100:.0f}%\n")

if __name__ == "__main__":
    run()
