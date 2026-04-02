from token_type import TokenType
from token import Token

# Every Lox keyword maps to its TokenType.
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
        self.error_reporter  = error_reporter  # callable: (line, message) -> None
        self.tokens: list[Token] = []

        self.start   = 0   # Index of the first char of the current lexeme
        self.current = 0   # Index of the current char being examined
        self.line    = 1   # Current source line (1-based)

    # ── Public ────────────────────────────────────────────────────────────────

    def scan_tokens(self) -> list[Token]:
        """Scan the entire source and return a list of Tokens."""
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    # ── Core scanning loop ────────────────────────────────────────────────────

    def _scan_token(self):
        """Read one lexeme starting at self.start and emit the right token."""
        c = self._advance()

        match c:
            # Single-character tokens
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

            # One-or-two character tokens
            case '!':
                self._add_token(TokenType.BANG_EQUAL if self._match('=') else TokenType.BANG)
            case '=':
                self._add_token(TokenType.EQUAL_EQUAL if self._match('=') else TokenType.EQUAL)
            case '<':
                self._add_token(TokenType.LESS_EQUAL if self._match('=') else TokenType.LESS)
            case '>':
                self._add_token(TokenType.GREATER_EQUAL if self._match('=') else TokenType.GREATER)

            # Slash or comment
            case '/':
                if self._match('/'):
                    # A comment runs to end of line — consume but emit nothing.
                    while self._peek() != '\n' and not self._is_at_end():
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)

            # Whitespace — skip silently
            case ' ' | '\r' | '\t':
                pass
            case '\n':
                self.line += 1

            # String literals
            case '"':
                self._string()

            case _:
                if c.isdigit():
                    self._number()
                elif c.isalpha() or c == '_':
                    self._identifier()
                else:
                    self.error_reporter(self.line, f"Unexpected character '{c}'.")

    # ── Literal helpers ───────────────────────────────────────────────────────

    def _string(self):
        """Consume a "..." string literal, including the closing quote."""
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
            self._advance()

        if self._is_at_end():
            self.error_reporter(self.line, "Unterminated string.")
            return

        self._advance()  # closing "

        # Trim the surrounding quotes to get the actual string value.
        value = self.source[self.start + 1 : self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _number(self):
        """Consume an integer or decimal number literal."""
        while self._peek().isdigit():
            self._advance()

        # Look for a fractional part: digits DOT digits
        if self._peek() == '.' and self._peek_next().isdigit():
            self._advance()  # consume the '.'
            while self._peek().isdigit():
                self._advance()

        value = float(self.source[self.start : self.current])
        self._add_token(TokenType.NUMBER, value)

    def _identifier(self):
        """Consume an identifier or keyword."""
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()

        text = self.source[self.start : self.current]
        # If the text is a reserved word, use that type; otherwise IDENTIFIER.
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)

    # ── Low-level character utilities ─────────────────────────────────────────

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        """Consume the current character and return it."""
        ch = self.source[self.current]
        self.current += 1
        return ch

    def _match(self, expected: str) -> bool:
        """Consume the next char only if it equals `expected` (conditional advance)."""
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        """Look at the current char without consuming it."""
        if self._is_at_end():
            return '\0'
        return self.source[self.current]

    def _peek_next(self) -> str:
        """Look one char ahead without consuming (used for decimal detection)."""
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _add_token(self, type: TokenType, literal=None):
        """Emit a token from self.start to self.current."""
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type, text, literal, self.line))