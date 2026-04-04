# stmt.py
# Defines all statement AST node classes for Lox. Statements cause side effects
# (printing, declaring variables, control flow, function declarations) but do
# not produce values. Like expr.py, these are pure data containers that use the
# Visitor pattern via accept() so the Interpreter can execute each one.

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 5 - "Representing Code" / Section: "The Visitor Pattern"
# https://craftinginterpreters.com/representing-code.html#the-visitor-pattern
# Note: Same Visitor pattern as expr.py — pure data containers + accept().

class Stmt:
    def accept(self, visitor):
        raise NotImplementedError


class Expression(Stmt):
    def __init__(self, expression):
        self.expression = expression

    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)


class Print(Stmt):
    def __init__(self, expression):
        self.expression = expression

    def accept(self, visitor):
        return visitor.visit_print_stmt(self)


class Var(Stmt):
    def __init__(self, name, initializer):
        self.name        = name
        self.initializer = initializer

    def accept(self, visitor):
        return visitor.visit_var_stmt(self)


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 8 - "Statements and State" / Section: "Blocks"
# https://craftinginterpreters.com/statements-and-state.html#block-syntax-and-semantics
class Block(Stmt):
    def __init__(self, statements: list):
        self.statements = statements

    def accept(self, visitor):
        return visitor.visit_block_stmt(self)


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 9 - "Control Flow" / Section: "Conditional Execution"
# https://craftinginterpreters.com/control-flow.html#conditional-execution
class If(Stmt):
    def __init__(self, condition, then_branch, else_branch):
        self.condition   = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor):
        return visitor.visit_if_stmt(self)


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 9 - "Control Flow" / Section: "While Loops"
# https://craftinginterpreters.com/control-flow.html#while-loops
class While(Stmt):
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body

    def accept(self, visitor):
        return visitor.visit_while_stmt(self)


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 10 - "Functions" / Section: "Interpreting Function Declarations"
# https://craftinginterpreters.com/functions.html#interpreting-function-declarations
class Function(Stmt):
    def __init__(self, name, params: list, body: list):
        self.name   = name
        self.params = params
        self.body   = body

    def accept(self, visitor):
        return visitor.visit_function_stmt(self)


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 10 - "Functions" / Section: "Return Statements"
# https://craftinginterpreters.com/functions.html#return-statements
class Return(Stmt):
    def __init__(self, keyword, value):
        self.keyword = keyword
        self.value   = value

    def accept(self, visitor):
        return visitor.visit_return_stmt(self)