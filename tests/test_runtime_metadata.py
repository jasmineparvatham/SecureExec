import unittest
import io
import sys
import re
from cli import run_programs
from core.runtime.runtime_manager import RuntimeManager
from compiler.c_subset_compiler import compile_c_subset

class TestRuntimeMetadata(unittest.TestCase):

    def setUp(self):
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_run_programs_preserves_program_name(self):
        # We'll use the compiled demo bc files for this test if they exist.
        # Alternatively, we just write a tiny bc file for testing.
        bytecode = compile_c_subset("int main() { return 0; }")
        with open("tests/test_meta_1.bc", "w") as f:
            f.write(repr(bytecode))
        
        run_programs(["tests/test_meta_1.bc"])
        output = sys.stdout.getvalue()
        
        self.assertIn("✓ test_meta_1.bc SAFE", output)
        self.assertIn("Program:\ntest_meta_1.bc", output)
        
    def test_execute_sources_output_association(self):
        manager = RuntimeManager(debug=False)
        with open("tests/test_prog.c", "w") as f:
            f.write("int main() { print(42); return 0; }")
            
        manager.execute_sources(["tests/test_prog.c"])
        output = sys.stdout.getvalue()
        
        # Test Task 6 formatting
        self.assertIn("Process:\ntest_prog.c", output)
        self.assertRegex(output, r"PID:\n\d+")
        self.assertIn("Output:\n42", output)
        
    def test_run_programs_debug_mode(self):
        bytecode = compile_c_subset("int main() { return 0; }")
        with open("tests/test_meta_2.bc", "w") as f:
            f.write(repr(bytecode))
        
        sys.argv.append("--debug")
        run_programs(["tests/test_meta_2.bc", "--debug"])
        sys.argv.remove("--debug")
        
        output = sys.stdout.getvalue()
        
        self.assertIn("Registers:", output)
        self.assertRegex(output, r"PID \d+ entered Q1")
        
    def test_rejected_summary_cli(self):
        with open("tests/test_meta_bad.bc", "w") as f:
            f.write("[['LOAD_CONST', 0]]") # invalid program
            
        run_programs(["tests/test_meta_bad.bc"])
        output = sys.stdout.getvalue()
        
        self.assertIn("✗ test_meta_bad.bc REJECTED", output)
        self.assertIn("Rejected Programs:", output)
        self.assertIn("Program:\ntest_meta_bad.bc", output)

if __name__ == '__main__':
    unittest.main()
