import unittest
from src.lexer import Lexer, TokenType
from src.parser import Parser
from src.types import Program, FunctionCall, Literal, Identifier, PropertyAccess, Precedence

class TestParser(unittest.TestCase):
    def test_basic_program(self):
        code = 'ECHO("Hello")'
        lexer = Lexer(code)
        parser = Parser(lexer)
        program = parser.parse_program()

        self.assertIsInstance(program, Program)
        self.assertEqual(len(program.statements), 1)
        self.assertIsInstance(program.statements[0], FunctionCall)
        self.assertEqual(program.statements[0].name.name, 'ECHO')
        self.assertEqual(program.statements[0].args[0].value, 'Hello')

    def test_infix_expression(self):
        # DOT has precedence
        code = 'STAT("file").LASTMODIFIEDDATE'
        lexer = Lexer(code)
        parser = Parser(lexer)
        program = parser.parse_program()

        stmt = program.statements[0]
        self.assertIsInstance(stmt, PropertyAccess)
        self.assertIsInstance(stmt.target, FunctionCall)
        self.assertEqual(stmt.target.name.name, 'STAT')
        self.assertEqual(stmt.property_name.name, 'LASTMODIFIEDDATE')

    def test_nested_calls(self):
        code = 'IF(NOT(EXISTS("file")), ECHO("Missing"))'
        lexer = Lexer(code)
        parser = Parser(lexer)
        program = parser.parse_program()

        stmt = program.statements[0]
        self.assertIsInstance(stmt, FunctionCall)
        self.assertEqual(stmt.name.name, 'IF')
        self.assertEqual(len(stmt.args), 2)

        arg1 = stmt.args[0]
        self.assertIsInstance(arg1, FunctionCall)
        self.assertEqual(arg1.name.name, 'NOT')

        arg1_arg = arg1.args[0]
        self.assertIsInstance(arg1_arg, FunctionCall)
        self.assertEqual(arg1_arg.name.name, 'EXISTS')

if __name__ == '__main__':
    unittest.main()
