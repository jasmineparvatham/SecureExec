import unittest
from core.process.process import Process
from core.memory.memory_manager import MemoryManager
from core.errors import VMError

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.manager = MemoryManager(memory_size=128, page_size=16)

    def test_page_allocation(self):
        p = Process([], config=None)
        p.virtual_memory_size = 32 # 2 pages
        self.manager.create_process_memory(p)
        self.assertIsNotNone(p.page_table)
        self.assertEqual(len(p.page_table.mapping), 2)
        # Verify physical frames allocated
        self.assertEqual(len(self.manager.free_frames), (128 // 16) - 2)

    def test_address_translation(self):
        p = Process([])
        p.virtual_memory_size = 32
        self.manager.create_process_memory(p)
        
        self.manager.write(p, 20, 99)
        val = self.manager.read(p, 20)
        self.assertEqual(val, 99)

    def test_process_isolation(self):
        p1 = Process([])
        p1.virtual_memory_size = 16
        self.manager.create_process_memory(p1)
        
        p2 = Process([])
        p2.virtual_memory_size = 16
        self.manager.create_process_memory(p2)
        
        self.manager.write(p1, 5, 42)
        self.manager.write(p2, 5, 100)
        
        self.assertEqual(self.manager.read(p1, 5), 42)
        self.assertEqual(self.manager.read(p2, 5), 100)

    def test_memory_release(self):
        p = Process([])
        p.virtual_memory_size = 32
        initial_frames = len(self.manager.free_frames)
        
        self.manager.create_process_memory(p)
        self.assertLess(len(self.manager.free_frames), initial_frames)
        
        self.manager.release_memory(p)
        self.assertEqual(len(self.manager.free_frames), initial_frames)

    def test_invalid_virtual_address(self):
        p = Process([])
        p.virtual_memory_size = 32
        self.manager.create_process_memory(p)
        
        with self.assertRaises(VMError):
            self.manager.read(p, 100)

if __name__ == "__main__":
    unittest.main()
