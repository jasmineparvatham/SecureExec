import unittest
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.vm.config import VMConfig
from core.errors import VerificationError

class TestHeapAnalysis(unittest.TestCase):
    def setUp(self):
        self.config = VMConfig(instruction_limit=1000)
        self.verifier = Verifier(self.config)

    def test_malloc_outside_loop_accepted(self):
        code = """
        int main() {
            int x = 0;
            int ptr;
            ptr = malloc(10);
            while (x < 10) {
                x = x + 1;
            }
            free(ptr);
            return 0;
        }
        """
        prog = compile_c_subset(code)
        # Should pass
        report = self.verifier.verify(prog)
        self.assertTrue(report.passed)

    def test_malloc_inside_loop_without_free_rejected(self):
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                int ptr;
                ptr = malloc(100);
                x = x + 1;
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(prog)
        self.assertIn("Potential heap exhaustion detected.", str(ctx.exception))

    def test_multiple_allocations_with_frees_accepted(self):
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                int ptr;
                ptr = malloc(10);
                free(ptr);
                x = x + 1;
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        report = self.verifier.verify(prog)
        self.assertTrue(report.passed)

if __name__ == '__main__':
    unittest.main()
