from src.lexer import TokenType
from src.ast_nodes import ASTNode

class ForLoopNode(ASTNode):
    def __init__(self, var_name, items, body):
        self.var_name = var_name
        self.items = items
        self.body = body

def parse_for(parser):
    # Consumed FOR token
    parser.eat(TokenType.IDENTIFIER)
    parser.eat(TokenType.LPAREN)

    # Arg 1: Identifier (Variable Name)
    var_name_node = parser.parse_identifier()
    var_name = var_name_node.name

    parser.eat(TokenType.COMMA)

    # Arg 2: List of items (arg_list)
    # The grammar says `arg_list`, which returns a list of expressions.
    # But wait, `arg_list` parses until it sees something that isn't a comma?
    # `parse_arg_list` in parser.py:
    # args = [self.parse_expression()]
    # while comma: eat comma, append parse_expression()
    # It stops when it sees something else (like RPAREN).
    # Here we are inside `FOR(...)`.
    # Structure: FOR ( id , item1, item2, item3 , stmt )
    # This is ambiguous if items are comma separated and stmt is after a comma.
    # How do we know which comma separates items from the statement?
    # The EBNF says: `identifier "," arg_list "," statement`.
    # `arg_list` consumes expressions separated by commas.
    # It will consume the statement too if it looks like an expression!
    # And `statement` IS a `function_call` which IS an expression.

    # Solution: The arguments passed to the loop are strictly the items.
    # The statement is the LAST argument?
    # User said: "loop pops the last argument as the statement".
    # This implies we parse *all* arguments as `arg_list`, and then take the last one as the body.

    items = []
    if parser.current_token.type != TokenType.RPAREN:
        items = parser.parse_arg_list()

    parser.eat(TokenType.RPAREN)

    if len(items) < 1:
        raise Exception("FOR loop requires at least a body statement")

    body = items.pop()
    # items is now the list to iterate over

    return ForLoopNode(var_name, items, body)

def execute_for(node, interpreter):
    # Evaluate items.
    # Items in AST are expressions. We need to evaluate them to get the list.
    # But wait, `items` from `parse_arg_list` is a list of AST nodes.
    # We should evaluate each node to get the value.

    evaluated_items = [interpreter.visit(item) for item in node.items]

    # Handle if items is actually a single list object?
    # `arg_list` returns [Expr, Expr].
    # If user passed `[1, 2, 3]`, that would be a single Expr (ArrayNode)?
    # But we don't have ArrayNode yet.
    # If user wrote `FOR(i, 1, 2, 3, print(i))`, then items=[1, 2, 3].

    for val in evaluated_items:
        # Set loop variable
        interpreter.context.set(node.var_name, val)
        # Execute body
        interpreter.visit(node.body)

def register(parser):
    parser.register_extension('FOR', parse_for)

    # Monkey-patch interpreter
    from src.interpreter import Interpreter
    original_visit = Interpreter.visit

    def visit_ForLoopNode(self, node):
        execute_for(node, self)

    Interpreter.visit_ForLoopNode = visit_ForLoopNode

    def new_visit(self, node):
        if isinstance(node, ForLoopNode):
            return self.visit_ForLoopNode(node)
        return original_visit(self, node)

    Interpreter.visit = new_visit
