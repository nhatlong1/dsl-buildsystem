from typing import Any, Optional
from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter


class TryNode(ASTNode):
    """AST node representing a try-catch block.

    Attributes:
        operation: ASTNode representing the operation to try
        catch_stmt: ASTNode representing the catch statement
    """

    def __init__(self, operation: ASTNode, catch_stmt: ASTNode) -> None:
        """Initialize a TryNode.

        Args:
            operation: ASTNode representing the operation to try
            catch_stmt: ASTNode representing the catch statement
        """
        self.operation: ASTNode = operation
        self.catch_stmt: ASTNode = catch_stmt


def parse_try(parser: Any) -> TryNode:
    """Parse a try-catch block.

    Parses try-catch syntax: try (operation, catch)

    Args:
        parser: The parser instance

    Returns:
        TryNode containing the operation and catch statement
    """
    # TRY ( operation , catch )
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Parse operation (expression/statement)
    # Using Precedence.LOWEST default if not specified
    operation = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.COMMA)

    # Parse catch statement
    catch_stmt = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.RPAREN)

    return TryNode(operation, catch_stmt)


def execute_try(interpreter: Interpreter, node: TryNode) -> Any:
    """Execute a try-catch block.

    Args:
        interpreter: The interpreter instance
        node: The TryNode to execute

    Returns:
        The result of the operation if successful, or the result of the catch statement
    """
    try:
        return interpreter.visit(node.operation)
    except Exception as e:
        interpreter.context.set("LAST_ERROR", str(e))
        return interpreter.visit(node.catch_stmt)


def register(parser: Any) -> None:
    """Register the try-catch plugin with the parser and interpreter.

    Registers:
    - 'TRY' keyword for try-catch statements
    - TryNode visitor with the interpreter

    Args:
        parser: The parser instance to register with
    """
    parser.register_token_handler("TRY", parse_try)

    # Register Visitor (Standard way)
    if not hasattr(Interpreter, "plugin_visitors"):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[TryNode] = execute_try
