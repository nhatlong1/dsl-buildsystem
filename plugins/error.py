from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter

class TryNode(ASTNode):
    def __init__(self, operation, catch_stmt):
        self.operation = operation
        self.catch_stmt = catch_stmt

def parse_try(parser):
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

def execute_try(interpreter, node):
    try:
        return interpreter.visit(node.operation)
    except Exception as e:
        interpreter.context.set("LAST_ERROR", str(e))
        return interpreter.visit(node.catch_stmt)

def register(parser):
    parser.register_token_handler('TRY', parse_try)

    # Register Visitor (Standard way)
    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[TryNode] = execute_try
