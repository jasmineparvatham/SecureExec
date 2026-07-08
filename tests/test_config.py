import unittest
from core.vm.config import VMConfig
from core.process.process import Process
from core.vm.vm import Virtual_Machine
from verifier.verifier import Verifier
from core.errors import VMError, VerificationError

class TestConfig(unittest.TestCase):

    def test_custom_memory(self):
        config = VMConfig(memory_size=1024)
        p = Process([], config)
        self.assertEqual(p.virtual_memory_size, 1024)

    def test_custom_registers(self):
        config = VMConfig(register_count=16)
        p = Process([], config)
        self.assertIn("R15", p.registers)
        self.assertEqual(len(p.registers), 16)

    def test_execution_limit(self):
        config = VMConfig(instruction_limit=5)
        program = [
            ("LOAD", "R0", 1),
            ("INC", "R0"),
            ("INC", "R0"),
            ("INC", "R0"),
            ("INC", "R0"),
            ("INC", "R0"),
            ("INC", "R0"),
            ("HALT",)
        ]
        p = Process(program, config)
        vm = Virtual_Machine()
        vm.memory_manager.create_process_memory(p)
        with self.assertRaises(VMError) as context:
            vm.run(p)
        self.assertTrue("Instruction limit exceeded" in str(context.exception))

    def test_memory_boundary(self):
        config = VMConfig(memory_size=10)
        program = [
            ("LOAD", "R0", 5),
            ("STORE", "R0", 15), # Out of bounds
            ("HALT",)
        ]
        
        verifier = Verifier(config)
        with self.assertRaises(VerificationError) as context:
            verifier.verify(program)
        self.assertTrue("Invalid memory write" in str(context.exception))
        
        # Test runtime bounds too
        p = Process(program, config)
        vm = Virtual_Machine()
        vm.memory_manager.create_process_memory(p)
        with self.assertRaises(VMError):
            vm.run(p)

    def test_backwards_compatibility(self):
        program = [
            ("LOAD", "R1", 10),
            ("HALT",)
        ]
        verifier = Verifier()
        verifier.verify(program)
        p = Process(program)
        vm = Virtual_Machine()
        vm.memory_manager.create_process_memory(p)
        vm.run(p)
        self.assertEqual(p.registers["R1"], 10)

if __name__ == "__main__":
    unittest.main()
