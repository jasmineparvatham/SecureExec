import unittest
from core.process.process import Process
from core.memory.memory_manager import MemoryManager

class TestProcess(unittest.TestCase):
    def test_pid_generation(self):
        p1 = Process([])
        p2 = Process([])
        self.assertNotEqual(p1.pid, p2.pid)
        self.assertEqual(p2.pid, p1.pid + 1)

    def test_process_states(self):
        p = Process([])
        self.assertEqual(p.state, "NEW")
        p.start()
        self.assertEqual(p.state, "READY")
        p.run()
        self.assertEqual(p.state, "RUNNING")
        p.wait()
        self.assertEqual(p.state, "WAITING")
        p.terminate()
        self.assertEqual(p.state, "TERMINATED")
        self.assertTrue(p.finished)

    def test_pcb_metadata(self):
        p = Process([])
        self.assertEqual(p.priority, 0)
        self.assertEqual(p.queue_level, 1)
        self.assertEqual(p.cpu_time_used, 0)
        self.assertIsNone(p.page_table)

if __name__ == "__main__":
    unittest.main()
