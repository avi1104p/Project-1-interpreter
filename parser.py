# parser.py — Recursive Descent Parser
#
# Consumes a flat list of Tokens (from the Scanner) and produces a list of
# Stmt nodes (an AST) that the Interpreter will walk.
#
# Each grammar rule maps to one method.  Methods call each other in order of
# *increasing* precedence, so lower-precedence operators are parsed first and
# end up higher (closer to the root) in the tree.
#
# Grammar (simplified):
#   program     → statement* EOF
#   declaration → funDecl | varDecl | statement
#   statement   → exprStmt | ifStmt | printStmt | returnStmt
#               | whileStmt | forStmt | block
#   expression  → assignment
#   assignment  → IDENTIFIER "=" assignment | logic_or
#   logic_or    → logic_and ( "or"  logic_and )*
#   logic_and   → equality  ( "and" equality  )*
#   equality    → comparison ( ( "!=" | "==" ) comparison )*
#   comparison  → term ( ( ">" | ">=" | "<" | "<=" ) term )*
#   term        → factor ( ( "+" | "-" ) factor )*
#   factor      → unary  ( ( "*" | "/" ) unary  )*
#   unary       → ( "!" | "-" ) unary | call
#   call        → primary ( "(" arguments? ")" )*
#   primary     → NUMBER | STRING | "true" | "false" | "nil"
#               | "(" expression ")" | IDENTIFIER

from token_type import TokenType
import expr as Expr
import stmt as Stmt


class ParseError(Exception):
    """Sentinel exception used for synchronising after a parse error."""
    pass


class Parser:
    def __init__(self, tokens: list, error_reporter):
        self.tokens         = tokens
        self.error_reporter = error_reporter  # callable(token, message)
        self.current        = 0               # index of the next token to consume

    # ── Public entry point ────────────────────────────────────────────────────

    def parse(self) -> list:
        """Parse the token stream and return a list of Stmt nodes."""
        statements = []
        while not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
        return statements

    # ── Declaration rules ─────────────────────────────────────────────────────

    def _declaration(self):
        """Top-level rule; catches ParseError to synchronise and keep going."""
        try:
            if self._match(TokenType.FUN):
                return self._function("function")
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _function(self, kind: str):
        """Parse a function declaration: fun name(params) { body }"""
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")

        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        params = []
        if not self._check(TokenType.RIGHT_PAREN):
            # Parse comma-separated parameter names
            while True:
                if len(params) >= 255:
                    self._error(self._peek(), "Can't have more than 255 parameters.")
                params.append(self._consume(TokenType.IDENTIFIER, "Expect parameter name."))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self._consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return Stmt.Function(name, params, body)

    def _var_declaration(self):
        """Parse: var IDENTIFIER ( "=" expression )? ";" """
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Stmt.Var(name, initializer)

    # ── Statement rules ───────────────────────────────────────────────────────

    def _statement(self):
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.LEFT_BRACE):
            return Stmt.Block(self._block())
        return self._expression_statement()

    def _if_statement(self):
        """Parse: if ( condition ) thenBranch ( else elseBranch )?"""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()

        return Stmt.If(condition, then_branch, else_branch)

    def _print_statement(self):
        """Parse: print expression ;"""
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Stmt.Print(value)

    def _return_statement(self):
        """Parse: return expression? ;"""
        keyword = self._previous()   # the 'return' token (carries line number)
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Stmt.Return(keyword, value)

    def _while_statement(self):
        """Parse: while ( condition ) body"""
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")
        body = self._statement()
        return Stmt.While(condition, body)

    def _for_statement(self):
        """
        Desugars a for loop into a while loop — no new AST node needed.
        for (initializer; condition; increment) body
        becomes:
        {
            initializer
            while (condition) {
                body
                increment
            }
        }
        """
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        # Initializer: var decl, expression, or nothing
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        # Condition: if omitted, treat as 'true' (infinite loop until break/return)
        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        # Increment: optional expression after second semicolon
        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self._statement()

        # Desugar: append increment to end of body
        if increment is not None:
            body = Stmt.Block([body, Stmt.Expression(increment)])

        # Desugar: wrap body in while loop
        if condition is None:
            condition = Expr.Literal(True)
        body = Stmt.While(condition, body)

        # Desugar: prepend initializer in an outer block
        if initializer is not None:
            body = Stmt.Block([initializer, body])

        return body

    def _block(self) -> list:
        """Parse statements until '}' or EOF. Returns list of Stmt."""
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression_statement(self):
        """Parse a bare expression used as a statement."""
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Stmt.Expression(expr)

    # ── Expression rules (ordered lowest → highest precedence) ────────────────

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        """
        Parse assignment or fall through to logic_or.
        Assignment is right-associative: a = b = c parses as a = (b = c).
        We parse the left side as a normal expression first, then check for '='.
        If the left side turns out to be a Variable, it's a valid assignment target.
        """
        expr = self._or()

        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value  = self._assignment()   # recurse right-associatively

            if isinstance(expr, Expr.Variable):
                return Expr.Assign(expr.name, value)

            # Not a valid assignment target — report but don't throw
            self._error(equals, "Invalid assignment target.")

        return expr

    def _or(self):
        """logic_or → logic_and ( "or" logic_and )*"""
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right    = self._and()
            expr     = Expr.Logical(expr, operator, right)
        return expr

    def _and(self):
        """logic_and → equality ( "and" equality )*"""
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right    = self._equality()
            expr     = Expr.Logical(expr, operator, right)
        return expr

    def _equality(self):
        """equality → comparison ( ( "!=" | "==" ) comparison )*"""
        expr = self._comparison()
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right    = self._comparison()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _comparison(self):
        """comparison → term ( ( ">" | ">=" | "<" | "<=" ) term )*"""
        expr = self._term()
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                          TokenType.LESS,    TokenType.LESS_EQUAL):
            operator = self._previous()
            right    = self._term()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _term(self):
        """term → factor ( ( "+" | "-" ) factor )*"""
        expr = self._factor()
        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right    = self._factor()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _factor(self):
        """factor → unary ( ( "*" | "/" ) unary )*"""
        expr = self._unary()
        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right    = self._unary()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _unary(self):
        """unary → ( "!" | "-" ) unary | call"""
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right    = self._unary()
            return Expr.Unary(operator, right)
        return self._call()

    def _call(self):
        """
        call → primary ( "(" arguments? ")" )*
        Handles chained calls: fn(a)(b)(c)
        """
        expr = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, callee):
        """Parse the argument list of a call and return a Call node."""
        arguments = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self._error(self._peek(), "Can't have more than 255 arguments.")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return Expr.Call(callee, paren, arguments)

    def _primary(self):
        """Highest-precedence rule: literals, grouping, identifiers."""
        if self._match(TokenType.FALSE): return Expr.Literal(False)
        if self._match(TokenType.TRUE):  return Expr.Literal(True)
        if self._match(TokenType.NIL):   return Expr.Literal(None)

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Expr.Literal(self._previous().literal)

        if self._match(TokenType.IDENTIFIER):
            return Expr.Variable(self._previous())

        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Expr.Grouping(expr)

        raise self._error(self._peek(), "Expect expression.")

    # ── Token navigation helpers ───────────────────────────────────────────────

    def _match(self, *types) -> bool:
        """Consume the current token if it matches any of the given types."""
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, type: TokenType) -> bool:
        """Return True if the current token is of the given type (no consume)."""
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _advance(self):
        """Consume and return the current token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self):
        """Return the current token without consuming it."""
        return self.tokens[self.current]

    def _previous(self):
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _consume(self, type: TokenType, message: str):
        """Consume the current token if it matches type, else raise ParseError."""
        if self._check(type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token, message: str) -> ParseError:
        """Report a parse error and return a ParseError (caller decides to raise)."""
        if token.type == TokenType.EOF:
            self.error_reporter(token, f" at end: {message}")
        else:
            self.error_reporter(token, f" at '{token.lexeme}': {message}")
        return ParseError()

    def _synchronize(self):
        """
        Panic-mode error recovery: discard tokens until we find a statement boundary.
        This lets the parser keep going after an error to find more errors in one pass.
        """
        self._advance()
        statement_starters = {
            TokenType.CLASS, TokenType.FUN, TokenType.VAR, TokenType.FOR,
            TokenType.IF,    TokenType.WHILE, TokenType.PRINT, TokenType.RETURN,
        }
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in statement_starters:
                return
            self._advance()