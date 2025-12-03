from src.lexer import TokenType
from src.ast_nodes import ASTNode
from src.interpreter import Interpreter

class PipelineNode(ASTNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

def parse_pipeline(left, parser=None): # Note: Infix handlers in Pratt parser receive `left` arg.
    # Note: Our Pratt parser implementation `infix(left)` calling convention.
    # We need access to `parser` instance.
    # But `register_infix` stores `(fn, precedence)`.
    # And calls `left = infix(left)`.
    # Wait, `infix` function in `src/parser.py` is called as `infix(left)`.
    # It doesn't pass `self` (parser instance) explicitly if `infix` is a bound method.
    # But here `parse_pipeline` is a standalone function.
    # We need to change `src/parser.py` to pass `self` to the handler?
    # Or we use a closure/lambda when registering.

    # Let's check `src/parser.py`:
    # `infix, _ = infix_tuple`
    # `left = infix(left)`
    # So `infix` must be a callable accepting `left`.
    # If it needs parser, it must be bound or capture it.
    pass

# We will define the handler wrapper in `register`.

def execute_pipeline(interpreter, node):
    # Evaluate left side
    left_val = interpreter.visit(node.left)

    # Right side is a FunctionCall.
    from src.ast_nodes import Literal

    arg_node = Literal(left_val)

    # Construct new args list
    new_args = [arg_node] + node.right.args

    # Call the function
    return interpreter.context.call_function(node.right.name.name, new_args, interpreter)

def register(parser):
    # Register Infix Operator
    from src.parser import Precedence

    def pipeline_handler(left):
        parser.eat(TokenType.PIPE_GT)
        # Right side usually FunctionCall, but `parse_expression` handles it via LED of `(`.
        # Wait, right side of pipe `x |> f(...)`.
        # `f(...)` is an expression.
        # But pipeline logic often implies `f` is just the name?
        # Sample: `val |> func(args)`.
        # `func(args)` is a FunctionCall.
        # So we parse expression with slightly higher precedence?
        # Right associativity?
        # `a |> b |> c` -> `(a |> b) |> c`. Left associative.
        # So we use `parse_expression(Precedence.PIPELINE)`.

        right = parser.parse_expression(Precedence.PIPELINE)

        # Verify right is FunctionCall?
        # User might do `x |> print`.
        # If `print` is Identifier, we might want to support `x |> print` -> `print(x)`.
        # But typically `|>` injects into first arg.
        # If right is Identifier `f`, we treat as `f()`.
        # But `parse_expression` returns `FunctionCall` if `f(...)`.
        # If just `f`, it returns `Identifier`.

        from src.ast_nodes import Identifier, FunctionCall
        if isinstance(right, Identifier):
            # Transform to FunctionCall(name=right, args=[])
            right = FunctionCall(name=right, args=[])

        return PipelineNode(left, right)

    # Use register_infix if available
    if hasattr(parser, 'register_infix'):
        parser.register_infix(TokenType.PIPE_GT, pipeline_handler, Precedence.PIPELINE)
    else:
        print("Warning: Pipeline plugin requires Pratt parser.")

    # Register Interpreter Visitor
    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[PipelineNode] = execute_pipeline
