from src.lexer import TokenType
from src.ast_nodes import ASTNode
from src.interpreter import Interpreter

class ForLoopNode(ASTNode):
    def __init__(self, var_name, items, body):
        self.var_name = var_name
        self.items = items
        self.body = body

def parse_for(parser):
    # Consumed FOR token via Identifier NUD hook
    # Current token is IDENTIFIER(FOR).
    # NUD handler consumes the current token usually.
    # So we eat 'FOR'.
    parser.eat(TokenType.IDENTIFIER)

    parser.eat(TokenType.LPAREN)

    # Arg 1: Identifier (Variable Name)
    # Use explicit `parse_identifier_node` if available or `parse_identifier`
    # But `parse_identifier` might be NUD which triggers handler recursively?
    # No, `FOR` handler is triggered because value is `FOR`.
    # `parse_identifier_node` in Parser just eats IDENTIFIER.
    var_name_node = parser.parse_identifier_node()
    var_name = var_name_node.name

    parser.eat(TokenType.COMMA)

    # Arg 2: Array Expression
    # "FOR parser will eat a deterministic number (3) of arguments"
    # So we parse one expression for the array.
    from src.parser import Precedence
    items_expr = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.COMMA)

    # Arg 3: Statement
    body = parser.parse_expression(Precedence.LOWEST)

    parser.eat(TokenType.RPAREN)

    return ForLoopNode(var_name, items_expr, body)

def execute_for(interpreter, node):
    # Evaluate items expression. Should return a list.
    items_val = interpreter.visit(node.items)

    if not isinstance(items_val, list):
        raise Exception(f"FOR loop expects an array/list as second argument, got {type(items_val)}")

    for val in items_val:
        interpreter.context.set(node.var_name, val)
        interpreter.visit(node.body)

def register(parser):
    # Register parser extension
    # In Pratt parser, we can hook into Identifier NUD by value
    if hasattr(parser, 'register_token_handler'):
        parser.register_token_handler('FOR', parse_for)
    else:
        # Fallback for old parser (though strictness might break old scripts)
        parser.register_extension('FOR', parse_for)

    # Register interpreter visitor
    # We need to access the active interpreter instance?
    # Plugins load in `main.py` before Interpreter is instantiated?
    # No, `main.py`:
    #   parser = Parser(lexer)
    #   load_plugins(parser)
    #   ast = parser.parse_program()
    #   interpreter = Interpreter()
    #   interpreter.visit(ast)

    # Wait. The `Interpreter` is instantiated LATER.
    # How do plugins register visitors to the interpreter?
    # The old way monkey-patched the *class* `Interpreter`.
    # The new way: `Interpreter` has `visitors` dict.
    # If we modify `Interpreter.visitors` (if it was a class attribute), it would work.
    # But `visitors` is instance attribute.
    # However, `Interpreter` is not passed to `register`. Only `parser`.

    # But we can monkey-patch the `Interpreter` class `__init__` or `register_core_visitors`?
    # OR we can continue to monkey-patch `Interpreter` class to auto-register?

    # Better approach: Monkey-patch `Interpreter.register_core_visitors`?
    # Or simply add to a global registry that Interpreter reads?

    # Or, maintain the pattern:
    # "The `Interpreter` could maintain a registry of visitors... and plugins could register their specific node visitors upon loading."
    # If plugins load BEFORE interpreter creation, they can't call `interpreter.register_visitor`.

    # But `load_plugins` is called with `parser`.
    # It does NOT receive interpreter class/instance.

    # Solution: We can patch `Interpreter` class.
    # Or add a static registry to `Interpreter` class?

    # Let's add a static method or class-level registry.

    # Since I'm refactoring `Interpreter`, I can add `Interpreter.plugin_visitors = {}`.
    # `Interpreter.__init__` will merge this into `self.visitors`.

    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[ForLoopNode] = execute_for

    # Also patch __init__ to ensure it picks it up?
    # I'll update `Interpreter` class in `src/interpreter.py` to support this.
    # But I already wrote `src/interpreter.py`.
    # I should update `src/interpreter.py` to read `Interpreter.plugin_visitors`.

