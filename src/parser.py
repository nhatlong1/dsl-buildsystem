from src.lexer import Lexer, TokenType
from src.types import ASTNode, Program, FunctionCall, Literal, Identifier, VariableDeref, PropertyAccess, Precedence
from src.protocols import ParserProtocol, LexerProtocol
import importlib
import os
import sys
from typing import Callable, Tuple, Dict, Any, Union

class Parser(ParserProtocol):
    def __init__(self, lexer: LexerProtocol):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

        # Pratt Parser tables
        self.prefix_parse_fns: Dict[TokenType, Callable[[], ASTNode]] = {}
        self.infix_parse_fns: Dict[TokenType, Tuple[Callable[[ASTNode], ASTNode], int]] = {}

        # Keyword/Token handlers (for special Identifiers like FOR)
        self.token_handlers: Dict[str, Callable[[Any], ASTNode]] = {}

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
        self.register_prefix(TokenType.STAR, self.parse_identifier_star)

        # Grouping
        self.register_prefix(TokenType.LPAREN, self.parse_grouped_expression)

        # Prefix Operators
        self.register_prefix(TokenType.AT, self.parse_deref)

        # Infix Operators
        self.register_infix(TokenType.LPAREN, self.parse_call_expression, Precedence.CALL)
        self.register_infix(TokenType.DOT, self.parse_property_access, Precedence.DOT)

    def register_prefix(self, token_type: TokenType, fn: Callable[[], ASTNode]):
        self.prefix_parse_fns[token_type] = fn

    def register_infix(self, token_type: TokenType, fn: Callable[[ASTNode], ASTNode], precedence: int):
        self.infix_parse_fns[token_type] = (fn, precedence)

    def register_token_handler(self, token_value: str, fn: Callable[[Any], ASTNode]):
        self.token_handlers[token_value] = fn

    # Compatibility method
    def register_extension(self, keyword, parse_func):
        """Registers a custom parser function for a specific keyword."""
        self.register_token_handler(keyword, parse_func)

    def error(self, msg):
        raise Exception(f"Parser error at line {self.current_token.line}: {msg}")

    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")

    def peek_precedence(self):
        token_type = self.current_token.type
        if token_type in self.infix_parse_fns:
            return self.infix_parse_fns[token_type][1]
        return Precedence.LOWEST

    def parse_program(self) -> Program:
        statements = []
        while self.current_token.type != TokenType.EOF:
            statements.append(self.parse_statement())
        return Program(statements=statements)

    def parse_statement(self) -> ASTNode:
        return self.parse_expression(Precedence.LOWEST)

    def parse_expression(self, precedence: int) -> ASTNode:
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

    def parse_identifier(self) -> ASTNode:
        # Check for special token handlers (Keywords)
        if self.current_token.value in self.token_handlers:
            return self.token_handlers[self.current_token.value](self)

        token = self.current_token
        self.eat(TokenType.IDENTIFIER)
        return Identifier(name=token.value)

    def parse_identifier_star(self) -> Identifier:
        self.eat(TokenType.STAR)
        return Identifier(name='*')

    def parse_literal(self) -> Literal:
        token = self.current_token
        self.eat(token.type)
        return Literal(value=token.value)

    def parse_grouped_expression(self) -> ASTNode:
        self.eat(TokenType.LPAREN)
        exp = self.parse_expression(Precedence.LOWEST)
        self.eat(TokenType.RPAREN)
        return exp

    def parse_deref(self) -> VariableDeref:
        self.eat(TokenType.AT)
        target = self.parse_expression(Precedence.PREFIX)
        return VariableDeref(target=target)

    # --- LED Handlers ---

    def parse_call_expression(self, left: ASTNode) -> FunctionCall:
        if not isinstance(left, Identifier):
             self.error(f"Function call must be on an Identifier, but got {type(left)}")

        self.eat(TokenType.LPAREN)
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args = self.parse_arg_list()
        self.eat(TokenType.RPAREN)

        return FunctionCall(name=left, args=args)

    def parse_property_access(self, left: ASTNode) -> PropertyAccess:
        self.eat(TokenType.DOT)
        prop_name = self.parse_identifier_node() # Parse identifier explicitly
        return PropertyAccess(target=left, property_name=prop_name)

    # Helper for parsing identifier as Node (not NUD)
    def parse_identifier_node(self) -> Identifier:
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
                    # print(f"Loaded plugin: {module_name}") # Optional logging
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
    elif node.__class__.__name__ == 'PipelineNode':
        print(f"{space}PipelineNode (|>)")
        pretty_print(node.left, indent + 1)
        pretty_print(node.right, indent + 1)
    elif node.__class__.__name__ == 'ForLoopNode':
        print(f"{space}ForLoopNode")
        print(f"{space}  Var: {node.var_name}")
        print(f"{space}  Items:")
        if isinstance(node.items, list):
             for item in node.items:
                 pretty_print(item, indent + 2)
        else:
             pretty_print(node.items, indent + 2)
        print(f"{space}  Body:")
        pretty_print(node.body, indent + 2)
    elif node.__class__.__name__ == 'ArrayNode':
        print(f"{space}ArrayNode")
        for item in node.items:
            pretty_print(item, indent + 1)
    else:
        print(f"{space}Unknown Node: {node}")
