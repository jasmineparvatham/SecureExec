import unittest
import io
import sys
from core.runtime.runtime_manager import RuntimeManager
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.errors import VerificationError

class TestArrays(unittest.TestCase):
    def setUp(self):
        self.manager = RuntimeManager(debug=False)
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_basic_arrays(self):
        self.manager.execute_source("examples/programs/arrays.c")
        output = sys.stdout.getvalue()
        self.assertIn("Compilation successful", output)
        self.assertIn("SAFE", output)
        self.assertIn("30", output)
        self.assertIn("Exit Code:\n0", output)
        
    def test_dynamic_index(self):
        code = '''
        int main() {
            int arr[10];
            int i = 0;
            while (i < 10) {
                arr[i] = i;
                i = i + 1;
            }
            print(arr[5]);
            return 0;
        }
        '''
        with open("examples/programs/temp_array_test.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_array_test.c")
        output = sys.stdout.getvalue()
        self.assertIn("SAFE", output)
        self.assertIn("5", output)
        
    def test_out_of_bounds_static(self):
        code = '''
        int main() {
            int arr[5];
            arr[10] = 20;
            return 0;
        }
        '''
        with open("examples/programs/temp_array_test.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_array_test.c")
        output = sys.stdout.getvalue()
        self.assertIn("Static array bounds detection failed", output)
        self.assertNotIn("SAFE", output)
        
    def test_out_of_bounds_dynamic(self):
        code = '''
        int main() {
            int arr[5];
            int i = 10;
            arr[i] = 20;
            return 0;
        }
        '''
        with open("examples/programs/temp_array_test.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_array_test.c")
        output = sys.stdout.getvalue()
        self.assertIn("SAFE", output)
        self.assertIn("FAILED", output)
        self.assertIn("Array index out of bounds", output)
        
    def test_large_allocation(self):
        code = '''
        int main() {
            int huge[999999999];
            return 0;
        }
        '''
        with open("examples/programs/temp_array_test.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_array_test.c")
        output = sys.stdout.getvalue()
        self.assertIn("exceeds memory limit", output)
        self.assertNotIn("SAFE", output)

if __name__ == '__main__':
    unittest.main()
