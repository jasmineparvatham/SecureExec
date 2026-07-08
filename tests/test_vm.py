import unittest
from core.vm.vm import Virtual_Machine
from core.process.process import Process


class TestVM(unittest.TestCase):

    def test_add(self):
        program = [
            ("LOAD", "R1", 10),
            ("LOAD", "R2", 20),
            ("ADD", "R3", "R1", "R2"),
            ("HALT",)
        ]

        vm = Virtual_Machine()
        p = Process(program)
        vm.memory_manager.create_process_memory(p)
        vm.run(p)

        self.assertEqual(p.registers["R3"], 30)

    def test_run_step(self):
        program = [
            ("LOAD", "R1", 5),
            ("LOAD", "R2", 7),
            ("ADD", "R3", "R1", "R2"),
            ("HALT",)
        ]

        vm = Virtual_Machine()
        p = Process(program)
        vm.memory_manager.create_process_memory(p)

        process, used, finished = vm.run_step(p, 2)
        self.assertEqual(used, 2)
        self.assertFalse(finished)
        self.assertEqual(process.ip, 2)
        self.assertEqual(process.registers["R1"], 5)
        self.assertEqual(process.registers["R2"], 7)

        process, used, finished = vm.run_step(p, 2)
        self.assertEqual(used, 2)
        self.assertTrue(finished)
        self.assertEqual(process.registers["R3"], 12)


if __name__ == "__main__":
    unittest.main()
