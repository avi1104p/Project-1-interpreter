# token.py
# Defines the Token data class. Every token produced by the Scanner carries
# four fields: its type (TokenType), its raw lexeme (the source text it came
# from), its literal value (a Python float or str for numbers/strings, else
# None), and the line number it appeared on for error reporting.

from token_type import TokenType

class Token:
    def __init__(self, type: TokenType, lexeme: str, literal, line: int):
        self.type    = type     # TokenType enum value
        self.lexeme  = lexeme   # Raw source text, e.g. "while", "123", "+"
        self.literal = literal  # Python value for strings/numbers, else None
        self.line    = line     # Source line number (for error messages)

    def __repr__(self):
        return f"Token({self.type}, {self.lexeme!r}, {self.literal})"