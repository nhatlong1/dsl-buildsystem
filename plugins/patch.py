from src.types import TokenType, ASTNode
from src.interpreter import Interpreter

class PatchNode(ASTNode):
    def __init__(self, target_id, new_id):
        self.target_id = target_id
        self.new_id = new_id

def parse_patch(parser):
    # PATCH ( id1 , id2 )
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Use non-NUD parser to avoid parsing an expression
    target = parser.parse_identifier_node()
    parser.eat(TokenType.COMMA)
    new_val = parser.parse_identifier_node()

    parser.eat(TokenType.RPAREN)
    # Target.name might be Identifier object or string?
    # `parse_identifier` returns `Identifier` node.
    return PatchNode(target.name, new_val.name)

def execute_patch(interpreter, node):
    val = interpreter.context.get(node.new_id)
    interpreter.context.set(node.target_id, val)

def register(parser):
    parser.register_token_handler('PATCH', parse_patch)

    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[PatchNode] = execute_patch
