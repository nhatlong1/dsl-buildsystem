from src.lexer import TokenType
from src.ast_nodes import ASTNode, Identifier

class TryNode(ASTNode):
    def __init__(self, operation, catch_stmt):
        self.operation = operation
        self.catch_stmt = catch_stmt

def parse_try(parser):
    # TRY ( operation , catch )
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Parse operation (expression/statement)
    operation = parser.parse_expression()

    parser.eat(TokenType.COMMA)

    # Parse catch statement
    catch_stmt = parser.parse_expression()

    parser.eat(TokenType.RPAREN)

    return TryNode(operation, catch_stmt)

def execute_try(node, interpreter):
    try:
        return interpreter.visit(node.operation)
    except Exception as e:
        # User might want to access the exception?
        # The prompt says: "TRY(op, catch)".
        # It doesn't specify binding the error.
        # But usually catch needs to know what happened.
        # "TRY(operation, catch) = IF(EQ(TYPE(operation), Exception), catch, None)"
        # This implies `operation` returns Exception on failure.
        # But if we are catching Python exceptions, we just run catch_stmt.

        # We could set a global or context variable `LAST_ERROR`?
        interpreter.context.set("LAST_ERROR", str(e))
        return interpreter.visit(node.catch_stmt)

def register(parser):
    parser.register_extension('TRY', parse_try)

    from src.interpreter import Interpreter
    original_visit = Interpreter.visit

    def visit_TryNode(self, node):
        return execute_try(node, self)

    Interpreter.visit_TryNode = visit_TryNode

    def new_visit(self, node):
        if isinstance(node, TryNode):
            return self.visit_TryNode(node)
        return original_visit(self, node)

    Interpreter.visit = new_visit
