import unittest
from os_layer.scheduler.scheduler import Scheduler
from core.process.process import Process

class TestSchedulerMetrics(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        self.scheduler.debug = False

    def test_completion_and_utilization(self):
        # Process 1: 3 steps
        p1 = Process([("LOAD", "R0", 1), ("INC", "R0"), ("HALT",)])
        # Process 2: 2 steps
        p2 = Process([("LOAD", "R0", 1), ("HALT",)])
        
        self.scheduler.load_processes([p1, p2])
        self.scheduler.run_all()
        
        stats = self.scheduler.get_statistics()
        
        self.assertEqual(stats["processes_completed"], 2)
        # Context switches:
        # Initial run p1 -> 1 switch. p1 finishes since 3 <= 5.
        # Run p2 -> 1 switch. p2 finishes. Total: 2 switches.
        self.assertEqual(stats["context_switches"], 2)
        
        self.assertEqual(stats["cpu_utilization"], 100.0) # No idle time
        self.assertEqual(self.scheduler.cpu_busy_time, 5)

    def test_context_switch_counting(self):
        # We need a process that exceeds Q1 quantum (5)
        # 10 steps to finish
        program = [("LOAD", "R0", 1)] * 9 + [("HALT",)]
        p1 = Process(program)
        p2 = Process([("LOAD", "R1", 1), ("HALT",)]) # 2 steps
        
        # p1 runs 5 steps, context switch to p2.
        # p2 runs 2 steps, finishes. context switch to p1 (from Q2).
        # p1 runs 5 steps, finishes.
        
        self.scheduler.load_processes([p1, p2])
        self.scheduler.run_all()
        
        stats = self.scheduler.get_statistics()
        self.assertEqual(stats["context_switches"], 3)
        self.assertEqual(stats["processes_completed"], 2)

    def test_timing_calculations(self):
        # p1 takes 2 steps
        p1 = Process([("LOAD", "R0", 1), ("HALT",)])
        # p2 takes 2 steps
        p2 = Process([("LOAD", "R0", 1), ("HALT",)])
        
        self.scheduler.load_processes([p1, p2])
        
        self.assertEqual(p1.creation_time, 0)
        self.assertEqual(p2.creation_time, 0)
        
        self.scheduler.run_all()
        
        # p1 runs first. waiting_time=0, turnaround=2, response=0
        self.assertEqual(p1.waiting_time, 0)
        self.assertEqual(p1.turnaround_time, 2)
        self.assertEqual(p1.response_time, 0)
        
        # p2 runs second. waiting_time=2 (while p1 ran), turnaround=4, response=2
        self.assertEqual(p2.waiting_time, 2)
        self.assertEqual(p2.turnaround_time, 4)
        self.assertEqual(p2.response_time, 2)

if __name__ == "__main__":
    unittest.main()
