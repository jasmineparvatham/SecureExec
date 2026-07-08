import unittest
from os_layer.scheduler.scheduler import Scheduler
from core.process.process import Process


class TestScheduler(unittest.TestCase):

    def test_short_program_finishes(self):
        program = [
            ("LOAD", "R1", 5),
            ("LOAD", "R2", 7),
            ("ADD", "R3", "R1", "R2"),
            ("HALT",)
        ]

        p = Process(program)
        s = Scheduler()
        s.load_processes([p])
        s.run_all()

        self.assertTrue(p.finished)
        self.assertEqual(p.registers["R3"], 12)

    def test_long_program_moves_and_finishes(self):
        program = [
            ("LOAD", "R1", 1),
            ("INC", "R1"),
            ("INC", "R1"),
            ("INC", "R1"),
            ("INC", "R1"),
            ("INC", "R1"),
            ("INC", "R1"),
            ("INC", "R1"),
            ("HALT",)
        ]

        p = Process(program)
        s = Scheduler()
        s.load_processes([p])
        s.run_all()

        self.assertTrue(p.finished)
        self.assertEqual(p.registers["R1"], 8)


if __name__ == "__main__":
    unittest.main()
