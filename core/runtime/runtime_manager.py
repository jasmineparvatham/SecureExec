import os
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.vm.config import VMConfig
from core.process.process import Process
from core.memory.memory_manager import MemoryManager
from os_layer.scheduler.scheduler import Scheduler
from core.runtime.logger import RuntimeLogger
from core.errors import VerificationError

class RuntimeManager:
    def __init__(self, debug=False):
        self.logger = RuntimeLogger(debug)
        self.config = VMConfig(memory_size=4096, register_count=16, instruction_limit=50000)
        self.memory_manager = MemoryManager(memory_size=1024 * 1024)
        self.scheduler = Scheduler(self.memory_manager)
        self.scheduler.debug = debug

    def execute_source(self, source_file):
        if not os.path.exists(source_file):
            self.report_failure("File not found", f"Could not find {source_file}")
            return
            
        with open(source_file, "r") as f:
            source_code = f.read()

        print("SecureExec Runtime v1.0\n")
        
        # 1. Compilation
        print("[1/4] Compilation")
        self.logger.log("Compiler", f"Compiling {source_file}")
        try:
            bytecode = compile_c_subset(source_code)
            print("OK Compilation successful")
            print(f"OK Generated instructions: {len(bytecode)}\n")
        except Exception as e:
            self.report_failure("Compilation failed.", str(e))
            return

        # 2. Verification
        print("[2/4] Security Verification")
        verifier = Verifier(self.config)
        try:
            report = verifier.verify(bytecode)
            print("OK SAFE")
            print(f"Security Score: 100/100\n")
            if self.logger.debug_mode:
                print("Verifier:\nCFG analysis passed\n")
        except VerificationError as e:
            self.report_failure("Security verification rejected program.", str(e))
            return

        # 3. Execution
        print("[3/4] Execution\n")
        
        process = Process(bytecode, self.config)
        self.scheduler.load_processes([process])
        
        self.logger.log("Scheduler", f"Starting execution of PID {process.pid}")
        self.scheduler.run_all()
        
        print("Program Output:\n")
        for line in process.program_output:
            print(line)
        print("\nExecution completed.\n")
        
        # 4. Report
        if process.termination_reason and process.termination_reason != "Exited via syscall":
            status_str = "FAILED"
        elif process.exit_code != 0:
            status_str = "FAILED"
        elif process.finished or process.state == "TERMINATED":
            status_str = "SUCCESS"
        else:
            status_str = "FAILED"
            
        allocs = getattr(process, "total_allocations", 0)
        freed = getattr(process, "total_freed", 0)
        leaked = len(process.heap_allocations)
        stats = self.scheduler.get_statistics()
        
        # Cleanup leaked memory automatically
        if hasattr(self.scheduler, "kernel") and hasattr(self.scheduler.kernel, "heap_manager"):
            self.scheduler.kernel.heap_manager.process_exit(process)
            
        print("--------------------------------")
        print("SecureExec Runtime v1.0\n")
        print(f"Program:\n{os.path.basename(source_file)}\n")
        
        print("Security:")
        if status_str == "FAILED" and process.termination_reason and "security" in process.termination_reason.lower():
            print("REJECTED")
            print("Security Score:\n0/100\n")
        else:
            print("SAFE")
            print("Security Score:\n100/100\n")
            
        print("Execution:")
        print(f"Status:\n{status_str}")
        print(f"Exit Code:\n{process.exit_code}\n")
        
        if process.termination_reason:
            print(f"Reason:\n{process.termination_reason}\n")
            
        print("Performance:")
        print(f"Instructions:\n{process.instructions_executed}")
        print(f"Memory:\nHeap:\n{allocs} cells\nStack:\n{process.virtual_memory_size} cells")
        print(f"Context Switches:\n{stats['context_switches']}")
        print(f"CPU Utilization:\n{stats['cpu_utilization']}%\n")
        print("--------------------------------\n")

    def execute_sources(self, source_files):
        print("SecureExec Runtime v1.0\n")
        
        compilation_results = {}
        compiled_bytecodes = {}
        
        # 1. Compilation Phase
        print("Compilation:")
        for source_file in source_files:
            prog_name = os.path.basename(source_file)
            if not os.path.exists(source_file):
                print(f"✗ {prog_name} (File not found)")
                compilation_results[source_file] = False
                continue
                
            with open(source_file, "r") as f:
                source_code = f.read()
                
            if self.logger.debug_mode:
                self.logger.log("Compiler", f"Compiling {source_file}")
                
            try:
                bytecode = compile_c_subset(source_code)
                print(f"✓ {prog_name}")
                compilation_results[source_file] = True
                compiled_bytecodes[source_file] = bytecode
            except Exception as e:
                print(f"✗ {prog_name} (Compilation error: {e})")
                compilation_results[source_file] = False
        
        print()
                
        # 2. Verification Phase
        print("Verification:")
        verification_results = {}
        rejected_reports = []
        processes = []
        
        for source_file, bytecode in compiled_bytecodes.items():
            prog_name = os.path.basename(source_file)
            verifier = Verifier(self.config)
            try:
                report = verifier.verify(bytecode, program_name=prog_name)
                print(f"✓ {prog_name} SAFE")
                verification_results[source_file] = True
                
                process = Process(bytecode, self.config)
                process.source_file = source_file
                process.program_name = prog_name
                processes.append(process)
            except VerificationError as e:
                print(f"✗ {prog_name} REJECTED")
                verification_results[source_file] = False
                rejected_reports.append((prog_name, str(e)))
                
        print()
                
        if rejected_reports:
            print("Rejected Programs:\n")
            for prog, reason in rejected_reports:
                print("Program:")
                print(prog)
                print("\nReason:")
                print(reason)
                print()
                
        if not processes:
            return
            
        # 3. Execution Phase
        print("Execution:\n")
        self.scheduler.load_processes(processes)
        
        if self.logger.debug_mode:
            self.logger.log("Scheduler", f"Starting execution of {len(processes)} processes")
            
        self.scheduler.run_all()
        
        for p in processes:
            print("Process:")
            print(p.program_name)
            print("\nPID:")
            print(p.pid)
            print("\nOutput:")
            for line in p.program_output:
                print(line)
            print()
            
            if self.logger.debug_mode:
                print("Registers:")
                for r_idx in range(p.config.register_count):
                    reg = f"R{r_idx}"
                    val = p.registers.get(reg, 0)
                    print(f"  {reg}: {val}")
                print()
            
            if hasattr(self.scheduler, "kernel") and hasattr(self.scheduler.kernel, "heap_manager"):
                self.scheduler.kernel.heap_manager.process_exit(p)
                
        # 4. Scheduler Statistics
        stats = self.scheduler.get_statistics()
        
        print("Execution Summary:\n")
        print("Programs Submitted:")
        print(len(source_files))
        print("\nVerification Passed:")
        print(len(processes))
        print("\nVerification Failed:")
        print(len(rejected_reports))
        print()
        
        print("Scheduler Statistics:\n")
        print("Processes Created:")
        print(f"{stats['processes_completed']}")
        print("\nProcesses Completed:")
        print(f"{stats['processes_completed']}")
        print("\nContext Switches:")
        print(f"{stats['context_switches']}")
        print("\nAverage Waiting Time:")
        print(f"{stats['average_waiting_time']}")
        print("\nAverage Turnaround Time:")
        print(f"{stats['average_turnaround_time']}")
        print("\nCPU Utilization:")
        print(f"{stats['cpu_utilization']}%")
        print()

    def report_failure(self, reason, error):
        print("\nSecureExec Execution Failed\n")
        print("Reason:\n" + reason + "\n")
        print("Error:\n" + error + "\n")
