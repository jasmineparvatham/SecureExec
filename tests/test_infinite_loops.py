import unittest
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.vm.config import VMConfig
from core.errors import VerificationError

class TestInfiniteLoops(unittest.TestCase):
    def setUp(self):
        self.config = VMConfig(instruction_limit=1000)
        self.verifier = Verifier(self.config)

    def test_bounded_loop_accepted(self):
        code = """
        int main() {
            int i = 0;
            while(i < 10) {
                i = i + 1;
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        report = self.verifier.verify(prog)
        self.assertTrue(report.passed)

    def test_constant_loop_rejected(self):
        code = """
        int main() {
            while(1) {
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(prog)
        self.assertIn("Potential infinite execution detected", str(ctx.exception))
        self.assertIn("no terminating path", str(ctx.exception))

    def test_unmodified_variable_loop_rejected(self):
        code = """
        int main() {
            int i = 0;
            int x = 0;
            while(i < 10) {
                x = x + 1;
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(prog)
        self.assertIn("Potential infinite execution detected", str(ctx.exception))
        
if __name__ == '__main__':
    unittest.main()
