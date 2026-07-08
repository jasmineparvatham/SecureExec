import unittest
import io
import sys
import re
from core.runtime.runtime_manager import RuntimeManager
from cli import run_programs
from compiler.c_subset_compiler import compile_c_subset

class TestRuntimeReporting(unittest.TestCase):

    def setUp(self):
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_execute_sources_normal_output(self):
        manager = RuntimeManager(debug=False)
        files = [
            "examples/demo/multiprocess/program1.c",
            "examples/demo/multiprocess/program2.c",
            "examples/demo/multiprocess/program3.c"
        ]
        manager.execute_sources(files)
        output = sys.stdout.getvalue()
        
        # Compilation status
        self.assertIn("Compilation:", output)
        self.assertIn("✓ program1.c", output)
        self.assertIn("✓ program2.c", output)
        
        # Verification status
        self.assertIn("Verification:", output)
        self.assertIn("✓ program1.c SAFE", output)
        
        # Program execution blocks
        self.assertIn("Process:\nprogram1.c", output)
        self.assertIn("Process:\nprogram2.c", output)
        self.assertIn("Process:\nprogram3.c", output)
        
        # Registers hidden normally
        self.assertNotIn("Registers:", output)
        self.assertNotIn("R0:", output)
        
        # Scheduler logs hidden normally
        self.assertNotIn("Context Switch:", output)
        self.assertNotIn("Q1", output)
        
        # Check Scheduler Statistics at the end
        self.assertIn("Scheduler Statistics:", output)
        self.assertIn("Processes Created:\n3", output)
        self.assertIn("CPU Utilization:", output)

    def test_execute_sources_debug_output(self):
        manager = RuntimeManager(debug=True)
        files = ["examples/demo/multiprocess/program3.c"]
        manager.execute_sources(files)
        output = sys.stdout.getvalue()
        
        # Debug logs visible
        self.assertIn("[Scheduler]:", output)
        self.assertIn("Q1", output)
        
        # Registers visible in debug
        self.assertIn("Registers:", output)
        self.assertIn("R0:", output)

    def test_failed_verification_identifies_correct_file(self):
        manager = RuntimeManager(debug=False)
        # Using a file that will fail verification (heap exhaustion / uninitialized)
        # We will create a temp file for this test.
        with open("examples/demo/multiprocess/bad.c", "w") as f:
            f.write("int main() { while(1) {} return 0; }")
            
        manager.execute_sources(["examples/demo/multiprocess/bad.c"])
        output = sys.stdout.getvalue()
        
        self.assertIn("✗ bad.c REJECTED", output)
        self.assertIn("Rejected Programs:", output)
        self.assertIn("Program:\nbad.c", output)

if __name__ == '__main__':
    unittest.main()
