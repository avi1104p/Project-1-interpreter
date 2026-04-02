# stmt.py — Statement AST nodes
#
# Statements don't produce values — they cause side effects.
# Same Visitor pattern as expr.py: pure data containers + accept().


class Stmt:
    """Base class for all statement nodes."""
    def accept(self, visitor):
        raise NotImplementedError


# ── Expression Statement ──────────────────────────────────────────────────────
# An expression used as a statement (result is discarded).
# Example: myFunc();   x + 1;
class Expression(Stmt):
    def __init__(self, expression):
        self.expression = expression   # Expr

    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)


# ── Print Statement ───────────────────────────────────────────────────────────
# Evaluates an expression and prints its value.
# Example: print "hello";   print 1 + 2;
class Print(Stmt):
    def __init__(self, expression):
        self.expression = expression   # Expr

    def accept(self, visitor):
        return visitor.visit_print_stmt(self)


# ── Var Statement ─────────────────────────────────────────────────────────────
# Declares a variable, optionally with an initializer.
# Example: var x = 5;   var y;
class Var(Stmt):
    def __init__(self, name, initializer):
        self.name        = name          # Token (IDENTIFIER)
        self.initializer = initializer   # Expr or None (if no "= value")

    def accept(self, visitor):
        return visitor.visit_var_stmt(self)


# ── Block Statement ───────────────────────────────────────────────────────────
# A list of statements inside { }.
# Creates a new nested scope when executed.
# Example: { var x = 1; print x; }
class Block(Stmt):
    def __init__(self, statements: list):
        self.statements = statements   # list[Stmt]

    def accept(self, visitor):
        return visitor.visit_block_stmt(self)


# ── If Statement ──────────────────────────────────────────────────────────────
# Conditional execution. else_branch may be None.
# Example: if (x > 0) print x; else print "neg";
class If(Stmt):
    def __init__(self, condition, then_branch, else_branch):
        self.condition   = condition    # Expr
        self.then_branch = then_branch  # Stmt
        self.else_branch = else_branch  # Stmt or None

    def accept(self, visitor):
        return visitor.visit_if_stmt(self)


# ── While Statement ───────────────────────────────────────────────────────────
# Loops while condition is truthy.
# Example: while (x > 0) { x = x - 1; }
class While(Stmt):
    def __init__(self, condition, body):
        self.condition = condition   # Expr
        self.body      = body        # Stmt

    def accept(self, visitor):
        return visitor.visit_while_stmt(self)


# ── Function Declaration ──────────────────────────────────────────────────────
# Declares a named function with parameters and a body.
# Example: fun add(a, b) { return a + b; }
class Function(Stmt):
    def __init__(self, name, params: list, body: list):
        self.name   = name    # Token (IDENTIFIER) — the function's name
        self.params = params  # list[Token] — parameter name tokens
        self.body   = body    # list[Stmt] — the statements inside { }

    def accept(self, visitor):
        return visitor.visit_function_stmt(self)


# ── Return Statement ──────────────────────────────────────────────────────────
# Returns a value from a function. value may be None (bare return).
# Example: return x + 1;   return;
class Return(Stmt):
    def __init__(self, keyword, value):
        self.keyword = keyword   # Token — used for error reporting line number
        self.value   = value     # Expr or None

    def accept(self, visitor):
        return visitor.visit_return_stmt(self)