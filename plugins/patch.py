from src.lexer import TokenType
from src.ast_nodes import ASTNode, Identifier

class PatchNode(ASTNode):
    def __init__(self, target_id, new_id):
        self.target_id = target_id
        self.new_id = new_id

def parse_patch(parser):
    # PATCH ( id1 , id2 )
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    target = parser.parse_identifier()
    parser.eat(TokenType.COMMA)
    new_val = parser.parse_identifier() # Or expression?
    # "replaces first identifier with second"
    # Usually patch means "redefine symbol".

    parser.eat(TokenType.RPAREN)
    return PatchNode(target.name, new_val.name)

def execute_patch(node, interpreter):
    # What does PATCH do?
    # "replaces first identifier with second"
    # Does it alias them?
    # interpreter.context.set(node.target_id, interpreter.context.get(node.new_id))

    val = interpreter.context.get(node.new_id)
    interpreter.context.set(node.target_id, val)

def register(parser):
    parser.register_extension('PATCH', parse_patch)

    from src.interpreter import Interpreter
    original_visit = Interpreter.visit

    def visit_PatchNode(self, node):
        execute_patch(node, self)
        return None

    Interpreter.visit_PatchNode = visit_PatchNode

    def new_visit(self, node):
        if isinstance(node, PatchNode):
            return self.visit_PatchNode(node)
        return original_visit(self, node)

    Interpreter.visit = new_visit
