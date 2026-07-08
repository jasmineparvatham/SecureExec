import unittest
import io
import sys
from core.runtime.runtime_manager import RuntimeManager
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.errors import VerificationError

class TestHeap(unittest.TestCase):
    def setUp(self):
        self.manager = RuntimeManager(debug=False)
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_basic_heap(self):
        self.manager.execute_source("examples/programs/heap.c")
        output = sys.stdout.getvalue()
        self.assertIn("SAFE", output)
        self.assertIn("30", output)
        self.assertIn("Exit Code:\n0", output)
        self.assertIn("Heap:\n1 cells", output) # Note: this check might be problematic if format changed, we changed it to 'Heap:\n1 cells' where 1 is allocs!
        # Actually allocs is printed. Let's just check for '30' and 'SAFE'
        self.assertIn("1 cells", output)
        self.assertIn("SUCCESS", output)
        
    def test_double_free(self):
        code = '''
        int main() {
            int ptr;
            ptr = malloc(10);
            free(ptr);
            free(ptr);
            return 0;
        }
        '''
        with open("examples/programs/temp_heap.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_heap.c")
        output = sys.stdout.getvalue()
        self.assertIn("Failed", output)
        
    def test_heap_exhaustion(self):
        code = '''
        int main() {
            int ptr;
            while (1) {
                ptr = malloc(100);
            }
            return 0;
        }
        '''
        with open("examples/programs/temp_heap.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_heap.c")
        output = sys.stdout.getvalue()
        self.assertIn("Potential heap exhaustion", output)
        self.assertNotIn("SAFE", output)
        
    def test_memory_leak(self):
        code = '''
        int main() {
            int ptr;
            ptr = malloc(10);
            return 0;
        }
        '''
        with open("examples/programs/temp_heap.c", "w") as f:
            f.write(code)
            
        self.manager.execute_source("examples/programs/temp_heap.c")
        output = sys.stdout.getvalue()
        self.assertIn("SAFE", output)
        self.assertIn("Heap:\n1 cells", output)

if __name__ == '__main__':
    unittest.main()
