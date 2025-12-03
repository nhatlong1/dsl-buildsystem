import sys
import os
from src.lexer import Lexer
from src.parser import Parser, load_plugins, pretty_print
from src.interpreter import Interpreter

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <buildfile>")
        return

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        text = f.read()

    # Parse
    lexer = Lexer(text)
    parser = Parser(lexer)

    # Load Plugins
    load_plugins(parser)

    try:
        ast = parser.parse_program()

        # Pretty Print (Requirement)
        print("--- Parsed AST ---")
        pretty_print(ast)
        print("--- Execution ---")

        # Execute
        interpreter = Interpreter()
        interpreter.visit(ast)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
