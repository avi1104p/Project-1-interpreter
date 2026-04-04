# parser.py
# The Recursive Descent Parser for Lox. Consumes the flat list of Tokens from
# the Scanner and builds a list of Stmt AST nodes. Each grammar rule maps to
# one method, and methods call each other in order of increasing precedence so
# lower-precedence operators sit higher (closer to the root) in the tree. Also
# handles panic-mode error recovery via _synchronize() so multiple errors can
# be reported in one pass. The for loop is desugared into a While node here at
# parse time — no separate For AST node is needed.

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 6 - "Parsing Expressions" / Section: "Recursive Descent Parsing"
# https://craftinginterpreters.com/parsing-expressions.html#recursive-descent-parsing

from token_type import TokenType
import expr as Expr
import stmt as Stmt


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list, error_reporter):
        self.tokens         = tokens
        self.error_reporter = error_reporter
        self.current        = 0

    def parse(self) -> list:
        statements = []
        while not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
        return statements

    # ── Declaration rules ─────────────────────────────────────────────────────

    def _declaration(self):
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
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        params = []
        if not self._check(TokenType.RIGHT_PAREN):
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
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Stmt.Var(name, initializer)

    # ── Statement rules ───────────────────────────────────────────────────────

    def _statement(self):
        if self._match(TokenType.IF):     return self._if_statement()
        if self._match(TokenType.PRINT):  return self._print_statement()
        if self._match(TokenType.RETURN): return self._return_statement()
        if self._match(TokenType.WHILE):  return self._while_statement()
        if self._match(TokenType.FOR):    return self._for_statement()
        if self._match(TokenType.LEFT_BRACE): return Stmt.Block(self._block())
        return self._expression_statement()

    def _if_statement(self):
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
        return Stmt.If(condition, then_branch, else_branch)

    def _print_statement(self):
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Stmt.Print(value)

    def _return_statement(self):
        keyword = self._previous()
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Stmt.Return(keyword, value)

    def _while_statement(self):
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")
        body = self._statement()
        return Stmt.While(condition, body)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 9 - "Control Flow" / Section: "Desugaring"
    # https://craftinginterpreters.com/control-flow.html#desugaring
    def _for_statement(self):
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self._statement()

        if increment is not None:
            body = Stmt.Block([body, Stmt.Expression(increment)])
        if condition is None:
            condition = Expr.Literal(True)
        body = Stmt.While(condition, body)
        if initializer is not None:
            body = Stmt.Block([initializer, body])

        return body

    def _block(self) -> list:
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression_statement(self):
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Stmt.Expression(expr)

    # ── Expression rules ──────────────────────────────────────────────────────
    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 6 - "Parsing Expressions" / Section: "A Grammar for Lox Expressions"
    # https://craftinginterpreters.com/parsing-expressions.html#ambiguity-and-the-parsing-game

    def _expression(self):
        return self._assignment()

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 8 - "Statements and State" / Section: "Assignment"
    # https://craftinginterpreters.com/statements-and-state.html#assignment
    def _assignment(self):
        expr = self._or()
        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value  = self._assignment()
            if isinstance(expr, Expr.Variable):
                return Expr.Assign(expr.name, value)
            self._error(equals, "Invalid assignment target.")
        return expr

    def _or(self):
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right    = self._and()
            expr     = Expr.Logical(expr, operator, right)
        return expr

    def _and(self):
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right    = self._equality()
            expr     = Expr.Logical(expr, operator, right)
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right    = self._comparison()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _comparison(self):
        expr = self._term()
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                          TokenType.LESS,    TokenType.LESS_EQUAL):
            operator = self._previous()
            right    = self._term()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _term(self):
        expr = self._factor()
        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right    = self._factor()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _factor(self):
        expr = self._unary()
        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right    = self._unary()
            expr     = Expr.Binary(expr, operator, right)
        return expr

    def _unary(self):
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right    = self._unary()
            return Expr.Unary(operator, right)
        return self._call()

    def _call(self):
        expr = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, callee):
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

    # ── Token navigation helpers ──────────────────────────────────────────────
    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 6 - "Parsing Expressions" / Section: "The Parser Class"
    # https://craftinginterpreters.com/parsing-expressions.html#the-parser-class

    def _match(self, *types) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _advance(self):
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self):
        return self.tokens[self.current]

    def _previous(self):
        return self.tokens[self.current - 1]

    def _consume(self, type: TokenType, message: str):
        if self._check(type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token, message: str) -> ParseError:
        if token.type == TokenType.EOF:
            self.error_reporter(token, f" at end: {message}")
        else:
            self.error_reporter(token, f" at '{token.lexeme}': {message}")
        return ParseError()

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 6 - "Parsing Expressions" / Section: "Synchronizing a Recursive Descent Parser"
    # https://craftinginterpreters.com/parsing-expressions.html#synchronizing-a-recursive-descent-parser
    def _synchronize(self):
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