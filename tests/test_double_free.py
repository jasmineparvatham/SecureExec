import unittest
from compiler.c_subset_compiler import compile_c_subset
from verifier.verifier import Verifier
from core.errors import VerificationError

class TestDoubleFree(unittest.TestCase):
    def setUp(self):
        self.verifier = Verifier()

    def test_safe_malloc_free(self):
        code = """
        int main() {
            int ptr;
            ptr = malloc(10);
            free(ptr);
            return 0;
        }
        """
        program = compile_c_subset(code)
        # Should not raise
        self.verifier.verify(program)
        
    def test_safe_reassignment(self):
        code = """
        int main() {
            int ptr;
            ptr = malloc(10);
            free(ptr);
            ptr = malloc(20);
            free(ptr);
            return 0;
        }
        """
        program = compile_c_subset(code)
        # Should not raise
        self.verifier.verify(program)

    def test_double_free(self):
        code = """
        int main() {
            int ptr;
            ptr = malloc(10);
            free(ptr);
            free(ptr);
            return 0;
        }
        """
        program = compile_c_subset(code)
        with self.assertRaises(VerificationError) as context:
            self.verifier.verify(program)
        self.assertIn("Double free detected", str(context.exception))

    def test_double_free_alias(self):
        code = """
        int main() {
            int ptr1;
            int ptr2;
            ptr1 = malloc(10);
            ptr2 = ptr1;
            free(ptr1);
            free(ptr2);
            return 0;
        }
        """
        program = compile_c_subset(code)
        with self.assertRaises(VerificationError) as context:
            self.verifier.verify(program)
        self.assertIn("Double free detected", str(context.exception))

    def test_double_free_branches(self):
        code = """
        int main() {
            int ptr;
            int flag;
            ptr = malloc(10);
            flag = 1;
            if (flag == 1) {
                free(ptr);
            }
            free(ptr);
            return 0;
        }
        """
        program = compile_c_subset(code)
        with self.assertRaises(VerificationError) as context:
            self.verifier.verify(program)
        self.assertIn("Double free detected", str(context.exception))

if __name__ == "__main__":
    unittest.main()
