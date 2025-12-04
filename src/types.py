from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import List, Union, Optional, Any
import re
from src.protocols import InterpreterProtocol

# --- Enums ---

class TokenType(Enum):
    IDENTIFIER = 'IDENTIFIER'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    BOOLEAN = 'BOOLEAN'
    NULL = 'NULL'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    COMMA = 'COMMA'
    DOT = 'DOT'
    AT = 'AT'
    STAR = 'STAR'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    LBRACKET = 'LBRACKET'
    RBRACKET = 'RBRACKET'
    PIPE_GT = 'PIPE_GT'
    EOF = 'EOF'

class SymbolType(Enum):
    VARIABLE = 'VARIABLE'
    FLAGS = 'FLAGS'
    EXECUTABLE = 'EXECUTABLE'
    MACRO = 'MACRO'

class Precedence(IntEnum):
    LOWEST = 0
    PIPELINE = 10
    DOT = 30
    PREFIX = 40
    CALL = 50

# --- Dataclasses ---

@dataclass
class Flag:
    name: str
    template: str
    arity: int = field(init=False)

    def __post_init__(self):
        matches = re.findall(r'\$(\d+)', self.template)
        if matches:
            self.arity = max(map(int, matches))
        else:
            self.arity = 0

    def apply(self, args: List[Any]) -> str:
        if len(args) != self.arity:
            raise Exception(f"Flag {self.name} expects {self.arity} arguments, got {len(args)}")

        result = self.template
        for i, arg in enumerate(args):
            result = result.replace(f"${i+1}", str(arg))
        return result

@dataclass
class Executable:
    name: str
    description: str
    source: str
    path: str

# --- AST Nodes ---

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class Literal(ASTNode):
    value: Union[str, int, bool, None]

@dataclass
class FunctionCall(ASTNode):
    name: Identifier
    args: List['Expression'] = field(default_factory=list)

@dataclass
class VariableDeref(ASTNode):
    target: 'Atom'

@dataclass
class PropertyAccess(ASTNode):
    target: 'Expression'
    property_name: Identifier

# Union types for type hinting
Atom = Union[Literal, FunctionCall, Identifier]
Term = Union[Atom, VariableDeref]
Expression = Union[Term, PropertyAccess]
