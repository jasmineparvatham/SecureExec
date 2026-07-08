import unittest
import io
import sys
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from os_layer.scheduler.scheduler import Scheduler
from core.process.process import Process
from core.vm.config import VMConfig

class TestCompiler(unittest.TestCase):
    def setUp(self):
        self.verifier = Verifier()

    def test_variable_and_arithmetic_compilation(self):
        code = '''
        int main() {
            int x = 10;
            int y = 5;
            int z = x + y;
            print(z);
        }
        '''
        bytecode = compile_c_subset(code)
        
        report = self.verifier.verify(bytecode)
        self.assertTrue(report.passed)
        
        p = Process(bytecode, config=VMConfig())
        scheduler = Scheduler()
        scheduler.debug = False
        scheduler.load_processes([p])
        
        scheduler.run_all()
        self.assertIn("15", p.program_output)

    def test_loop_compilation(self):
        code = '''
        int main() {
            int i = 0;
            while (i < 3) {
                print(i);
                i = i + 1;
            }
        }
        '''
        bytecode = compile_c_subset(code)
        
        report = self.verifier.verify(bytecode)
        self.assertTrue(report.passed)
        
        p = Process(bytecode, config=VMConfig())
        scheduler = Scheduler()
        scheduler.debug = False
        scheduler.load_processes([p])
        
        scheduler.run_all()
        
        output = p.program_output
        self.assertIn("0", output)
        self.assertIn("1", output)
        self.assertIn("2", output)
        self.assertNotIn("3", output)

    def test_invalid_syntax_rejection(self):
        code = '''
        int main() {
            int x = 10
        }
        '''
        with self.assertRaises(SyntaxError):
            compile_c_subset(code)

if __name__ == "__main__":
    unittest.main()
