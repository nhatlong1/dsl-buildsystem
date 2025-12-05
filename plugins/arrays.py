from typing import List, Any
from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter


class ArrayNode(ASTNode):
    """AST node representing an array literal.

    Attributes:
        items: List of AST nodes representing array elements
    """

    def __init__(self, items: List[ASTNode]) -> None:
        """Initialize an ArrayNode.

        Args:
            items: List of AST nodes to be stored in the array
        """
        self.items: List[ASTNode] = items  # List of AST nodes


def parse_array(parser: Any) -> ArrayNode:
    """Parse an array literal from tokens.

    Parses array syntax: [item1, item2, ...]

    Args:
        parser: The parser instance

    Returns:
        ArrayNode containing the parsed array elements
    """
    # Consumes the opening LBRACKET
    parser.eat(TokenType.LBRACKET)

    items = []
    if parser.current_token.type != TokenType.RBRACKET:
        # Parse expression list
        # Similar to parse_arg_list but using ] as terminator check
        items.append(parser.parse_expression(Precedence.LOWEST))
        while parser.current_token.type == TokenType.COMMA:
            parser.eat(TokenType.COMMA)
            items.append(parser.parse_expression(Precedence.LOWEST))

    parser.eat(TokenType.RBRACKET)
    return ArrayNode(items)


def execute_array(interpreter: Interpreter, node: ArrayNode) -> List[Any]:
    """Execute an array node by evaluating all its items.

    Args:
        interpreter: The interpreter instance
        node: The ArrayNode to execute

    Returns:
        List containing the evaluated values of all array items
    """
    # Evaluate all items
    return [interpreter.visit(item) for item in node.items]


def register(parser: Any) -> None:
    """Register the array plugin with the parser and interpreter.

    Registers:
    - '[' as a prefix operator (NUD) for array literals
    - ArrayNode visitor with the interpreter

    Args:
        parser: The parser instance to register with
    """
    # Register [ as Prefix (NUD)
    if hasattr(parser, "register_prefix"):
        parser.register_prefix(TokenType.LBRACKET, lambda: parse_array(parser))

    # Register Visitor
    if not hasattr(Interpreter, "plugin_visitors"):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[ArrayNode] = execute_array
