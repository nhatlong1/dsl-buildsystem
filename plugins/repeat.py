from src.lexer import TokenType
from src.ast_nodes import ASTNode, Identifier, Literal

class RepeatNode(ASTNode):
    def __init__(self, count, body):
        self.count = count
        self.body = body

def parse_repeat(parser):
    # Consumed REPEAT token (it was the identifier that triggered this)
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Expect a number (count)
    count_token = parser.current_token
    parser.eat(TokenType.NUMBER)
    count = count_token.value

    parser.eat(TokenType.COMMA)

    # Parse the statement to be repeated
    body = parser.parse_expression()

    parser.eat(TokenType.RPAREN)

    return RepeatNode(count, [body])

def execute_repeat(node, interpreter):
    # We need to register this handler in the interpreter?
    # Or does the interpreter need to know about RepeatNode?
    # The interpreter uses `visit`. It dispatches based on type.
    # We can monkey-patch the interpreter or register a handler if we had a registry.
    # But `visit` uses `isinstance`.

    # We can inject a visit method for RepeatNode into the Interpreter class?
    # Or better, the plugin system should allow registering runtime handlers too.

    # But for now, since `visit` is hardcoded with elifs, we might need a `visit_Extension` hook.
    # Or, we can modify Interpreter to allow dynamic dispatch.

    for _ in range(node.count):
        for stmt in node.body:
            interpreter.visit(stmt)

def register(parser):
    parser.register_extension('REPEAT', parse_repeat)

    # We also need to tell the interpreter how to handle RepeatNode.
    # Since we can't easily pass the interpreter instance here during parse time,
    # we might need to rely on the fact that we can patch the Interpreter class
    # or the Interpreter instance needs to load plugins too.

    # Let's patch the Interpreter class or add a method.
    from src.interpreter import Interpreter

    # Add visit_RepeatNode method
    def visit_RepeatNode(self, node):
        execute_repeat(node, self)

    Interpreter.visit_RepeatNode = visit_RepeatNode

    # We also need to update `visit` to call it.
    # This is the tricky part with the current implementation of `visit`.
    # `visit` has a specific chain of `if isinstance`.
    # We can monkey patch `visit`?

    original_visit = Interpreter.visit

    def new_visit(self, node):
        if isinstance(node, RepeatNode):
            return self.visit_RepeatNode(node)
        return original_visit(self, node)

    Interpreter.visit = new_visit
