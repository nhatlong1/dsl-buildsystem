from typing import Any, Optional
from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter


class ForLoopNode(ASTNode):
    """AST node representing a loop control flow statement.

    Attributes:
        var_name: Identifier (Variable Name)
        items: Array Expression
        body: Statement
    """

    def __init__(self, var_name: str, items: Any, body: Any) -> None:
        """Initialize a ForLoopNode.

        Args:
            var_name: Identifier (Variable Name)
            items: Array Expression
            body: Statement
        """
        self.var_name = var_name
        self.items = items
        self.body = body


def parse_for(parser: Any) -> ForLoopNode:
    """Parse a for loop statement.

    Parses loop syntax: for (var_name) { body }

    Args:
        parser: The parser instance

    Returns:
        ForLoopNode containing the var_name, items, and body
    """
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Arg 1: Identifier (Variable Name)
    var_name_node = parser.parse_identifier_node()
    var_name = var_name_node.name

    parser.eat(TokenType.COMMA)

    # Arg 2: Array Expression
    items_expr = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.COMMA)

    # Arg 3: Statement
    body = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.RPAREN)

    return ForLoopNode(var_name, items_expr, body)


def execute_for(interpreter: Interpreter, node: ForLoopNode) -> Optional[Any]:
    """Execute a for loop node by repeatedly evaluating body while condition is true.

    Args:
        interpreter: The interpreter instance
        node: The ForLoopNode to execute

    Returns:
        The last evaluated value from the loop body, or None
    """
    items_val = interpreter.visit(node.items)

    if not isinstance(items_val, list):
        raise Exception(
            f"FOR loop expects an array/list as second argument, got {type(items_val)}"
        )

    for val in items_val:
        interpreter.context.set(node.var_name, val)
        interpreter.visit(node.body)


def register(parser: Any) -> None:
    """Register the loop plugin with the parser and interpreter.

    Registers:
    - 'FOR' keyword for loop statements
    - ForLoopNode visitor with the interpreter

    Args:
        parser: The parser instance to register with
    """
    if hasattr(parser, "register_token_handler"):
        parser.register_token_handler("FOR", parse_for)

    if not hasattr(Interpreter, "plugin_visitors"):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[ForLoopNode] = execute_for
