from src.lexer import TokenType
from src.ast_nodes import ASTNode

class PipelineNode(ASTNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

def parse_pipeline(parser, left):
    # This is called by the patched parse_statement when it sees |>
    # left is the already parsed expression (e.g. function call)

    parser.eat(TokenType.PIPE_GT)

    # The right side must be a function call
    right = parser.parse_function_call()

    # We might have chained pipelines: a |> b |> c
    # `parse_statement` loop (below) handles this if we return PipelineNode,
    # and the loop checks for |> again.

    return PipelineNode(left, right)

def execute_pipeline(node, interpreter):
    # Evaluate left side
    left_val = interpreter.visit(node.left)

    # Right side is a FunctionCall.
    # We need to inject `left_val` as the first argument.
    # But `FunctionCall` in AST has `args` (list of expressions).
    # We can't easily modify the AST node here because it might be reused?
    # Actually, AST is usually static.
    # But here we are executing.
    # We can create a *new* list of args with the value injected?
    # But `call_function` expects AST nodes as args because it evaluates them!
    # `interpreter.visit_FunctionCall` -> `self.context.call_function(name, args, interp)`

    # We have a specific value `left_val`. We need to pass it as an argument.
    # We can wrap it in a `Literal` node?
    from src.ast_nodes import Literal

    arg_node = Literal(left_val)

    # Construct new args list
    new_args = [arg_node] + node.right.args

    # Call the function
    return interpreter.context.call_function(node.right.name.name, new_args, interpreter)

def register(parser):
    # We don't register a keyword extension.
    # We monkey-patch parse_statement to support infix operator `|>`

    # We need to access Parser class
    Parser = parser.__class__
    original_parse_statement = Parser.parse_statement

    def parse_statement_with_pipeline(self):
        # Parse the first part (standard statement/expression)
        # We replace original_parse_statement logic to allow arbitrary expressions
        # (needed for literals on left side of pipeline)

        # Check extensions first
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.value in self.keyword_extensions:
             return self.keyword_extensions[self.current_token.value](self)

        node = self.parse_expression()

        # Check for pipeline operator
        while self.current_token.type == TokenType.PIPE_GT:
            node = parse_pipeline(self, node)

        return node

    Parser.parse_statement = parse_statement_with_pipeline

    # Monkey-patch Interpreter
    from src.interpreter import Interpreter
    original_visit = Interpreter.visit

    def visit_PipelineNode(self, node):
        return execute_pipeline(node, self)

    Interpreter.visit_PipelineNode = visit_PipelineNode

    def new_visit(self, node):
        if isinstance(node, PipelineNode):
            return self.visit_PipelineNode(node)
        return original_visit(self, node)

    Interpreter.visit = new_visit
