from token_type import TokenType

class Token:
    def __init__(self, type: TokenType, lexeme: str, literal, line: int):
        self.type    = type     # TokenType enum value
        self.lexeme  = lexeme   # Raw source text, e.g. "while", "123", "+"
        self.literal = literal  # Python value for strings/numbers, else None
        self.line    = line     # Source line number (for error messages)

    def __repr__(self):
        return f"Token({self.type}, {self.lexeme!r}, {self.literal})"