from compiler.lexer import lex
from compiler.parser import Parser
from compiler.code_generator import CodeGenerator

def compile_c_subset(code):
    # Lexical Analysis
    tokens = lex(code)
    
    # Syntax Analysis (Parsing)
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Code Generation
    generator = CodeGenerator()
    generator.generate_ir(ast)
    bytecode = generator.to_bytecode()
    
    return bytecode
