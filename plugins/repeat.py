from src.types import TokenType, ASTNode, Precedence
from src.interpreter import Interpreter

class RepeatNode(ASTNode):
    def __init__(self, count, body):
        self.count = count
        self.body = body

def parse_repeat(parser):
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    count_token = parser.current_token
    parser.eat(TokenType.NUMBER)
    count = count_token.value

    parser.eat(TokenType.COMMA)

    body = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.RPAREN)

    return RepeatNode(count, [body])

def execute_repeat(interpreter, node):
    for _ in range(node.count):
        for stmt in node.body:
            interpreter.visit(stmt)

def register(parser):
    parser.register_token_handler('REPEAT', parse_repeat)

    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[RepeatNode] = execute_repeat
