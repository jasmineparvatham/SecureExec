import unittest
from core.vm.vm import Virtual_Machine
from core.process.process import Process
from os_layer.scheduler.scheduler import Scheduler
from verifier.verifier import Verifier
from core.errors import VMError, VerificationError

class TestRegression(unittest.TestCase):

    def setUp(self):
        self.verifier = Verifier()
        self.scheduler = Scheduler()

    def test_arithmetic_and_memory(self):
        program = [
            ("LOAD", "R0", 15),
            ("LOAD", "R1", 20),
            ("ADD", "R2", "R0", "R1"), # 35
            ("STORE", "R2", 10),
            ("LOADM", "R3", 10),
            ("HALT",)
        ]
        self.verifier.verify(program)
        p = Process(program)
        self.scheduler.load_processes([p])
        self.scheduler.run_all()
        self.assertEqual(p.registers["R3"], 35)

    def test_jumps(self):
        program = [
            ("LOAD", "R0", 0),
            ("LOAD", "R1", 5),
            ("ADD", "R0", "R0", "R1"), # IP: 2
            ("DEC", "R1"),
            ("JNZ", "R1", 2),
            ("HALT",)
        ]
        self.verifier.verify(program)
        p = Process(program)
        self.scheduler.load_processes([p])
        self.scheduler.run_all()
        self.assertEqual(p.registers["R0"], 15)

    def test_unsafe_uninitialized(self):
        program = [
            ("ADD", "R1", "R2", "R3"),
            ("HALT",)
        ]
        with self.assertRaises(VerificationError):
            self.verifier.verify(program)

    def test_unsafe_no_halt(self):
        program = [
            ("LOAD", "R0", 1),
            ("INC", "R0")
        ]
        with self.assertRaises(VerificationError):
            self.verifier.verify(program)

    def test_multiple_processes(self):
        p1 = Process([("LOAD", "R0", 10), ("HALT",)])
        p2 = Process([("LOAD", "R1", 20), ("HALT",)])
        self.scheduler.load_processes([p1, p2])
        self.scheduler.run_all()
        self.assertEqual(p1.registers["R0"], 10)
        self.assertEqual(p2.registers["R1"], 20)

if __name__ == "__main__":
    unittest.main()
