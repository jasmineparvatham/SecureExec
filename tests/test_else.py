import unittest
import sys
import io
import os
from core.runtime.runtime_manager import RuntimeManager

class TestElse(unittest.TestCase):
    def setUp(self):
        self.manager = RuntimeManager(debug=False)
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_else_branch(self):
        code = """
        int main() {
            int x = 0;
            if (x == 1) {
                print(10);
            } else {
                print(20);
            }
            return 0;
        }
        """
        with open("examples/programs/temp_else.c", "w") as f:
            f.write(code)
        self.manager.execute_source("examples/programs/temp_else.c")
        output = sys.stdout.getvalue()
        self.assertIn("20", output)
        self.assertNotIn("\n10\n", output)

    def test_if_branch(self):
        code = """
        int main() {
            int x = 1;
            if (x == 1) {
                print(10);
            } else {
                print(20);
            }
            return 0;
        }
        """
        with open("examples/programs/temp_else2.c", "w") as f:
            f.write(code)
        self.manager.execute_source("examples/programs/temp_else2.c")
        output = sys.stdout.getvalue()
        self.assertIn("10", output)
        self.assertNotIn("\n20\n", output)

if __name__ == '__main__':
    unittest.main()
