import unittest
import os
import subprocess

class TestCLICompile(unittest.TestCase):
    def setUp(self):
        self.valid_c_1 = "tests/temp_cli_valid_1.c"
        self.valid_c_2 = "tests/temp_cli_valid_2.c"
        self.invalid_c = "tests/temp_cli_invalid.c"
        
        with open(self.valid_c_1, "w") as f:
            f.write("int main() { return 0; }")
            
        with open(self.valid_c_2, "w") as f:
            f.write("int main() { int x; x = 5; return x; }")
            
        with open(self.invalid_c, "w") as f:
            f.write("int main() { invalid syntax!!! }")
            
    def tearDown(self):
        for f in [self.valid_c_1, self.valid_c_2, self.invalid_c]:
            if os.path.exists(f):
                os.remove(f)
            bc_file = f.replace(".c", ".bc")
            if os.path.exists(bc_file):
                os.remove(bc_file)

    def test_single_file_compilation(self):
        result = subprocess.run(["python", "cli.py", "compile", self.valid_c_1], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0)
        self.assertIn("✓ temp_cli_valid_1.c", result.stdout)
        self.assertIn("Successful:\n1", result.stdout)
        self.assertIn("Failed:\n0", result.stdout)
        self.assertTrue(os.path.exists(self.valid_c_1.replace(".c", ".bc")))

    def test_multiple_file_compilation(self):
        result = subprocess.run(["python", "cli.py", "compile", self.valid_c_1, self.valid_c_2], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0)
        self.assertIn("✓ temp_cli_valid_1.c", result.stdout)
        self.assertIn("✓ temp_cli_valid_2.c", result.stdout)
        self.assertIn("Programs Submitted:\n2", result.stdout)
        self.assertIn("Successful:\n2", result.stdout)
        self.assertIn("Failed:\n0", result.stdout)
        self.assertTrue(os.path.exists(self.valid_c_1.replace(".c", ".bc")))
        self.assertTrue(os.path.exists(self.valid_c_2.replace(".c", ".bc")))

    def test_compilation_with_invalid_file(self):
        result = subprocess.run(["python", "cli.py", "compile", self.valid_c_1, self.invalid_c, self.valid_c_2], capture_output=True, text=True, encoding='utf-8')
        self.assertIn("✓ temp_cli_valid_1.c", result.stdout)
        self.assertIn("✗ temp_cli_invalid.c", result.stdout)
        self.assertIn("✓ temp_cli_valid_2.c", result.stdout)
        self.assertIn("Programs Submitted:\n3", result.stdout)
        self.assertIn("Successful:\n2", result.stdout)
        self.assertIn("Failed:\n1", result.stdout)
        self.assertTrue(os.path.exists(self.valid_c_1.replace(".c", ".bc")))
        self.assertTrue(os.path.exists(self.valid_c_2.replace(".c", ".bc")))
        self.assertFalse(os.path.exists(self.invalid_c.replace(".c", ".bc")))

if __name__ == "__main__":
    unittest.main()
