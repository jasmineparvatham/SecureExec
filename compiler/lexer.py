import re

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

def remove_comments(code):
    # Remove single line comments
    code = re.sub(r'//.*', '', code)
    # Remove multi-line comments, preserving newlines for correct line numbers
    def replacer(match):
        return '\n' * match.group(0).count('\n')
    code = re.sub(r'/\*.*?\*/', replacer, code, flags=re.DOTALL)
    return code

def lex(code):
    code = remove_comments(code)
    rules = [
        ("INT", r'\bint\b'),
        ("IF", r'\bif\b'),
        ("ELSE", r'\belse\b'),
        ("WHILE", r'\bwhile\b'),
        ("PRINT", r'\bprint\b'),
        ("RETURN", r'\breturn\b'),
        ("MALLOC", r'\bmalloc\b'),
        ("FREE", r'\bfree\b'),
        ("ID", r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ("NUM", r'\d+'),
        ("EQEQ", r'=='),
        ("EQ", r'='),
        ("PLUS", r'\+'),
        ("MINUS", r'-'),
        ("MULT", r'\*'),
        ("DIV", r'/'),
        ("LT", r'<'),
        ("GT", r'>'),
        ("LBRACKET", r'\['),
        ("RBRACKET", r'\]'),
        ("LPAREN", r'\('),
        ("RPAREN", r'\)'),
        ("LBRACE", r'\{'),
        ("RBRACE", r'\}'),
        ("COMMA", r','),
        ("SEMI", r';'),
        ("WS", r'\s+'),
    ]
    tokens = []
    line_num = 1
    i = 0
    while i < len(code):
        match = None
        for name, pattern in rules:
            regex = re.compile(pattern)
            match = regex.match(code, i)
            if match:
                value = match.group(0)
                if name != "WS":
                    tokens.append(Token(name, value, line_num))
                line_num += value.count('\n')
                i = match.end()
                break
        if not match:
            raise SyntaxError(f"Illegal character '{code[i]}' at line {line_num}")
    return tokens
