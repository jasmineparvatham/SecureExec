import unittest
from compiler.c_subset_compiler import compile_c_subset
from core.vm.config import VMConfig
from core.process.process import Process
from core.memory.memory_manager import MemoryManager
from os_layer.scheduler.scheduler import Scheduler

class TestExpression(unittest.TestCase):
    def test_array_expression(self):
        with open("examples/programs/expression_test.c", "r") as f:
            code = f.read()
            
        prog = compile_c_subset(code)
        config = VMConfig(memory_size=4096, register_count=16, instruction_limit=1000)
        memory_manager = MemoryManager(memory_size=1024 * 1024)
        scheduler = Scheduler(memory_manager)
        
        p = Process(prog, config)
        scheduler.load_processes([p])
        scheduler.run_all()
        
        self.assertIn("6", p.program_output)
        
    def test_complex_precedence(self):
        code = """
        int main() {
            int a = 10;
            int b = 2;
            int c = 3;
            int d = a + b * c;
            int e = (a + b) * c;
            print(d);
            print(e);
            return 0;
        }
        """
        prog = compile_c_subset(code)
        config = VMConfig(memory_size=4096, register_count=16, instruction_limit=1000)
        memory_manager = MemoryManager(memory_size=1024 * 1024)
        scheduler = Scheduler(memory_manager)
        
        p = Process(prog, config)
        scheduler.load_processes([p])
        scheduler.run_all()
        
        self.assertIn("16", p.program_output)
        self.assertIn("36", p.program_output)

if __name__ == '__main__':
    unittest.main()
