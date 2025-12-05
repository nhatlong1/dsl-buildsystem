from typing import Any, Optional, List

from src.protocols import ParserProtocol
from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter
from src.types import Token


class RepeatNode(ASTNode):
    """AST node representing a repeat statement for fixed iterations.

    Attributes:
        count: AST node representing the number of times to repeat
        body: AST node representing the body to execute repeatedly
    """

    def __init__(self, count: int, body: List[ASTNode]) -> None:
        """Initialize a RepeatNode.

        Args:
            count: AST node for the repeat count expression
            body: AST node for the body to repeat
        """
        self.count: int = count
        self.body: List[ASTNode] = body


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

    count_token: Token = parser.current_token
    parser.eat(TokenType.NUMBER)
    count: int = count_token.value

    parser.eat(TokenType.COMMA)

    body = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.RPAREN)

    return RepeatNode(count, [body])


def execute_repeat(interpreter: Interpreter, node: RepeatNode) -> Optional[List[Any]]:
    """Execute a repeat node by evaluating body a fixed number of times.

    Args:
        interpreter: The interpreter instance
        node: The RepeatNode to execute

    Returns:
        List of all results from each iteration, or None if count is invalid
    """
    for _ in range(node.count):
        for stmt in node.body:
            interpreter.visit(stmt)


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
