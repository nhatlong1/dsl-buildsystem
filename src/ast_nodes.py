from dataclasses import dataclass, field
from typing import List, Union, Optional

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
    target: 'Atom'  # Identifier, FunctionCall, or Literal (for string interpolation)

@dataclass
class PropertyAccess(ASTNode):
    target: 'Expression'
    property_name: Identifier

# Union types for type hinting
Atom = Union[Literal, FunctionCall, Identifier]
Term = Union[Atom, VariableDeref]
Expression = Union[Term, PropertyAccess]
