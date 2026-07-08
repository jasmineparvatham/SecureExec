import unittest
from verifier.verifier import Verifier
from core.errors import VerificationError

class TestVerifierSecurity(unittest.TestCase):
    def setUp(self):
        self.verifier = Verifier()

    def test_invalid_instruction_rejection(self):
        program = [("HACK", "R0"), ("HALT",)]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Unknown instruction", str(ctx.exception))

    def test_unsafe_syscall_rejection(self):
        program = [("SYSCALL", "DELETE_FILES"), ("HALT",)]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Unauthorized syscall", str(ctx.exception))

    def test_memory_attack_detection(self):
        program = [("LOAD", "R0", 5), ("STORE", "R0", 999999), ("HALT",)]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Invalid memory write", str(ctx.exception))

    def test_infinite_loop_detection(self):
        program = [("JMP", 0)]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Program has no HALT", str(ctx.exception))

    def test_infinite_loop_no_halt_path(self):
        program = [
            ("LOAD", "R0", 1),
            ("JMP", 0),
            ("HALT",)
        ]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Unbounded loop", str(ctx.exception))

    def test_resource_abuse_detection_process(self):
        program = [
            ("SYSCALL", "CREATE_PROCESS", [("HALT",)]),
            ("JMP", 0),
            ("HALT",)
        ]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Potential process explosion", str(ctx.exception))

    def test_resource_abuse_detection_memory(self):
        program = [
            ("SYSCALL", "ALLOCATE_MEMORY", 999999999),
            ("HALT",)
        ]
        with self.assertRaises(VerificationError) as ctx:
            self.verifier.verify(program)
        self.assertIn("Memory request exceeds runtime limits", str(ctx.exception))

    def test_verification_report_generation(self):
        program = [("LOAD", "R0", 1), ("HALT",), ("ADD", "R0", "R0", "R0")]
        report = self.verifier.verify(program)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.errors), 0)
        self.assertEqual(len(report.warnings), 1)
        self.assertIn("unreachable", report.warnings[0])
        self.assertIn("PASSED", str(report))

if __name__ == "__main__":
    unittest.main()
