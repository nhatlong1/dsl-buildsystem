import sys
import os
import argparse
from src.lexer import Lexer
from src.parser import Parser, load_plugins, pretty_print
from src.interpreter import Interpreter

def main():
    parser = argparse.ArgumentParser(description="Build DSL Interpreter")
    parser.add_argument("file", help="Path to the build file")
    parser.add_argument("--parse-only", action="store_true", help="Parse and pretty-print AST, then exit (unless dry-run is also set)")
    parser.add_argument("--dry-run", action="store_true", help="Execute in dry-run mode (print commands instead of running)")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        return

    with open(args.file, 'r') as f:
        text = f.read()

    # Parse
    lexer = Lexer(text)
    pratt_parser = Parser(lexer)

    # Load Plugins
    load_plugins(pratt_parser)

    try:
        ast = pratt_parser.parse_program()

        # Logic for Flags:
        # 1. If --parse-only: Print AST.
        # 2. If --parse-only AND NOT --dry-run: Exit.
        # 3. If --dry-run OR (NOT --parse-only): Execute (with appropriate dry_run flag).

        should_print_ast = args.parse_only
        should_execute = (not args.parse_only) or args.dry_run

        if should_print_ast:
            print("--- Parsed AST ---")
            pretty_print(ast)

        if should_execute:
            if should_print_ast:
                 print("--- Execution ---")

            # Execute
            interpreter = Interpreter(dry_run=args.dry_run)
            interpreter.visit(ast)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
