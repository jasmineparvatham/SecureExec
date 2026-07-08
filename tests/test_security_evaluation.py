import unittest
import sys
import io
from benchmarks.security_evaluation import evaluate_security

class TestSecurityEvaluation(unittest.TestCase):
    def setUp(self):
        self.held_out = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self):
        sys.stdout = self.held_out

    def test_evaluation(self):
        evaluate_security()
        output = sys.stdout.getvalue()
        self.assertIn("100% detected", output)
        self.assertIn("SecureExec Security Evaluation", output)

if __name__ == '__main__':
    unittest.main()
