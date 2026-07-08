import unittest
import io
import sys
from core.runtime.runtime_manager import RuntimeManager

class TestMultiprocessExecution(unittest.TestCase):
    def setUp(self):
        self.manager = RuntimeManager(debug=True)
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_multiprocess_execution(self):
        files = [
            "examples/demo/multiprocess/program1.c",
            "examples/demo/multiprocess/program2.c",
            "examples/demo/multiprocess/program3.c"
        ]
        
        self.manager.execute_sources(files)
        output = sys.stdout.getvalue()
        
        import re
        self.assertIsNotNone(re.search(r"Process:\nprogram1.c\n\nPID:\n\d+\n\nOutput:", output))
        self.assertIsNotNone(re.search(r"Process:\nprogram2.c\n\nPID:\n\d+\n\nOutput:", output))
        self.assertIsNotNone(re.search(r"Process:\nprogram3.c\n\nPID:\n\d+\n\nOutput:", output))
        self.assertIsNotNone(re.search(r"Context Switch:", output))
        self.assertIsNotNone(re.search(r"PID \d+ entered Q1", output))
        
        # Verify Context switches > 1
        # The output format for context switch is Context Switches:\n<number>
        import re
        match = re.search(r"Context Switches:\n(\d+)", output)
        self.assertIsNotNone(match)
        switches = int(match.group(1))
        self.assertGreater(switches, 1)

if __name__ == '__main__':
    unittest.main()
