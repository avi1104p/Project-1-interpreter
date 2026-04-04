# interpreter.py
# The Tree-Walk Interpreter for Lox. Implements the Visitor pattern to walk the
# AST produced by the Parser and execute each node. Expression visitors return
# a value; statement visitors execute side effects and return None. Manages a
# chain of Environments for variable scoping. Lox truthiness rules differ from
# Python — only nil and false are falsy, everything else including 0 and empty
# string is truthy. Runtime errors are caught at the top level and reported
# with a line number.

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 7 - "Evaluating Expressions" / Section: "Evaluating Expressions"
# https://craftinginterpreters.com/evaluating-expressions.html#evaluating-expressions

from token_type    import TokenType
from runtime_error import RuntimeError
from environment   import Environment
import expr as Expr
import stmt as Stmt


class Interpreter:
    def __init__(self, error_reporter):
        self.error_reporter = error_reporter
        self.environment = Environment()

    def interpret(self, statements: list):
        try:
            for statement in statements:
                self._execute(statement)
        except RuntimeError as e:
            self.error_reporter(e)

    # ── Statement visitors ────────────────────────────────────────────────────

    def visit_expression_stmt(self, stmt: Stmt.Expression):
        self._evaluate(stmt.expression)

    def visit_print_stmt(self, stmt: Stmt.Print):
        value = self._evaluate(stmt.expression)
        print(self._stringify(value))

    def visit_var_stmt(self, stmt: Stmt.Var):
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 8 - "Statements and State" / Section: "Blocks"
    # https://craftinginterpreters.com/statements-and-state.html#block-syntax-and-semantics
    def visit_block_stmt(self, stmt: Stmt.Block):
        new_env = Environment(enclosing=self.environment)
        self._execute_block(stmt.statements, new_env)

    def visit_if_stmt(self, stmt: Stmt.If):
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)

    def visit_while_stmt(self, stmt: Stmt.While):
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)

    def visit_function_stmt(self, stmt: Stmt.Function):
        from lox_function import LoxFunction
        function = LoxFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 10 - "Functions" / Section: "Return Statements"
    # https://craftinginterpreters.com/functions.html#return-statements
    def visit_return_stmt(self, stmt: Stmt.Return):
        from lox_function import ReturnException
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        raise ReturnException(value)

    # ── Expression visitors ───────────────────────────────────────────────────

    def visit_literal_expr(self, expr: Expr.Literal):
        return expr.value

    def visit_grouping_expr(self, expr: Expr.Grouping):
        return self._evaluate(expr.expression)

    def visit_unary_expr(self, expr: Expr.Unary):
        right = self._evaluate(expr.right)
        match expr.operator.type:
            case TokenType.MINUS:
                self._check_number_operand(expr.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not self._is_truthy(right)
        return None

    def visit_binary_expr(self, expr: Expr.Binary):
        left  = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        match expr.operator.type:
            case TokenType.MINUS:
                self._check_number_operands(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.SLASH:
                self._check_number_operands(expr.operator, left, right)
                if right == 0:
                    raise RuntimeError(expr.operator, "Division by zero.")
                return float(left) / float(right)
            case TokenType.STAR:
                self._check_number_operands(expr.operator, left, right)
                return float(left) * float(right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise RuntimeError(expr.operator,
                    "Operands must be two numbers or two strings.")
            case TokenType.GREATER:
                self._check_number_operands(expr.operator, left, right)
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                self._check_number_operands(expr.operator, left, right)
                return float(left) >= float(right)
            case TokenType.LESS:
                self._check_number_operands(expr.operator, left, right)
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                self._check_number_operands(expr.operator, left, right)
                return float(left) <= float(right)
            case TokenType.BANG_EQUAL:
                return not self._is_equal(left, right)
            case TokenType.EQUAL_EQUAL:
                return self._is_equal(left, right)
        return None

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 9 - "Control Flow" / Section: "Logical Operators"
    # https://craftinginterpreters.com/control-flow.html#logical-operators
    def visit_logical_expr(self, expr: Expr.Logical):
        left = self._evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left
        return self._evaluate(expr.right)

    def visit_variable_expr(self, expr: Expr.Variable):
        return self.environment.get(expr.name)

    def visit_assign_expr(self, expr: Expr.Assign):
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 10 - "Functions" / Section: "Checking Arity"
    # https://craftinginterpreters.com/functions.html#checking-arity
    def visit_call_expr(self, expr: Expr.Call):
        from lox_callable import LoxCallable
        callee    = self._evaluate(expr.callee)
        arguments = [self._evaluate(arg) for arg in expr.arguments]
        if not isinstance(callee, LoxCallable):
            raise RuntimeError(expr.paren, "Can only call functions and classes.")
        if len(arguments) != callee.arity():
            raise RuntimeError(expr.paren,
                f"Expected {callee.arity()} arguments but got {len(arguments)}.")
        return callee.call(self, arguments)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _evaluate(self, expr):
        return expr.accept(self)

    def _execute(self, stmt):
        stmt.accept(self)

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 8 - "Statements and State" / Section: "Blocks"
    # https://craftinginterpreters.com/statements-and-state.html#block-syntax-and-semantics
    def _execute_block(self, statements: list, environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 7 - "Evaluating Expressions" / Section: "Truthiness and Falsiness"
    # https://craftinginterpreters.com/evaluating-expressions.html#truthiness-and-falsiness
    def _is_truthy(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 7 - "Evaluating Expressions" / Section: "Equality and Comparison"
    # https://craftinginterpreters.com/evaluating-expressions.html#equality-and-comparison
    def _is_equal(self, a, b) -> bool:
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b

    def _stringify(self, value) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            text = str(value)
            if text.endswith(".0"):
                text = text[:-2]
            return text
        return str(value)

    def _check_number_operand(self, operator, operand):
        if isinstance(operand, float):
            return
        raise RuntimeError(operator, "Operand must be a number.")

    def _check_number_operands(self, operator, left, right):
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RuntimeError(operator, "Operands must be numbers.")