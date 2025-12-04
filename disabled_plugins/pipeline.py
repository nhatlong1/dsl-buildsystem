from src.types import TokenType, ASTNode, Precedence, Identifier, FunctionCall, Literal
from src.interpreter import Interpreter

class PipelineNode(ASTNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

def execute_pipeline(interpreter, node):
    # Evaluate left side
    left_val = interpreter.visit(node.left)

    arg_node = Literal(left_val)

    # Construct new args list
    new_args = [arg_node] + node.right.args

    # Call the function
    return interpreter.context.call_function(node.right.name.name, new_args, interpreter)

def register(parser):
    def pipeline_handler(left):
        parser.eat(TokenType.PIPE_GT)

        right = parser.parse_expression(Precedence.PIPELINE)

        if isinstance(right, Identifier):
            # Transform to FunctionCall(name=right, args=[])
            right = FunctionCall(name=right, args=[])

        return PipelineNode(left, right)

    if hasattr(parser, 'register_infix'):
        parser.register_infix(TokenType.PIPE_GT, pipeline_handler, Precedence.PIPELINE)
    else:
        print("Warning: Pipeline plugin requires Pratt parser.")

    if not hasattr(Interpreter, 'plugin_visitors'):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[PipelineNode] = execute_pipeline
