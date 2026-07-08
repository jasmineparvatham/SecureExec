import unittest
from compiler.c_subset_compiler import compile_c_subset

class TestComments(unittest.TestCase):
    def test_single_line_comment(self):
        code = """
        // This is a comment
        int main() {
            int x = 10; // inline comment
            return x;
        }
        """
        prog = compile_c_subset(code)
        self.assertTrue(len(prog) > 0)

    def test_multi_line_comment(self):
        code = """
        /* Multi-line
           comment
        */
        int main() {
            /* inline block */ int y = 5;
            return y;
        }
        """
        prog = compile_c_subset(code)
        self.assertTrue(len(prog) > 0)

if __name__ == '__main__':
    unittest.main()
