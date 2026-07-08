class Node: pass
class Program(Node): 
    def __init__(self, functions): self.functions = functions
class FunctionDefinition(Node):
    def __init__(self, name, params, body): self.name = name; self.params = params; self.body = body
class FunctionCall(Node):
    def __init__(self, name, args): self.name = name; self.args = args
class VarDecl(Node): 
    def __init__(self, name, expr): self.name = name; self.expr = expr
class ArrayDeclaration(Node):
    def __init__(self, name, size): self.name = name; self.size = size
class ArrayAccess(Node):
    def __init__(self, name, index): self.name = name; self.index = index
class ArrayAssignment(Node):
    def __init__(self, name, index, expr): self.name = name; self.index = index; self.expr = expr
class MallocExpression(Node):
    def __init__(self, size_expr): self.size_expr = size_expr
class FreeStatement(Node):
    def __init__(self, ptr_expr): self.ptr_expr = ptr_expr
class Assign(Node): 
    def __init__(self, name, expr): self.name = name; self.expr = expr
class Print(Node): 
    def __init__(self, expr): self.expr = expr
class Return(Node):
    def __init__(self, expr): self.expr = expr
class If(Node): 
    def __init__(self, cond, body, else_body=None): self.cond = cond; self.body = body; self.else_body = else_body
class While(Node): 
    def __init__(self, cond, body): self.cond = cond; self.body = body
class BinOp(Node): 
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right
class Var(Node): 
    def __init__(self, name): self.name = name
class Num(Node): 
    def __init__(self, val): self.val = val

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, *types):
        t = self.peek()
        if t and t.type in types:
            self.pos += 1
            return t
        return None

    def expect(self, type):
        t = self.match(type)
        if not t:
            p = self.peek()
            raise SyntaxError(f"Expected {type}, got {p.type if p else 'EOF'} at line {p.line if p else 'end'}")
        return t

    def parse(self):
        functions = []
        while self.peek():
            functions.append(self.parse_function())
        return Program(functions)

    def parse_function(self):
        self.expect("INT")
        name = self.expect("ID").value
        self.expect("LPAREN")
        params = []
        if not self.match("RPAREN"):
            while True:
                self.expect("INT")
                params.append(self.expect("ID").value)
                if not self.match("COMMA"):
                    self.expect("RPAREN")
                    break
        self.expect("LBRACE")
        body = []
        while not self.match("RBRACE"):
            body.append(self.parse_stmt())
        return FunctionDefinition(name, params, body)

    def parse_stmt(self):
        if self.match("INT"):
            name = self.expect("ID").value
            if self.match("LBRACKET"):
                size = int(self.expect("NUM").value)
                self.expect("RBRACKET")
                self.expect("SEMI")
                return ArrayDeclaration(name, size)
            if self.match("EQ"):
                expr = self.parse_expr()
                self.expect("SEMI")
                return VarDecl(name, expr)
            self.expect("SEMI")
            return VarDecl(name, Num(0))
        elif self.match("PRINT"):
            self.expect("LPAREN")
            expr = self.parse_expr()
            self.expect("RPAREN")
            self.expect("SEMI")
            return Print(expr)
        elif self.match("FREE"):
            self.expect("LPAREN")
            expr = self.parse_expr()
            self.expect("RPAREN")
            self.expect("SEMI")
            return FreeStatement(expr)
        elif self.match("RETURN"):
            expr = self.parse_expr()
            self.expect("SEMI")
            return Return(expr)
        elif self.match("IF"):
            self.expect("LPAREN")
            cond = self.parse_expr()
            self.expect("RPAREN")
            self.expect("LBRACE")
            body = []
            while not self.match("RBRACE"):
                body.append(self.parse_stmt())
            else_body = None
            if self.match("ELSE"):
                self.expect("LBRACE")
                else_body = []
                while not self.match("RBRACE"):
                    else_body.append(self.parse_stmt())
            return If(cond, body, else_body)
        elif self.match("WHILE"):
            self.expect("LPAREN")
            cond = self.parse_expr()
            self.expect("RPAREN")
            self.expect("LBRACE")
            body = []
            while not self.match("RBRACE"):
                body.append(self.parse_stmt())
            return While(cond, body)
        else:
            name = self.expect("ID").value
            if self.match("LBRACKET"):
                index = self.parse_expr()
                self.expect("RBRACKET")
                self.expect("EQ")
                expr = self.parse_expr()
                self.expect("SEMI")
                return ArrayAssignment(name, index, expr)
            self.expect("EQ")
            expr = self.parse_expr()
            self.expect("SEMI")
            return Assign(name, expr)

    def parse_expr(self):
        left = self.parse_addition()
        t = self.peek()
        while t and t.type in ["LT", "GT", "EQEQ"]:
            op = self.match(t.type).value
            right = self.parse_addition()
            left = BinOp(left, op, right)
            t = self.peek()
        return left

    def parse_addition(self):
        left = self.parse_term()
        t = self.peek()
        while t and t.type in ["PLUS", "MINUS"]:
            op = self.match(t.type).value
            right = self.parse_term()
            left = BinOp(left, op, right)
            t = self.peek()
        return left

    def parse_term(self):
        left = self.parse_factor()
        t = self.peek()
        while t and t.type in ["MULT", "DIV"]:
            op = self.match(t.type).value
            right = self.parse_factor()
            left = BinOp(left, op, right)
            t = self.peek()
        return left

    def parse_factor(self):
        if self.match("LPAREN"):
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr
            
        if self.peek() and self.peek().type == "NUM":
            return Num(int(self.match("NUM").value))
        elif self.match("MALLOC"):
            self.expect("LPAREN")
            size_expr = self.parse_expr()
            self.expect("RPAREN")
            return MallocExpression(size_expr)
        elif self.peek() and self.peek().type == "ID":
            name = self.match("ID").value
            if self.match("LPAREN"):
                args = []
                if not self.match("RPAREN"):
                    while True:
                        args.append(self.parse_expr())
                        if not self.match("COMMA"):
                            self.expect("RPAREN")
                            break
                return FunctionCall(name, args)
            elif self.match("LBRACKET"):
                index = self.parse_expr()
                self.expect("RBRACKET")
                return ArrayAccess(name, index)
            return Var(name)
        raise SyntaxError("Expected expression")
