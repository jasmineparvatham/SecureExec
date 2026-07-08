import unittest
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.vm.config import VMConfig
from core.errors import VerificationError

class TestLoopAnalysis(unittest.TestCase):
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
        self.assertTrue(report.detected_loops >= 1)
        self.assertTrue(report.bounded_loops >= 1)

    def test_infinite_loop_rejected(self):
        code = """
        int main() {
            int i = 0;
            while(i < 100) {
                print(i);
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(prog)
        self.assertIn("Potential infinite execution detected", str(ctx.exception))

    def test_nested_bounded_loops_accepted(self):
        code = """
        int main() {
            int i = 0;
            int j;
            while(i < 10) {
                j = 0;
                while(j < 10) {
                    j = j + 1;
                }
                i = i + 1;
            }
            return 0;
        }
        """
        prog = compile_c_subset(code)
        report = self.verifier.verify(prog)
        self.assertTrue(report.passed)
        self.assertTrue(report.detected_loops >= 2)

if __name__ == '__main__':
    unittest.main()
