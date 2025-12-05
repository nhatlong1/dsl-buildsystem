from typing import Any, Dict
from src.types import ASTNode
from src.interpreter import Interpreter


class PatchNode(ASTNode):
    """AST node representing a patch operation for modifying objects.

    Attributes:
        target: AST node representing the object to be patched
        patches: Dictionary mapping property names to their new value AST nodes
    """

    def __init__(self, target: ASTNode, patches: Dict[str, ASTNode]) -> None:
        """Initialize a PatchNode.

        Args:
            target: AST node for the target object
            patches: Dictionary of property names to value AST nodes
        """
        self.target: ASTNode = target
        self.patches: Dict[str, ASTNode] = patches


def parse_patch(parser: Any) -> PatchNode:
    """Parse a patch statement.

    Parses patch syntax: patch target { key1: value1, key2: value2 }

    Args:
        parser: The parser instance

    Returns:
        PatchNode containing the target and patch operations
    """
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


def execute_patch(interpreter: Interpreter, node: PatchNode) -> Any:
    """Execute a patch node by modifying the target object.

    Args:
        interpreter: The interpreter instance
        node: The PatchNode to execute

    Returns:
        The patched object (a modified copy)
    """
    val = interpreter.context.get(node.new_id)
    interpreter.context.set(node.target_id, val)


def register(parser: Any) -> None:
    """Register the patch plugin with the parser and interpreter.

    Registers:
    - 'patch' keyword for patch statements
    - PatchNode visitor with the interpreter

    Args:
        parser: The parser instance to register with
    """
    parser.register_token_handler("PATCH", parse_patch)

    if not hasattr(Interpreter, "plugin_visitors"):
        Interpreter.plugin_visitors = {}

    Interpreter.plugin_visitors[PatchNode] = execute_patch
