# environment.py
# Manages variable storage and scoping for Lox. Each Environment is a hash map
# of variable names to values, with a pointer to its enclosing (parent) scope.
# Variable lookup walks up the chain until it finds the name or errors. The key
# distinction: define() always creates a variable in the current scope, while
# assign() walks up the chain to update an existing one — assigning to an
# undeclared variable is a runtime error in Lox.

from runtime_error import RuntimeError


# Source: Crafting Interpreters by Robert Nystrom
# Chapter 8 - "Statements and State" / Section: "Environments"
# https://craftinginterpreters.com/statements-and-state.html#environments
class Environment:
    def __init__(self, enclosing=None):
        self.values    = {}
        self.enclosing = enclosing

    def define(self, name: str, value):
        # Source: Crafting Interpreters by Robert Nystrom
        # Chapter 8 - "Statements and State" / Section: "Assignment"
        # https://craftinginterpreters.com/statements-and-state.html#assignment
        self.values[name] = value

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 8 - "Statements and State" / Section: "Scope"
    # https://craftinginterpreters.com/statements-and-state.html#nesting-and-shadowing
    def get(self, name):
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    # Source: Crafting Interpreters by Robert Nystrom
    # Chapter 8 - "Statements and State" / Section: "Assignment"
    # https://craftinginterpreters.com/statements-and-state.html#assignment
    def assign(self, name, value):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")