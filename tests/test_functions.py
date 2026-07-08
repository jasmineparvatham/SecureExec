import unittest
import io
import sys
from core.runtime.runtime_manager import RuntimeManager
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.errors import VerificationError

class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.manager = RuntimeManager(debug=False)
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_function_execution(self):
        self.manager.execute_source("examples/programs/functions.c")
        output = sys.stdout.getvalue()
        
        self.assertIn("Compilation successful", output)
        self.assertIn("SAFE", output)
        self.assertIn("30", output)
        self.assertIn("Exit Code:\n0", output)
        
    def test_recursive_function(self):
        code = '''
        int fib(int n) {
            if (n < 2) {
                return n;
            }
            return fib(n - 1) + fib(n - 2);
        }
        
        int main() {
            print(fib(5));
            return 0;
        }
        '''
        with open("examples/programs/temp_test.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_test.c")
        output = sys.stdout.getvalue()
        
        self.assertIn("Compilation successful", output)
        self.assertIn("SAFE", output)
        self.assertIn("5", output)
        
    def test_verifier_stack_exhaustion(self):
        # We can test stack overflow at runtime
        code = '''
        int overflow() {
            return overflow();
        }
        int main() {
            return overflow();
        }
        '''
        with open("examples/programs/temp_test.c", "w") as f:
            f.write(code)
            
        from core.vm.config import VMConfig
        config = VMConfig()
        config.max_call_depth = 10
        self.manager = RuntimeManager(debug=False)
        # Assuming RuntimeManager doesn't take config, we can just patch it later if needed.
        # But actually, the VM inside manager reads process.config.
        # Let's just create a custom process or change the system default config.

        self.manager.execute_source("examples/programs/temp_test.c")
        output = sys.stdout.getvalue()
        self.assertIn("FAILED", output)
        self.assertIn("Stack overflow", output)

if __name__ == '__main__':
    unittest.main()
