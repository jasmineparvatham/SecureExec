import unittest
import io
import sys
from os_layer.scheduler.scheduler import Scheduler
from core.process.process import Process
from core.vm.config import VMConfig
from verifier.verifier import Verifier
from core.errors import VerificationError

class TestSyscalls(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        self.scheduler.debug = False
        self.verifier = Verifier(VMConfig())

    def test_print_syscall(self):
        program = [
            ("SYSCALL", "PRINT", "Hello, World!"),
            ("HALT",)
        ]
        self.verifier.verify(program)
        p = Process(program)
        
        self.scheduler.load_processes([p])
        self.scheduler.run_all()
        
        self.assertIn("Hello, World!", p.program_output)
        self.assertEqual(p.syscalls_executed, 1)
        self.assertEqual(p.last_syscall, "PRINT")
        self.assertEqual(p.resource_requests, 1)

    def test_get_time_syscall(self):
        program = [
            ("SYSCALL", "GET_TIME"),
            ("HALT",)
        ]
        self.verifier.verify(program)
        p = Process(program)
        self.scheduler.load_processes([p])
        
        self.scheduler.current_time = 42
        self.scheduler.run_all()
        
        self.assertEqual(p.registers["R0"], 42)

    def test_allocate_memory_syscall(self):
        program = [
            ("SYSCALL", "ALLOCATE_MEMORY", 16),
            ("HALT",)
        ]
        self.verifier.verify(program)
        p = Process(program, config=VMConfig(memory_size=16))
        self.scheduler.load_processes([p])
        self.scheduler.run_all()
        
        self.assertEqual(p.virtual_memory_size, 32)
        # mapping is cleared when process terminates, so it should be empty
        self.assertEqual(len(p.page_table.mapping), 0)

    def test_create_process_syscall(self):
        child_program = [("HALT",)]
        program = [
            ("SYSCALL", "CREATE_PROCESS", child_program),
            ("HALT",)
        ]
        self.verifier.verify(program)
        p = Process(program)
        self.scheduler.load_processes([p])
        
        self.scheduler.run_all()
        
        self.assertEqual(len(self.scheduler.completed_processes), 2)
        child_pid = p.registers["R0"]
        child_found = any(proc.pid == child_pid for proc in self.scheduler.completed_processes)
        self.assertTrue(child_found)

    def test_invalid_syscall_rejection(self):
        program = [
            ("SYSCALL", "DELETE_FILES"),
            ("HALT",)
        ]
        with self.assertRaises(VerificationError):
            self.verifier.verify(program)

if __name__ == "__main__":
    unittest.main()
