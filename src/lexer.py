import re

class TokenType:
    IDENTIFIER = 'IDENTIFIER'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    BOOLEAN = 'BOOLEAN'
    NULL = 'NULL'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    COMMA = 'COMMA'
    DOT = 'DOT'
    AT = 'AT'
    STAR = 'STAR'
    LBRACE = 'LBRACE' # For potential syntax extensions
    RBRACE = 'RBRACE' # For potential syntax extensions
    EOF = 'EOF'

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.column})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[self.pos] if self.text else None

    def error(self, msg):
        raise Exception(f"Lexer error at line {self.line}, column {self.column}: {msg}")

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        self.pos += 1
        self.column += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos < len(self.text):
            return self.text[peek_pos]
        return None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        # Comments start with /* and end with */
        self.advance() # /
        self.advance() # *
        while self.current_char is not None:
            if self.current_char == '*' and self.peek() == '/':
                self.advance()
                self.advance()
                return
            self.advance()
        self.error("Unterminated comment")

    def number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def string(self):
        result = ''
        self.advance() # skip opening quote
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char in ['"', '\\', 'n', 't', 'r', '0']:
                    escape_map = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0', '"': '"', '\\': '\\'}
                    result += escape_map.get(self.current_char, self.current_char)
                else:
                    result += self.current_char
            else:
                result += self.current_char
            self.advance()

        if self.current_char != '"':
            self.error("Unterminated string")
        self.advance() # skip closing quote
        return result

    def identifier(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()

        if result == 'TRUE':
            return Token(TokenType.BOOLEAN, True, self.line, self.column)
        if result == 'FALSE':
            return Token(TokenType.BOOLEAN, False, self.line, self.column)
        if result == 'NULL':
            return Token(TokenType.NULL, None, self.line, self.column)

        return Token(TokenType.IDENTIFIER, result, self.line, self.column)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '/' and self.peek() == '*':
                self.skip_comment()
                continue

            if self.current_char.isdigit():
                return Token(TokenType.NUMBER, self.number(), self.line, self.column)

            if self.current_char == '"':
                return Token(TokenType.STRING, self.string(), self.line, self.column)

            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()

            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN, '(', self.line, self.column)

            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN, ')', self.line, self.column)

            if self.current_char == ',':
                self.advance()
                return Token(TokenType.COMMA, ',', self.line, self.column)

            if self.current_char == '.':
                self.advance()
                return Token(TokenType.DOT, '.', self.line, self.column)

            if self.current_char == '@':
                self.advance()
                return Token(TokenType.AT, '@', self.line, self.column)

            if self.current_char == '*':
                self.advance()
                return Token(TokenType.STAR, '*', self.line, self.column)

            if self.current_char == '{':
                self.advance()
                return Token(TokenType.LBRACE, '{', self.line, self.column)

            if self.current_char == '}':
                self.advance()
                return Token(TokenType.RBRACE, '}', self.line, self.column)

            self.error(f"Invalid character '{self.current_char}'")

        return Token(TokenType.EOF, None, self.line, self.column)
