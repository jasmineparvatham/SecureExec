import unittest
import io
import sys
from core.runtime.runtime_manager import RuntimeManager

class TestRuntime(unittest.TestCase):
    def setUp(self):
        self.manager = RuntimeManager(debug=False)
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_execute_source(self):
        self.manager.execute_source("examples/programs/hello.c")
        output = sys.stdout.getvalue()
        
        self.assertIn("Compilation successful", output)
        self.assertIn("SAFE", output)
        self.assertIn("Status:\nSUCCESS", output)
        self.assertIn("Exit Code:\n0", output)
        self.assertIn("Instructions:\n10", output)

    def test_return_statement(self):
        self.manager.execute_source("examples/programs/return_test.c")
        output = sys.stdout.getvalue()
        
        self.assertIn("Compilation successful", output)
        self.assertIn("SAFE", output)
        self.assertIn("10", output)
        self.assertIn("Exit Code:\n5", output)

if __name__ == '__main__':
    unittest.main()
