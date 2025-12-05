"""
Parser implementation using Top-Down Operator Precedence (Pratt Parser).

This module provides the Parser class which transforms tokens from the lexer
into an Abstract Syntax Tree (AST). It supports extensibility through plugins
and custom token handlers.
"""

import os
import sys
import importlib
from typing import Callable, Tuple, Dict, Any, List

from src.lexer import TokenType
from src.types import (
    ASTNode,
    Program,
    FunctionCall,
    Literal,
    Identifier,
    VariableDeref,
    PropertyAccess,
    Precedence,
    Token,
)
from src.protocols import ParserProtocol, LexerProtocol


class Parser(ParserProtocol):
    """
    Parser implementation using Top-Down Operator Precedence (Pratt Parser).

    Parameters
    ----------
    lexer : LexerProtocol
        The lexer instance used to retrieve tokens.

    Attributes
    ----------
    lexer : LexerProtocol
        The lexer instance.
    current_token : Token
        The current token being processed.
    prefix_parse_fns : Dict[TokenType, Callable[[], ASTNode]]
        Mapping of tokens to prefix parse functions.
    infix_parse_fns : Dict[TokenType, Tuple[Callable[[ASTNode], ASTNode], int]]
        Mapping of tokens to infix parse functions and precedence.
    token_handlers : Dict[str, Callable[[Any], ASTNode]]
        Handlers for specific token values (keywords).
    """

    def __init__(self, lexer: LexerProtocol):
        self.lexer = lexer
        self._current_token: Token = self.lexer.get_next_token()

        # Pratt Parser tables
        self.prefix_parse_fns: Dict[TokenType, Callable[[], ASTNode]] = {}
        self.infix_parse_fns: Dict[
            TokenType, Tuple[Callable[[ASTNode], ASTNode], int]
        ] = {}

        # Keyword/Token handlers (for special Identifiers like FOR)
        self.token_handlers: Dict[str, Callable[[Any], ASTNode]] = {}

        # Compatibility for old plugins
        self.keyword_extensions: Dict[str, Any] = {}

        self.register_core_grammar()

    @property
    def current_token(self) -> Token:
        return self._current_token

    def register_core_grammar(self) -> None:
        """
        Registers the core grammar rules (prefix and infix parsers).
        """
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
        self.register_infix(
            TokenType.LPAREN, self.parse_call_expression, Precedence.CALL
        )
        self.register_infix(TokenType.DOT, self.parse_property_access, Precedence.DOT)

    def register_prefix(self, token_type: TokenType, fn: Callable[[], ASTNode]) -> None:
        """
        Registers a prefix parse function for a token type.

        Parameters
        ----------
        token_type : TokenType
            The token type to register.
        fn : Callable[[], ASTNode]
            The function to call when this token is encountered in prefix position.
        """
        self.prefix_parse_fns[token_type] = fn

    def register_infix(
        self, token_type: TokenType, fn: Callable[[ASTNode], ASTNode], precedence: int
    ) -> None:
        """
        Registers an infix parse function for a token type.

        Parameters
        ----------
        token_type : TokenType
            The token type to register.
        fn : Callable[[ASTNode], ASTNode]
            The function to call when this token is encountered in infix position.
        precedence : int
            The precedence level of the infix operator.
        """
        self.infix_parse_fns[token_type] = (fn, precedence)

    def register_token_handler(
        self, token_value: str, fn: Callable[[Any], ASTNode]
    ) -> None:
        """
        Registers a handler for a specific token value (keyword).

        Parameters
        ----------
        token_value : str
            The keyword to handle.
        fn : Callable[[Any], ASTNode]
            The handler function.
        """
        self.token_handlers[token_value] = fn

    # Compatibility method
    def register_extension(
        self, keyword: str, parse_func: Callable[[Any], ASTNode]
    ) -> None:
        """
        Registers a custom parser function for a specific keyword.

        Parameters
        ----------
        keyword : str
            The keyword to register.
        parse_func : Callable[[Any], ASTNode]
            The parser function.
        """
        self.register_token_handler(keyword, parse_func)

    def error(self, msg: str) -> None:
        """
        Raises a parser error.

        Parameters
        ----------
        msg : str
            The error message.
        """
        # pylint: disable=broad-exception-raised
        raise Exception(f"Parser error at line {self._current_token.line}: {msg}")

    def eat(self, token_type: TokenType) -> None:
        """
        Consumes the current token if it matches the expected type, otherwise raises an error.

        Parameters
        ----------
        token_type : TokenType
            The expected token type.
        """
        if self._current_token.type == token_type:
            self._current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self._current_token.type}")

    def peek_precedence(self) -> int:
        """
        Returns the precedence of the current token.

        Returns
        -------
        int
            The precedence level.
        """
        token_type = self._current_token.type
        if token_type in self.infix_parse_fns:
            return self.infix_parse_fns[token_type][1]
        return Precedence.LOWEST

    def parse_program(self) -> Program:
        """
        Parses the entire program.

        Returns
        -------
        Program
            The root of the AST.
        """
        statements = []
        while self._current_token.type != TokenType.EOF:
            statements.append(self.parse_statement())
        return Program(statements=statements)

    def parse_statement(self) -> ASTNode:
        """
        Parses a single statement.

        Returns
        -------
        ASTNode
            The parsed statement node.
        """
        return self.parse_expression(Precedence.LOWEST)

    def parse_expression(self, precedence: int) -> ASTNode:
        """
        Parses an expression using Pratt parsing.

        Parameters
        ----------
        precedence : int
            The right-binding power (precedence) to bind to.

        Returns
        -------
        ASTNode
            The parsed expression node.
        """
        token_type = self._current_token.type

        # Prefix (NUD)
        prefix = self.prefix_parse_fns.get(token_type)
        if not prefix:
            self.error(f"No prefix parse function for {token_type}")
            return Identifier("ERROR")  # Should be unreachable due to error()

        left = prefix()

        # Infix (LED)
        while precedence < self.peek_precedence():
            token_type = self._current_token.type
            infix_tuple = self.infix_parse_fns.get(token_type)
            if not infix_tuple:
                return left

            infix, _ = infix_tuple
            left = infix(left)

        return left

    # --- NUD Handlers ---

    def parse_identifier(self) -> ASTNode:
        """
        Parses an identifier or keyword.

        Returns
        -------
        ASTNode
            An Identifier node or the result of a keyword handler.
        """
        # Check for special token handlers (Keywords)
        if str(self._current_token.value) in self.token_handlers:
            return self.token_handlers[str(self._current_token.value)](self)

        token = self._current_token
        self.eat(TokenType.IDENTIFIER)
        return Identifier(name=str(token.value))

    def parse_identifier_star(self) -> Identifier:
        """
        Parses the '*' token as an identifier.

        Returns
        -------
        Identifier
            An Identifier node with name '*'.
        """
        self.eat(TokenType.STAR)
        return Identifier(name="*")

    def parse_literal(self) -> Literal:
        """
        Parses a literal value (string, number, boolean, null).

        Returns
        -------
        Literal
            A Literal node.
        """
        token = self._current_token
        self.eat(token.type)
        return Literal(value=token.value)

    def parse_grouped_expression(self) -> ASTNode:
        """
        Parses a grouped expression (parenthesized).

        Returns
        -------
        ASTNode
            The expression inside the parentheses.
        """
        self.eat(TokenType.LPAREN)
        exp = self.parse_expression(Precedence.LOWEST)
        self.eat(TokenType.RPAREN)
        return exp

    def parse_deref(self) -> VariableDeref:
        """
        Parses a variable dereference (@VAR).

        Returns
        -------
        VariableDeref
            A VariableDeref node.
        """
        self.eat(TokenType.AT)
        target = self.parse_expression(Precedence.PREFIX)
        # Ensure target is Atom-compatible if strictly typed, but here ASTNode covers it
        return VariableDeref(target=target)  # type: ignore

    # --- LED Handlers ---

    def parse_call_expression(self, left: ASTNode) -> FunctionCall:
        """
        Parses a function call expression.

        Parameters
        ----------
        left : ASTNode
            The identifier being called.

        Returns
        -------
        FunctionCall
            A FunctionCall node.
        """
        if not isinstance(left, Identifier):
            self.error(f"Function call must be on an Identifier, but got {type(left)}")

        self.eat(TokenType.LPAREN)
        args: List[ASTNode] = []
        if self._current_token.type != TokenType.RPAREN:
            args = self.parse_arg_list()
        self.eat(TokenType.RPAREN)

        return FunctionCall(name=left, args=args)  # type: ignore

    def parse_property_access(self, left: ASTNode) -> PropertyAccess:
        """
        Parses a property access expression.

        Parameters
        ----------
        left : ASTNode
            The target object.

        Returns
        -------
        PropertyAccess
            A PropertyAccess node.
        """
        self.eat(TokenType.DOT)
        prop_name = self.parse_identifier_node()  # Parse identifier explicitly
        return PropertyAccess(target=left, property_name=prop_name)  # type: ignore

    # Helper for parsing identifier as Node (not NUD)
    def parse_identifier_node(self) -> Identifier:
        """
        Helper to parse an identifier token directly into an Identifier node.

        Returns
        -------
        Identifier
            The Identifier node.
        """
        token = self._current_token
        self.eat(TokenType.IDENTIFIER)
        return Identifier(name=str(token.value))

    def parse_arg_list(self) -> List[ASTNode]:
        """
        Parses a comma-separated list of arguments.

        Returns
        -------
        List[ASTNode]
            The list of argument nodes.
        """
        args = [self.parse_expression(Precedence.LOWEST)]
        while self._current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.parse_expression(Precedence.LOWEST))
        return args


def load_plugins(parser: ParserProtocol, plugin_dir: str = "plugins") -> None:
    """
    Loads plugins from the specified directory and registers them with the parser.

    Parameters
    ----------
    parser : ParserProtocol
        The parser instance to register plugins with.
    plugin_dir : str, optional
        The directory containing plugin modules.
    """
    if not os.path.exists(plugin_dir):
        return

    sys.path.append(os.getcwd())

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f"{plugin_dir}.{module_name}")
                if hasattr(module, "register"):
                    module.register(parser)
                    # print(f"Loaded plugin: {module_name}") # Optional logging
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Failed to load plugin {module_name}: {e}")


def pretty_print(node: ASTNode, indent: int = 0) -> None:
    """
    Recursively prints the AST in a readable format.

    Parameters
    ----------
    node : ASTNode
        The root node to print.
    indent : int, optional
        The current indentation level.
    """
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
    elif node.__class__.__name__ == "PipelineNode":
        # Dynamic check for plugin nodes
        print(f"{space}PipelineNode (|>)")
        pretty_print(getattr(node, "left"), indent + 1)  # type: ignore
        pretty_print(getattr(node, "right"), indent + 1)  # type: ignore
    elif node.__class__.__name__ == "ForLoopNode":
        print(f"{space}ForLoopNode")
        print(f"{space}  Var: {getattr(node, 'var_name')}")
        print(f"{space}  Items:")
        items = getattr(node, "items")
        if isinstance(items, list):
            for item in items:
                pretty_print(item, indent + 2)
        else:
            pretty_print(items, indent + 2)
        print(f"{space}  Body:")
        pretty_print(getattr(node, "body"), indent + 2)
    elif node.__class__.__name__ == "ArrayNode":
        print(f"{space}ArrayNode")
        for item in getattr(node, "items"):
            pretty_print(item, indent + 1)
    else:
        print(f"{space}Unknown Node: {node}")
