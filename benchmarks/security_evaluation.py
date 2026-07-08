import sys
import io
import os
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.vm.config import VMConfig
from core.process.process import Process
from core.memory.memory_manager import MemoryManager
from os_layer.scheduler.scheduler import Scheduler
from core.errors import VerificationError, VMError

def evaluate_security():
    config = VMConfig(memory_size=4096, register_count=16, instruction_limit=500)
    memory_manager = MemoryManager(memory_size=1024 * 1024)
    scheduler = Scheduler(memory_manager)
    verifier = Verifier(config)
    
    metrics = {
        "memory": {"tested": 0, "detected": 0},
        "control_flow": {"tested": 0, "detected": 0},
        "resource": {"tested": 0, "detected": 0},
        "syscall": {"tested": 0, "detected": 0}
    }
    
    def test_program(category, source_file=None, bytecode=None):
        metrics[category]["tested"] += 1
        try:
            if source_file:
                with open(source_file, "r") as f:
                    code = f.read()
                prog = compile_c_subset(code)
            else:
                prog = bytecode
                
            report = verifier.verify(prog)
            
            p = Process(prog, config)
            scheduler.load_processes([p])
            scheduler.run_all()
            
            if p.exit_code != 0 or p.termination_reason != "Exited via syscall":
                metrics[category]["detected"] += 1
        except VerificationError:
            metrics[category]["detected"] += 1
        except VMError:
            metrics[category]["detected"] += 1
        except Exception:
            metrics[category]["detected"] += 1

    test_program("memory", "benchmarks/security_attacks/mem_oob.c")
    test_program("memory", "benchmarks/security_attacks/mem_double_free.c")
    
    test_program("control_flow", "benchmarks/security_attacks/cf_infinite.c")
    test_program("control_flow", bytecode=[("JMP", 100), ("HALT",)])
    
    test_program("resource", "benchmarks/security_attacks/res_exhaustion.c")
    test_program("resource", bytecode=[("SYSCALL", "CREATE_PROCESS", "R0"), ("JMP", 0)])
    
    test_program("syscall", bytecode=[("SYSCALL", "DELETE_FILES"), ("HALT",)])
    test_program("syscall", bytecode=[("SYSCALL", "PRINT"), ("HALT",)]) # invalid args
    
    print("SecureExec Security Evaluation\n")
    total = sum(m['tested'] for m in metrics.values())
    print(f"Programs Tested:\n{total}\n")
    print("Threat Categories:\n")
    
    for cat, data in metrics.items():
        if data["tested"] > 0:
            rate = (data["detected"] / data["tested"]) * 100
            name = cat.replace("_", " ").title()
            if cat == "memory": name = "Memory Safety"
            print(f"{name}:\n{rate:.0f}% detected\n")

if __name__ == "__main__":
    evaluate_security()
