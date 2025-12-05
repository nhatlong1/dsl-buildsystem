"""
Type definitions for the build system.

This module contains all the core type definitions including tokens, AST nodes,
and runtime types like Flag and Executable.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import List, Union, Optional, Any

# --- Enums ---


class TokenType(Enum):
    """
    Enum representing the different types of tokens in the language.
    """

    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    DOT = "DOT"
    AT = "AT"
    STAR = "STAR"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    PIPE_GT = "PIPE_GT"
    EOF = "EOF"


class SymbolType(Enum):
    """
    Enum representing the types of symbols that can be declared.
    """

    VARIABLE = "VARIABLE"
    FLAGS = "FLAGS"
    EXECUTABLE = "EXECUTABLE"
    MACRO = "MACRO"


class Precedence(IntEnum):
    """
    Enum representing operator precedence levels.
    """

    LOWEST = 0
    PIPELINE = 10
    DOT = 30
    PREFIX = 40
    CALL = 50


# --- Dataclasses ---


@dataclass
class Token:
    """
    Represents a lexical token.

    Parameters
    ----------
    type : TokenType
        The type of the token.
    value : Any
        The value associated with the token.
    line : int
        The line number where the token was found.
    column : int
        The column number where the token starts.
    """

    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.column})"


@dataclass
class Flag:
    """
    Represents a command-line flag template.

    Parameters
    ----------
    name : str
        The name of the flag.
    template : str
        The template string with placeholders (e.g. "-I$1").
    arity : int
        The number of arguments the flag expects (calculated automatically).
    """

    name: str
    template: str
    arity: int = field(init=False)

    def __post_init__(self) -> None:
        """
        Calculates the arity of the flag based on the template.
        """
        matches = re.findall(r"\$(\d+)", self.template)
        if matches:
            self.arity = max(map(int, matches))
        else:
            self.arity = 0

    def apply(self, args: List[Any]) -> str:
        """
        Applies arguments to the flag template.

        Parameters
        ----------
        args : List[Any]
            The arguments to substitute into the template.

        Returns
        -------
        str
            The formatted flag string.

        Raises
        ------
        ValueError
            If the number of arguments does not match the arity.
        """
        if len(args) != self.arity:
            raise ValueError(
                f"Flag {self.name} expects {self.arity} arguments, got {len(args)}"
            )

        result = self.template
        for i, arg in enumerate(args):
            result = result.replace(f"${i+1}", str(arg))
        return result


@dataclass
class Executable:
    """
    Represents an executable command.

    Parameters
    ----------
    name : str
        The name of the executable.
    description : str
        A description of the executable.
    source : str
        The source or origin of the executable.
    path : Optional[str]
        The path to the executable file (or None).
    """

    name: str
    description: str
    source: str
    path: Optional[str]


# --- AST Nodes ---


@dataclass
class ASTNode:
    """
    Base class for Abstract Syntax Tree nodes.
    """


@dataclass
class Program(ASTNode):
    """
    Represents a complete program consisting of statements.

    Parameters
    ----------
    statements : List[ASTNode]
        The list of statements in the program.
    """

    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class Identifier(ASTNode):
    """
    Represents an identifier.

    Parameters
    ----------
    name : str
        The name of the identifier.
    """

    name: str


@dataclass
class Literal(ASTNode):
    """
    Represents a literal value.

    Parameters
    ----------
    value : Union[str, int, bool, None]
        The value of the literal.
    """

    value: Union[str, int, bool, None]


# Forward reference for type hints
Expression = Union["Term", "PropertyAccess"]


@dataclass
class FunctionCall(ASTNode):
    """
    Represents a function call.

    Parameters
    ----------
    name : Identifier
        The name of the function being called.
    args : List[Expression]
        The arguments passed to the function.
    """

    name: Identifier
    args: List[Expression] = field(default_factory=list)


Atom = Union[Literal, FunctionCall, Identifier]


@dataclass
class VariableDeref(ASTNode):
    """
    Represents a variable dereference (e.g. @VAR).

    Parameters
    ----------
    target : Atom
        The target being dereferenced.
    """

    target: Atom


@dataclass
class PropertyAccess(ASTNode):
    """
    Represents a property access (e.g. OBJ.PROP).

    Parameters
    ----------
    target : Expression
        The object whose property is being accessed.
    property_name : Identifier
        The name of the property.
    """

    target: Expression
    property_name: Identifier


Term = Union[Atom, VariableDeref]
