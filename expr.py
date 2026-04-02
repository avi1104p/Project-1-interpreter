# expr.py — Expression AST nodes
#
# Each class represents one kind of expression node in the AST.
# Every node stores the child nodes / tokens it needs, and implements
# accept() so a Visitor can dispatch to the right visit_* method.
#
# Visitor pattern: instead of putting evaluation logic IN these nodes,
# we keep the nodes as pure data and let external classes (Interpreter,
# Printer, etc.) define what to DO with each node type.


class Expr:
    """Base class for all expression nodes."""
    def accept(self, visitor):
        raise NotImplementedError


# ── Literal ───────────────────────────────────────────────────────────────────
# A raw value: a number, string, boolean, or nil.
# Example: 42  "hello"  true  nil
class Literal(Expr):
    def __init__(self, value):
        self.value = value   # Python float, str, bool, or None

    def accept(self, visitor):
        return visitor.visit_literal_expr(self)


# ── Grouping ──────────────────────────────────────────────────────────────────
# Parentheses around an expression.
# Example: (1 + 2)
class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor):
        return visitor.visit_grouping_expr(self)


# ── Unary ─────────────────────────────────────────────────────────────────────
# A unary operator applied to one operand.
# Example: -5   !true
class Unary(Expr):
    def __init__(self, operator, right: Expr):
        self.operator = operator   # Token  (MINUS or BANG)
        self.right    = right      # Expr

    def accept(self, visitor):
        return visitor.visit_unary_expr(self)


# ── Binary ────────────────────────────────────────────────────────────────────
# A binary operator applied to two operands.
# Example: 1 + 2   x >= y   "hi" + "!"
class Binary(Expr):
    def __init__(self, left: Expr, operator, right: Expr):
        self.left     = left       # Expr
        self.operator = operator   # Token
        self.right    = right      # Expr

    def accept(self, visitor):
        return visitor.visit_binary_expr(self)


# ── Logical ───────────────────────────────────────────────────────────────────
# Short-circuit logical operators (and / or).
# Kept separate from Binary because evaluation short-circuits.
# Example: a and b   x or y
class Logical(Expr):
    def __init__(self, left: Expr, operator, right: Expr):
        self.left     = left
        self.operator = operator   # Token (AND or OR)
        self.right    = right

    def accept(self, visitor):
        return visitor.visit_logical_expr(self)


# ── Variable ──────────────────────────────────────────────────────────────────
# A variable reference (reading its value).
# Example: x   myVar
class Variable(Expr):
    def __init__(self, name):
        self.name = name   # Token (IDENTIFIER)

    def accept(self, visitor):
        return visitor.visit_variable_expr(self)


# ── Assign ────────────────────────────────────────────────────────────────────
# An assignment expression (writing a value to an existing variable).
# Example: x = 5
class Assign(Expr):
    def __init__(self, name, value: Expr):
        self.name  = name    # Token (IDENTIFIER)
        self.value = value   # Expr — the new value

    def accept(self, visitor):
        return visitor.visit_assign_expr(self)


# ── Call ──────────────────────────────────────────────────────────────────────
# A function call expression.
# Example: sayHi("world")   add(1, 2)
class Call(Expr):
    def __init__(self, callee: Expr, paren, arguments: list):
        self.callee    = callee      # Expr — expression that evaluates to a callable
        self.paren     = paren       # Token — the closing ')' used for error reporting
        self.arguments = arguments   # list[Expr]

    def accept(self, visitor):
        return visitor.visit_call_expr(self)