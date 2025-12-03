from src.lexer import Lexer, TokenType
from src.ast_nodes import Program, FunctionCall, Literal, Identifier, VariableDeref, PropertyAccess
import importlib
import os
import sys

class Precedence:
    LOWEST = 0
    PIPELINE = 10
    DOT = 30
    PREFIX = 40
    CALL = 50

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

        # Pratt Parser tables
        self.prefix_parse_fns = {} # token_type -> fn
        self.infix_parse_fns = {}  # token_type -> (fn, precedence)

        # Keyword/Token handlers (for special Identifiers like FOR)
        self.token_handlers = {}   # token_value -> fn

        # Compatibility for old plugins
        self.keyword_extensions = {}

        self.register_core_grammar()

    def register_core_grammar(self):
        # Literals & Atoms
        self.register_prefix(TokenType.IDENTIFIER, self.parse_identifier)
        self.register_prefix(TokenType.STRING, self.parse_literal)
        self.register_prefix(TokenType.NUMBER, self.parse_literal)
        self.register_prefix(TokenType.BOOLEAN, self.parse_literal)
        self.register_prefix(TokenType.NULL, self.parse_literal)
        self.register_prefix(TokenType.STAR, self.parse_identifier_star) # Treat * as identifier? Or literal?

        # Grouping
        self.register_prefix(TokenType.LPAREN, self.parse_grouped_expression)

        # Prefix Operators
        self.register_prefix(TokenType.AT, self.parse_deref)

        # Infix Operators
        self.register_infix(TokenType.LPAREN, self.parse_call_expression, Precedence.CALL)
        self.register_infix(TokenType.DOT, self.parse_property_access, Precedence.DOT)

        # Note: PIPELINE will be registered by plugin, but we could add core support if we wanted.

    def register_prefix(self, token_type, fn):
        self.prefix_parse_fns[token_type] = fn

    def register_infix(self, token_type, fn, precedence):
        self.infix_parse_fns[token_type] = (fn, precedence)

    def register_token_handler(self, token_value, fn):
        self.token_handlers[token_value] = fn

    # Compatibility method
    def register_extension(self, keyword, parse_func):
        """Registers a custom parser function for a specific keyword."""
        self.register_token_handler(keyword, parse_func)

    def error(self, msg):
        raise Exception(f"Parser error at line {self.current_token.line}: {msg}")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")

    def peek_precedence(self):
        token_type = self.current_token.type
        if token_type in self.infix_parse_fns:
            return self.infix_parse_fns[token_type][1]
        return Precedence.LOWEST

    def parse_program(self):
        statements = []
        while self.current_token.type != TokenType.EOF:
            statements.append(self.parse_statement())
        return Program(statements=statements)

    def parse_statement(self):
        # In this language, statements are just expressions (function calls usually)
        return self.parse_expression(Precedence.LOWEST)

    def parse_expression(self, precedence):
        token_type = self.current_token.type

        # Prefix (NUD)
        prefix = self.prefix_parse_fns.get(token_type)
        if not prefix:
            self.error(f"No prefix parse function for {token_type}")

        left = prefix()

        # Infix (LED)
        while precedence < self.peek_precedence():
            token_type = self.current_token.type
            infix_tuple = self.infix_parse_fns.get(token_type)
            if not infix_tuple:
                return left

            infix, _ = infix_tuple
            left = infix(left)

        return left

    # --- NUD Handlers ---

    def parse_identifier(self):
        # Check for special token handlers (Keywords)
        if self.current_token.value in self.token_handlers:
            return self.token_handlers[self.current_token.value](self)

        token = self.current_token
        self.eat(TokenType.IDENTIFIER)
        return Identifier(name=token.value)

    def parse_identifier_star(self):
        self.eat(TokenType.STAR)
        return Identifier(name='*')

    def parse_literal(self):
        token = self.current_token
        self.eat(token.type)
        return Literal(value=token.value)

    def parse_grouped_expression(self):
        self.eat(TokenType.LPAREN)
        exp = self.parse_expression(Precedence.LOWEST)
        self.eat(TokenType.RPAREN)
        return exp

    def parse_deref(self):
        self.eat(TokenType.AT)
        # Parse the next atom/expression.
        # Usually deref applies to an atom (ID, String, Call).
        # We use Precedence.PREFIX?
        # If we use LOWEST, we might eat too much?
        # @A.B -> VariableDeref(target=PropAccess(A, B)) ?
        # Or PropertyAccess(VariableDeref(A), B) ?
        # Existing parser: `parse_term` handles `@`. `parse_expression` handles `.`.
        # `parse_expression` calls `parse_term`.
        # So `@A.B` -> `term` is `@A`. Then `.` B.
        # So `PropAccess(VariableDeref(A), B)`.
        # To achieve this in Pratt:
        # `parse_deref` calls `parse_expression(PREFIX)`.
        # If `DOT` has precedence < PREFIX, it won't be consumed by `parse_expression(PREFIX)`.
        # DOT is 30. PREFIX is 40.
        # So `parse_expression(40)` will parse `A`. Then see `.`. 30 < 40. Stop.
        # Return `VariableDeref(A)`.
        # Then the outer loop (which called `parse_deref` as NUD, likely `parse_expression(LOWEST)`)
        # sees `left = VariableDeref(A)`.
        # Next token is `.`. Precedence 30 > 0.
        # Calls `parse_property_access(left)`.
        # Result: `PropertyAccess(VariableDeref(A), B)`.
        # This matches old behavior.

        target = self.parse_expression(Precedence.PREFIX)
        return VariableDeref(target=target)

    # --- LED Handlers ---

    def parse_call_expression(self, left):
        # left is the function name (Identifier or whatever evaluated before LPAREN)
        # Check if left is valid for call? (Identifier or PropertyAccess)
        if not isinstance(left, (Identifier, PropertyAccess, VariableDeref)):
             # Actually grammar allows calling anything? `@"cmd"(...)`?
             pass

        self.eat(TokenType.LPAREN)
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args = self.parse_arg_list()
        self.eat(TokenType.RPAREN)

        # `left` is the `name`. But `FunctionCall` expects `Identifier`.
        # If `left` is `PropertyAccess`, is it a method call?
        # The AST `FunctionCall` definition: `name: Identifier`.
        # This implies we can only call simple Identifiers?
        # Old parser: `parse_function_call` -> `name = self.parse_identifier()`.
        # So yes, old parser restricted calls to simple identifiers.
        # But wait, `IF(...)` is a call.
        # What about `OBJ.FUNC(...)`?
        # Old parser `parse_expression` loop handles `.` property access.
        # But `parse_statement` calls `parse_function_call` OR extension.
        # `parse_function_call` starts with `Identifier`.
        # So `OBJ.FUNC(...)` was NOT reachable in `parse_statement` unless `OBJ` was an extension?
        # Wait. `parse_statement` -> `parse_function_call`.
        # `parse_function_call` -> parses ID, then args.
        # It does NOT parse property access.
        # So `OBJ.FUNC` was likely invalid as a statement in old parser?
        # Unless `OBJ` is a function returning an object, and we access property?
        # `SELECT(STAT(...))`
        # `STAT` returns object. `SELECT` is function.
        # `STAT(...).PROP` -> `Expression` handles `.`.
        # But `parse_statement` calls `parse_function_call`.
        # `parse_function_call` parses `ID (...)`.
        # It returns `FunctionCall`.
        # It does not continue to parse `.`.
        # So `STAT(...).PROP` as a statement was NOT possible?
        # Only as an argument inside another call.
        # Because `parse_arg_list` calls `parse_expression`.
        # `parse_expression` handles `.`.

        # New Pratt parser allows `OBJ.FUNC(...)` if we treat `Call` as infix.
        # But we must respect the AST node definition `FunctionCall(name: Identifier)`.
        # If we allow `Call` on `PropertyAccess`, we need to change AST or map it.
        # Given existing AST, I should probably enforce `left` is `Identifier`.
        # Or maybe the user wants to relax this?
        # "The `parse_statement_with_pipeline` function completely replaces `Parser.parse_statement`... Maybe we change to a Pratt parser?"
        # I will assume `FunctionCall` requires Identifier name for now to match AST.
        # But `left` in `parse_call_expression` is the expression before `(`.

        if not isinstance(left, Identifier):
             self.error(f"Function call must be on an Identifier, but got {type(left)}")

        return FunctionCall(name=left, args=args)

    def parse_property_access(self, left):
        self.eat(TokenType.DOT)
        prop_name = self.parse_identifier_node() # Parse identifier explicitly
        return PropertyAccess(target=left, property_name=prop_name)

    # Helper for parsing identifier as Node (not NUD)
    def parse_identifier_node(self):
        token = self.current_token
        self.eat(TokenType.IDENTIFIER)
        return Identifier(name=token.value)

    def parse_arg_list(self):
        args = [self.parse_expression(Precedence.LOWEST)]
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.parse_expression(Precedence.LOWEST))
        return args

def load_plugins(parser, plugin_dir='plugins'):
    if not os.path.exists(plugin_dir):
        return

    sys.path.append(os.getcwd())

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
    # New AST Nodes (will be added)
    elif node.__class__.__name__ == 'PipelineNode':
        print(f"{space}PipelineNode (|>)")
        pretty_print(node.left, indent + 1)
        pretty_print(node.right, indent + 1)
    elif node.__class__.__name__ == 'ForLoopNode':
        print(f"{space}ForLoopNode")
        print(f"{space}  Var: {node.var_name}")
        print(f"{space}  Items:")
        # If items is a list (old loop)
        if isinstance(node.items, list):
             for item in node.items:
                 pretty_print(item, indent + 2)
        else: # New loop (Expression)
             pretty_print(node.items, indent + 2)
        print(f"{space}  Body:")
        pretty_print(node.body, indent + 2)
    elif node.__class__.__name__ == 'ArrayNode':
        print(f"{space}ArrayNode")
        for item in node.items:
            pretty_print(item, indent + 1)
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
