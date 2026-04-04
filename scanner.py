# scanner.py
# The Lexer/Scanner for Lox. Takes raw source code as a string and produces a
# flat list of Token objects. It walks the source character by character using
# two pointers (start and current) to window over each lexeme. Handles single
# and double character operators, string and number literals, identifiers, and
# reserved keywords. Comments and whitespace are silently skipped.

from token_type import TokenType
from token import Token

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 4 - "Scanning" / Section: "Reserved Words and Identifiers"
# https://craftinginterpreters.com/scanning.html#reserved-words-and-identifiers
KEYWORDS = {
    "and":    TokenType.AND,
    "class":  TokenType.CLASS,
    "else":   TokenType.ELSE,
    "false":  TokenType.FALSE,
    "for":    TokenType.FOR,
    "fun":    TokenType.FUN,
    "if":     TokenType.IF,
    "nil":    TokenType.NIL,
    "or":     TokenType.OR,
    "print":  TokenType.PRINT,
    "return": TokenType.RETURN,
    "super":  TokenType.SUPER,
    "this":   TokenType.THIS,
    "true":   TokenType.TRUE,
    "var":    TokenType.VAR,
    "while":  TokenType.WHILE,
}


class Scanner:
    def __init__(self, source: str, error_reporter):
        self.source          = source
        self.error_reporter  = error_reporter
        self.tokens: list[Token] = []

        # Source: Crafting Interpreters by Robert Nystrom
        # Chapter 4 - "Scanning" / Section: "Lexemes and Tokens"
        # https://craftinginterpreters.com/scanning.html#lexemes-and-tokens
        self.start   = 0
        self.current = 0
        self.line    = 1

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def _scan_token(self):
        c = self._advance()
        match c:
            case '(': self._add_token(TokenType.LEFT_PAREN)
            case ')': self._add_token(TokenType.RIGHT_PAREN)
            case '{': self._add_token(TokenType.LEFT_BRACE)
            case '}': self._add_token(TokenType.RIGHT_BRACE)
            case ',': self._add_token(TokenType.COMMA)
            case '.': self._add_token(TokenType.DOT)
            case '-': self._add_token(TokenType.MINUS)
            case '+': self._add_token(TokenType.PLUS)
            case ';': self._add_token(TokenType.SEMICOLON)
            case '*': self._add_token(TokenType.STAR)

            # Source: Crafting Interpreters by Robert Nystrom
            # Chapter 4 - "Scanning" / Section: "Operators"
            # https://craftinginterpreters.com/scanning.html#operators
            case '!':
                self._add_token(TokenType.BANG_EQUAL if self._match('=') else TokenType.BANG)
            case '=':
                self._add_token(TokenType.EQUAL_EQUAL if self._match('=') else TokenType.EQUAL)
            case '<':
                self._add_token(TokenType.LESS_EQUAL if self._match('=') else TokenType.LESS)
            case '>':
                self._add_token(TokenType.GREATER_EQUAL if self._match('=') else TokenType.GREATER)

            case '/':
                if self._match('/'):
                    while self._peek() != '\n' and not self._is_at_end():
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)

            case ' ' | '\r' | '\t':
                pass
            case '\n':
                self.line += 1
            case '"':
                self._string()
            case _:
                if c.isdigit():
                    self._number()
                elif c.isalpha() or c == '_':
                    self._identifier()
                else:
                    self.error_reporter(self.line, f"Unexpected character '{c}'.")

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 4 - "Scanning" / Section: "Literals" > "Strings"
    # https://craftinginterpreters.com/scanning.html#string-literals
    def _string(self):
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
            self._advance()
        if self._is_at_end():
            self.error_reporter(self.line, "Unterminated string.")
            return
        self._advance()
        value = self.source[self.start + 1 : self.current - 1]
        self._add_token(TokenType.STRING, value)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 4 - "Scanning" / Section: "Literals" > "Numbers"
    # https://craftinginterpreters.com/scanning.html#number-literals
    def _number(self):
        while self._peek().isdigit():
            self._advance()
        if self._peek() == '.' and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        value = float(self.source[self.start : self.current])
        self._add_token(TokenType.NUMBER, value)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 4 - "Scanning" / Section: "Reserved Words and Identifiers"
    # https://craftinginterpreters.com/scanning.html#reserved-words-and-identifiers
    def _identifier(self):
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()
        text = self.source[self.start : self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 4 - "Scanning" / Section: "A Longer Look at Lookahead"
    # https://craftinginterpreters.com/scanning.html#a-longer-look-at-lookahead
    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _add_token(self, type: TokenType, literal=None):
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, literal, self.line))