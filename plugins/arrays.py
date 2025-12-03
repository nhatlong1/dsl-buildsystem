from src.lexer import TokenType
from src.ast_nodes import ASTNode
from src.interpreter import Interpreter

class ArrayNode(ASTNode):
    def __init__(self, items):
        self.items = items # List of AST nodes

def parse_array(parser):
    # Consumed LBRACKET (via NUD)
    parser.eat(TokenType.LBRACKET)

    items = []
    if parser.current_token.type != TokenType.RBRACKET:
        # Parse expression list
        # Similar to parse_arg_list but using ] as terminator check
        from src.parser import Precedence
        items.append(parser.parse_expression(Precedence.LOWEST))
        while parser.current_token.type == TokenType.COMMA:
            parser.eat(TokenType.COMMA)
            items.append(parser.parse_expression(Precedence.LOWEST))

    parser.eat(TokenType.RBRACKET)
    return ArrayNode(items)

def execute_array(interpreter, node):
    # Evaluate all items
    return [interpreter.visit(item) for item in node.items]

def register(parser):
    # Register [ as Prefix (NUD)
    if hasattr(parser, 'register_prefix'):
        parser.register_prefix(TokenType.LBRACKET, lambda: parse_array(parser))

    # Register Visitor
    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[ArrayNode] = execute_array
