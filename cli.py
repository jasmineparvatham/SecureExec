import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import ast

from core.process.process import Process
from os_layer.scheduler.scheduler import Scheduler
from core.vm.vm import Virtual_Machine
from verifier.verifier import Verifier
from core.errors import VMError, VerificationError


def print_help():
    help_text = """
SecureExec Runtime v1.0

USAGE
    python cli.py <command> [options] [files...]

COMMANDS

    execute
        Purpose: Compiles, verifies, and executes one or more C source files.
                 Flow: C Source → Compiler → Bytecode → Verifier → Kernel → Scheduler → VM
        Example: python cli.py execute examples/demo/hello.c
        Multiple Files: python cli.py execute examples/demo/hello.c examples/demo/heap.c
        Expected behavior: Shows compilation status, verification result, and detailed execution report per process.

    compile
        Purpose: Compiles one or more C source files into SecureExec bytecode without executing.
        Example: python cli.py compile examples/demo/hello.c
        Multiple Files: python cli.py compile examples/demo/hello.c examples/demo/heap.c
        Expected behavior: Generates .bc bytecode files alongside the source files and prints a summary.

    run
        Purpose: Executes one or more precompiled bytecode (.bc) files natively.
        Example: python cli.py run examples/demo/hello.bc
        Multiple Files: python cli.py run examples/demo/hello.bc examples/demo/heap.bc
        Expected behavior: Bypasses the compiler and immediately loads bytecode into the Verifier and Runtime.

    verify
        Purpose: Runs static security verification on a bytecode file without executing it.
        Example: python cli.py verify examples/demo/hello.bc
        Expected behavior: Outputs a detailed static analysis report showing validation checks (CFG, memory bounds).

OPTIONS

    --debug
        Purpose: Enables verbose debugging output.
        Applies to: execute, run
        Expected behavior: Shows queue transitions, context switches, scheduler decisions, process movement, and register states.

    --help, help, -h
        Purpose: Displays this help manual.
"""
    print(help_text.strip())


def load_program_from_file(filename):
    try:
        with open(filename, "r") as f:
            return ast.literal_eval(f.read())
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception:
        print("Error: Invalid bytecode format.")
        sys.exit(1)


def run_programs(filenames):
    import os
    verifier = Verifier()
    processes = []
    
    debug_mode = "--debug" in filenames
    if debug_mode:
        filenames = [f for f in filenames if f != "--debug"]

    print("Verification:")
    rejected_reports = []

    for file in filenames:
        prog_name = os.path.basename(file)
        try:
            program = load_program_from_file(file)
            report = verifier.verify(program, program_name=prog_name)
            print(f"✓ {prog_name} SAFE")

            p = Process(program)
            p.program_name = prog_name
            p.source_file = file
            processes.append(p)

        except VerificationError as e:
            print(f"✗ {prog_name} REJECTED")
            rejected_reports.append((prog_name, str(e)))

        except Exception as e:
            print(f"✗ {prog_name} REJECTED")
            rejected_reports.append((prog_name, str(e)))
            
    print()

    if rejected_reports:
        print("Rejected Programs:\n")
        for prog, reason in rejected_reports:
            print("Program:")
            print(prog)
            print("\nStatus:")
            print("REJECTED")
            print("\nReason:")
            print(reason)
            print()

    if not processes:
        return

    scheduler = Scheduler()
    scheduler.debug = debug_mode
    scheduler.load_processes(processes)
    scheduler.run_all()

    print("Execution completed.\n")

    for i, p in enumerate(processes):
        print("--------------------------------")
        print("Process Report\n")
        print("PID:")
        print(p.pid)
        print("\nProgram:")
        print(getattr(p, 'program_name', f"program_{i}.bc"))
        print("\nStatus:")
        print(p.state)
        print("\nExit Code:")
        print(p.exit_code)
        print("\nInstructions:")
        print(p.instructions_executed)
        print("\nCPU Time:")
        print(p.cpu_time_used)
        
        allocs = getattr(p, "total_allocations", 0)
        stack_size = p.virtual_memory_size - p.stack_pointer if p.stack_pointer > 0 else 0
        
        print("\nMemory:\n")
        print("Virtual Memory:")
        print(f"{p.virtual_memory_size} cells\n")
        print("Heap:")
        print(f"{allocs} cells\n")
        print("Stack:")
        print(f"{stack_size} cells\n")
        
        print("Program Output:\n")
        for line in p.program_output:
            print(line)
        print()
        print("--------------------------------\n")

        if debug_mode:
            print("\nRegisters:")
            for r_idx in range(p.config.register_count):
                reg = f"R{r_idx}"
                val = p.registers.get(reg, 0)
                print(f"  {reg}: {val}")
                
    stats = scheduler.get_statistics()
    
    print("Execution Summary:\n")
    print("Programs Submitted:")
    print(len(filenames))
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


if __name__ == "__main__":

    if len(sys.argv) < 2 or sys.argv[1] in ["help", "--help", "-h"]:
        print_help()
        sys.exit(0)

    command = sys.argv[1]

    if command == "help":
        print_help()
        
    elif command == "compile":
        if len(sys.argv) < 3:
            print("Error: Missing source file.")
            print("Usage: python cli.py compile <program1.c> [program2.c ...]")
            sys.exit(1)
        
        source_files = sys.argv[2:]
        from compiler.c_subset_compiler import compile_c_subset
        import os
        
        print("SecureExec Compiler v1.0\n")
        print("Compilation:\n")
        
        successful = 0
        failed = 0
        
        for source_file in source_files:
            file_base = os.path.basename(source_file)
            try:
                with open(source_file, "r") as f:
                    code = f.read()
            except FileNotFoundError:
                print(f"✗ {file_base}")
                print("  Compilation Failed")
                print("\nReason:")
                print(f"File '{source_file}' not found.\n")
                failed += 1
                continue
                
            try:
                bytecode = compile_c_subset(code)
            except Exception as e:
                print(f"✗ {file_base}")
                print("  Compilation Failed")
                print("\nReason:")
                if hasattr(e, 'lineno'):
                    print(f"Compilation failed at line {e.lineno}:\n{e}\n")
                else:
                    print(f"{e}\n")
                failed += 1
                continue
                
            output_file = source_file.replace(".c", ".bc")
            if not output_file.endswith(".bc"):
                output_file += ".bc"
                
            with open(output_file, "w") as f:
                f.write(f"# Compiler Metadata\n# source_file: {source_file}\n# generated_bytecode_size: {len(bytecode)}\n")
                f.write("[\n" + ",\n".join("    " + repr(instr) for instr in bytecode) + "\n]\n")
                
            out_base = os.path.basename(output_file)
            print(f"✓ {file_base}")
            print("  Generated:")
            print(f"  {out_base}\n")
            successful += 1
            
        print("Compilation Summary:\n")
        print("Programs Submitted:")
        print(len(source_files))
        print("\nSuccessful:")
        print(successful)
        print("\nFailed:")
        print(failed)
        print()

    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: Missing program file.")
            print("Usage: python3 cli.py verify <program.bc>")
            sys.exit(1)

        file = sys.argv[2]
        program = load_program_from_file(file)
        verifier = Verifier()
        try:
            report = verifier.verify(program)
            print(f"{file}: Verification successful")
            print(report)
        except VerificationError as e:
            print(f"Verification rejected for {file}:")
            print(e)
            sys.exit(1)

    elif command == "run":
        if len(sys.argv) < 3:
            print("Error: Missing program file(s).")
            print("Usage: python3 cli.py run <program1.bc> <program2.bc> ...")
            sys.exit(1)

        run_programs(sys.argv[2:])

    elif command == "execute":
        if len(sys.argv) < 3:
            print("Error: Missing program file(s).")
            print("Usage: python3 cli.py execute <program1.c> <program2.c> ... [--debug]")
            sys.exit(1)

        source_files = [arg for arg in sys.argv[2:] if arg != "--debug"]
        debug_mode = "--debug" in sys.argv
        
        from core.runtime.runtime_manager import RuntimeManager
        manager = RuntimeManager(debug=debug_mode)
        manager.execute_sources(source_files)

    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)
