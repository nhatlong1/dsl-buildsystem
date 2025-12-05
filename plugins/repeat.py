from typing import Any

from src.protocols import ParserProtocol
from src.types import TokenType, ASTNode, Precedence, Token
from src.interpreter import Interpreter


class RepeatNode(ASTNode):
    """AST node representing a repeat statement for fixed iterations.

    Attributes:
        count: The number of times to repeat (int)
        body: AST node representing the body to execute repeatedly
    """

    def __init__(self, count: int, body: ASTNode) -> None:
        """Initialize a RepeatNode.

        Args:
            count: Integer for the repeat count
            body: AST node for the body
        """
        self.count: int = count
        self.body: ASTNode = body


def parse_repeat(parser: ParserProtocol) -> RepeatNode:
    """Parse a repeat statement.

    Parses repeat syntax: repeat (count) { body }

    Args:
        parser: The parser instance

    Returns:
        RepeatNode containing the count and body
    """
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Use the new eat return value for strict typing
    count_token = parser.eat(TokenType.NUMBER)
    count: int = count_token.value

    parser.eat(TokenType.COMMA)

    body = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.RPAREN)

    return RepeatNode(count, body)


def execute_repeat(interpreter: Interpreter, node: RepeatNode) -> None:
    """Execute a repeat node by evaluating body a fixed number of times.

    Args:
        interpreter: The interpreter instance
        node: The RepeatNode to execute
    """
    for _ in range(node.count):
        interpreter.visit(node.body)


def register(parser: Any) -> None:
    """Register the repeat plugin with the parser and interpreter.

    Registers:
    - 'repeat' keyword for repeat statements
    - RepeatNode visitor with the interpreter

    Args:
        parser: The parser instance to register with
    """
    parser.register_token_handler("REPEAT", parse_repeat)

    if not hasattr(Interpreter, "plugin_visitors"):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[RepeatNode] = execute_repeat
