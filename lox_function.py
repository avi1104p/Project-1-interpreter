# lox_function.py
# Implements callable Lox functions. LoxFunction wraps a Function AST node
# together with the closure — the environment active when the function was
# defined. When called, it creates a new environment parented to the closure
# (not the call site), binds parameters to arguments, then executes the body.
# ReturnException is a control flow trick: instead of threading return values
# back through every _execute() call, a return statement throws this exception
# and call() catches it to extract the value. Functions that reach the end
# without a return statement implicitly return nil.

from lox_callable import LoxCallable
from environment  import Environment


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 10 - "Functions" / Section: "Return Statements"
# https://craftinginterpreters.com/functions.html#return-statements
class ReturnException(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 10 - "Functions" / Section: "Interpreting Function Declarations"
# https://craftinginterpreters.com/functions.html#interpreting-function-declarations
class LoxFunction(LoxCallable):
    def __init__(self, declaration, closure: Environment):
        self.declaration = declaration
        # Source: Crafting Interpreters by Robert Nystrom
        # Chapter 10 - "Functions" / Section: "Closures"
        # https://craftinginterpreters.com/functions.html#closures
        self.closure     = closure

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter, arguments: list):
        # Source: Crafting Interpreters by Robert Nystrom
        # Chapter 10 - "Functions" / Section: "Interpreting Function Declarations"
        # https://craftinginterpreters.com/functions.html#interpreting-function-declarations
        environment = Environment(enclosing=self.closure)

        for param, argument in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, argument)

        try:
            interpreter._execute_block(self.declaration.body, environment)
        except ReturnException as return_value:
            return return_value.value

        return None

    def __str__(self):
        return f"<fn {self.declaration.name.lexeme}>"