# expr.py
# Defines all expression AST node classes for Lox. Each class represents one
# kind of expression (literal values, unary/binary operations, variable reads,
# assignments, function calls, etc.). Nodes are pure data containers with no
# evaluation logic — they implement accept() so an external Visitor (the
# Interpreter) can dispatch to the correct visit_* method for each node type.

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 5 - "Representing Code" / Section: "Metaprogramming the Trees"
# https://craftinginterpreters.com/representing-code.html#metaprogramming-the-trees
# Note: The book auto-generates these classes using a GenerateAst.java script.
# I wrote them by hand in Python instead for clarity and readability.

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 5 - "Representing Code" / Section: "The Visitor Pattern"
# https://craftinginterpreters.com/representing-code.html#the-visitor-pattern
class Expr:
    def accept(self, visitor):
        raise NotImplementedError

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 5 - "Representing Code" / Section: "Representing Code"
# https://craftinginterpreters.com/representing-code.html
class Literal(Expr):
    def __init__(self, value):
        self.value = value

    def accept(self, visitor):
        return visitor.visit_literal_expr(self)


class Grouping(Expr):
    def __init__(self, expression):
        self.expression = expression

    def accept(self, visitor):
        return visitor.visit_grouping_expr(self)


class Unary(Expr):
    def __init__(self, operator, right):
        self.operator = operator
        self.right    = right

    def accept(self, visitor):
        return visitor.visit_unary_expr(self)


class Binary(Expr):
    def __init__(self, left, operator, right):
        self.left     = left
        self.operator = operator
        self.right    = right

    def accept(self, visitor):
        return visitor.visit_binary_expr(self)


class Logical(Expr):
    def __init__(self, left, operator, right):
        self.left     = left
        self.operator = operator
        self.right    = right

    def accept(self, visitor):
        return visitor.visit_logical_expr(self)


class Variable(Expr):
    def __init__(self, name):
        self.name = name

    def accept(self, visitor):
        return visitor.visit_variable_expr(self)


class Assign(Expr):
    def __init__(self, name, value):
        self.name  = name
        self.value = value

    def accept(self, visitor):
        return visitor.visit_assign_expr(self)


class Call(Expr):
    def __init__(self, callee, paren, arguments):
        self.callee    = callee
        self.paren     = paren
        self.arguments = arguments

    def accept(self, visitor):
        return visitor.visit_call_expr(self)