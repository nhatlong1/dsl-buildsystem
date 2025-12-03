from src.lexer import Lexer, TokenType
from src.ast_nodes import Program, FunctionCall, Literal, Identifier, VariableDeref, PropertyAccess
import importlib
import os
import sys

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.keyword_extensions = {} # Map keyword -> parse_function

    def error(self, msg):
        raise Exception(f"Parser error at line {self.current_token.line}: {msg}")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")

    def register_extension(self, keyword, parse_func):
        """Registers a custom parser function for a specific keyword."""
        self.keyword_extensions[keyword] = parse_func

    def parse_program(self):
        statements = []
        while self.current_token.type != TokenType.EOF:
            statements.append(self.parse_statement())
        return Program(statements=statements)

    def parse_statement(self):
        # Check if the current token matches a registered extension
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in self.keyword_extensions:
            return self.keyword_extensions[self.current_token.value](self)

        return self.parse_function_call()

    def parse_function_call(self):
        name = self.parse_identifier()
        self.eat(TokenType.LPAREN)
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args = self.parse_arg_list()
        self.eat(TokenType.RPAREN)
        return FunctionCall(name=name, args=args)

    def parse_arg_list(self):
        args = [self.parse_expression()]
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.parse_expression())
        return args

    def parse_expression(self):
        node = self.parse_term()
        while self.current_token.type == TokenType.DOT:
            self.eat(TokenType.DOT)
            prop = self.parse_identifier()
            node = PropertyAccess(target=node, property_name=prop)
        return node

    def parse_term(self):
        if self.current_token.type == TokenType.AT:
            self.eat(TokenType.AT)
            atom = self.parse_atom()
            return VariableDeref(target=atom)
        return self.parse_atom()

    def parse_atom(self):
        token = self.current_token
        if token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return Literal(value=token.value)
        elif token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Literal(value=token.value)
        elif token.type == TokenType.BOOLEAN:
            self.eat(TokenType.BOOLEAN)
            return Literal(value=token.value)
        elif token.type == TokenType.NULL:
            self.eat(TokenType.NULL)
            return Literal(value=None)
        elif token.type == TokenType.STAR:
            self.eat(TokenType.STAR)
            return Identifier(name='*')
        elif token.type == TokenType.IDENTIFIER:
            # Look ahead to see if it's a function call
            # This is LL(1) but we need LL(2) here or backtracking.
            # Lexer has peek, but parser has consumed token.
            # However, simpler: if it's an Identifier, we check if next token is LPAREN.
            # But wait, self.lexer.peek() is on lexer char stream, not token stream.
            # We assume current_token is loaded. We need to peek next token.
            # Recursive descent usually handles this by left-factoring or knowing context.
            # But here `atom` can be Identifier OR FunctionCall.
            # FunctionCall starts with Identifier.
            # So we grab identifier. Check if next is LPAREN.
            # If LPAREN, it's a call. Else it's just ID.

            # BUT: parse_function_call calls eat(LPAREN).

            # Let's peek the next token?
            # Creating a 'peek_token' method requires buffering.

            # Hack: consume identifier. Then check current token.
            # If (, then it was a function call start.

            id_node = self.parse_identifier()
            if self.current_token.type == TokenType.LPAREN:
                # It is a function call.
                # Construct it manually since we already ate the name.
                self.eat(TokenType.LPAREN)
                args = []
                if self.current_token.type != TokenType.RPAREN:
                    args = self.parse_arg_list()
                self.eat(TokenType.RPAREN)
                return FunctionCall(name=id_node, args=args)
            else:
                return id_node
        else:
            self.error(f"Unexpected token {token.type} in atom")

    def parse_identifier(self):
        token = self.current_token
        if token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            return Identifier(name=token.value)
        self.error("Expected identifier")

def load_plugins(parser, plugin_dir='plugins'):
    if not os.path.exists(plugin_dir):
        return

    sys.path.append(os.getcwd()) # Ensure root is in path to load plugins

    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f'{plugin_dir}.{module_name}')
                if hasattr(module, 'register'):
                    module.register(parser)
                    print(f"Loaded plugin: {module_name}")
            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")

def pretty_print(node, indent=0):
    space = "  " * indent
    if isinstance(node, Program):
        print(f"{space}Program")
        for stmt in node.statements:
            pretty_print(stmt, indent + 1)
    elif isinstance(node, FunctionCall):
        print(f"{space}FunctionCall: {node.name.name}")
        for arg in node.args:
            pretty_print(arg, indent + 1)
    elif isinstance(node, Identifier):
        print(f"{space}Identifier: {node.name}")
    elif isinstance(node, Literal):
        print(f"{space}Literal: {repr(node.value)}")
    elif isinstance(node, VariableDeref):
        print(f"{space}VariableDeref (@)")
        pretty_print(node.target, indent + 1)
    elif isinstance(node, PropertyAccess):
        print(f"{space}PropertyAccess: .{node.property_name.name}")
        pretty_print(node.target, indent + 1)
    else:
        print(f"{space}Unknown Node: {node}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            text = f.read()
        lexer = Lexer(text)
        parser = Parser(lexer)
        load_plugins(parser)
        ast = parser.parse_program()
        pretty_print(ast)
