from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter

class ForLoopNode(ASTNode):
    def __init__(self, var_name, items, body):
        self.var_name = var_name
        self.items = items
        self.body = body

def parse_for(parser):
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

def execute_for(interpreter, node):
    items_val = interpreter.visit(node.items)

    if not isinstance(items_val, list):
        raise Exception(f"FOR loop expects an array/list as second argument, got {type(items_val)}")

    for val in items_val:
        interpreter.context.set(node.var_name, val)
        interpreter.visit(node.body)

def register(parser):
    if hasattr(parser, 'register_token_handler'):
        parser.register_token_handler('FOR', parse_for)

    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[ForLoopNode] = execute_for
