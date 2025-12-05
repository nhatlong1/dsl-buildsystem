"""
Protocol definitions for the build system.

This module defines the protocol interfaces that components must implement
to participate in the build system. Protocols are used for loose coupling
and to enable extensibility through plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Generic, TypeVar

from src.types import Token, ASTNode, TokenType

T = TypeVar("T")

class LexerProtocol(ABC):
    """
    Protocol for lexer implementations.

    A lexer is responsible for tokenizing input text into a stream of tokens
    that can be consumed by a parser.
    """

    @abstractmethod
    def get_next_token(self) -> Token[Any]:
        """
        Retrieves the next token from the input stream.

        Returns
        -------
        Token[Any]
            The next token object.
        """

    @abstractmethod
    def peek(self) -> Optional[str]:
        """
        Returns the next character without advancing the position.

        Returns
        -------
        Optional[str]
            The next character, or None if at the end of input.
        """

    @abstractmethod
    def advance(self) -> None:
        """
        Advances the lexer's position to the next character.
        """


class ParserProtocol(ABC):
    """
    Protocol for parser implementations.

    A parser transforms a stream of tokens from a lexer into an Abstract
    Syntax Tree (AST). It supports extensibility through prefix/infix
    parsers and token handlers.
    """

    @property
    @abstractmethod
    def current_token(self) -> Token[Any]:
        """
        Returns the current token being processed by the parser.

        Returns
        -------
        Token[Any]
            The current token in the token stream.
        """

    @abstractmethod
    def parse_program(self) -> Any:
        """
        Parses the entire program from the token stream.

        Returns
        -------
        Any
            The root AST node (typically a Program node).
        """

    @abstractmethod
    def parse_expression(self, precedence: int) -> ASTNode:
        """
        Parses an expression with the given precedence level.

        Parameters
        ----------
        precedence : int
            The minimum precedence level for operators to bind.

        Returns
        -------
        ASTNode
            The parsed expression AST node.
        """

    @abstractmethod
    def register_prefix(self, token_type: TokenType, fn: Any) -> None:
        """
        Registers a prefix parse function for a token type.

        Parameters
        ----------
        token_type : TokenType
            The token type to register.
        fn : Any
            The parse function to call when this token is encountered in prefix position.
        """

    @abstractmethod
    def register_infix(self, token_type: TokenType, fn: Any, precedence: int) -> None:
        """
        Registers an infix parse function for a token type.

        Parameters
        ----------
        token_type : TokenType
            The token type to register.
        fn : Any
            The parse function to call when this token is encountered in infix position.
        precedence : int
            The precedence level of this infix operator.
        """

    @abstractmethod
    def register_token_handler(self, token_value: str, fn: Any) -> None:
        """
        Registers a handler for a specific token value (keyword).

        Parameters
        ----------
        token_value : str
            The keyword or token value to handle (e.g., "FOR", "IF").
        fn : Any
            The handler function to call when this keyword is encountered.
        """

    @abstractmethod
    def eat(self, token_type: TokenType) -> Token[Any]:
        """
        Consumes the current token if it matches the expected type.

        Parameters
        ----------
        token_type : TokenType
            The expected token type.

        Returns
        -------
        Token[Any]
            The consumed token.

        Raises
        ------
        Exception
            If the current token does not match the expected type.
        """


class ContextProtocol(ABC):
    """
    Protocol for execution context implementations.

    A context manages the runtime environment including variables (symbols),
    functions, and loaded modules.
    """

    @property
    @abstractmethod
    def symbols(self) -> Dict[str, Any]:
        """
        Returns the dictionary of symbols (variables).

        Returns
        -------
        Dict[str, Any]
            The symbols dictionary mapping names to values.
        """

    @property
    @abstractmethod
    def functions(self) -> Dict[str, Any]:
        """
        Returns the dictionary of registered functions.

        Returns
        -------
        Dict[str, Any]
            The functions dictionary mapping names to callable implementations.
        """

    @property
    @abstractmethod
    def modules(self) -> Dict[str, Any]:
        """
        Returns the dictionary of loaded modules.

        Returns
        -------
        Dict[str, Any]
            The modules dictionary mapping names to module objects.
        """

    @abstractmethod
    def get(self, name: str) -> Any:
        """
        Retrieves a symbol's value by name.

        Parameters
        ----------
        name : str
            The symbol name to look up.

        Returns
        -------
        Any
            The symbol's value, or None if not found.
        """

    @abstractmethod
    def set(self, name: str, value: Any) -> None:
        """
        Sets a symbol's value.

        Parameters
        ----------
        name : str
            The symbol name.
        value : Any
            The value to assign to the symbol.
        """

    @abstractmethod
    def register_function(self, name: str, func: Any) -> None:
        """
        Registers a function in the context.

        Parameters
        ----------
        name : str
            The function name.
        func : Any
            The function implementation (typically a callable).
        """

    @abstractmethod
    def call_function(
        self, name: str, args: List[Any], interpreter: "InterpreterProtocol"
    ) -> Any:
        """
        Calls a registered function.

        Parameters
        ----------
        name : str
            The name of the function to call.
        args : List[Any]
            The argument nodes to pass to the function.
        interpreter : InterpreterProtocol
            The interpreter instance for evaluating arguments and executing the function.

        Returns
        -------
        Any
            The return value of the function.

        Raises
        ------
        Exception
            If the function is not found or not callable.
        """


class InterpreterProtocol(ABC):
    """
    Protocol for interpreter implementations.

    An interpreter traverses and executes an Abstract Syntax Tree (AST),
    managing the execution context and visiting nodes using the visitor pattern.
    """

    @property
    @abstractmethod
    def context(self) -> ContextProtocol:
        """
        Returns the interpreter's execution context.

        Returns
        -------
        ContextProtocol
            The context managing symbols, functions, and modules.
        """

    @property
    @abstractmethod
    def dry_run(self) -> bool:
        """
        Returns whether the interpreter is in dry-run mode.

        Returns
        -------
        bool
            True if in dry-run mode (commands are printed but not executed),
            False otherwise.
        """

    @abstractmethod
    def visit(self, node: Any) -> Any:
        """
        Visits an AST node and executes it.

        Parameters
        ----------
        node : Any
            The AST node to visit.

        Returns
        -------
        Any
            The result of visiting the node.

        Raises
        ------
        Exception
            If no visitor is registered for the node type.
        """

    @abstractmethod
    def register_visitor(self, node_type: Any, handler: Any) -> None:
        """
        Registers a visitor function for a specific AST node type.

        Parameters
        ----------
        node_type : Any
            The class of the AST node to handle.
        handler : Any
            The visitor function (signature: (interpreter, node) -> Any).
        """

    @abstractmethod
    def interpolate_string(self, s: str) -> str:
        """
        Interpolates variables in a string (e.g., "$VAR" -> value).

        Parameters
        ----------
        s : str
            The string containing variable references.

        Returns
        -------
        str
            The string with variables replaced by their values.
        """

    @abstractmethod
    def evaluate_args(self, args_nodes: List[Any]) -> List[Any]:
        """
        Evaluates a list of argument nodes.

        Parameters
        ----------
        args_nodes : List[Any]
            The list of AST nodes representing arguments.

        Returns
        -------
        List[Any]
            The list of evaluated argument values.
        """
