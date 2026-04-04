# lox_callable.py
# Abstract base class that any callable Lox value must implement. Defines two
# methods: arity() returns how many arguments the callable expects, and call()
# executes it. The Interpreter checks isinstance(callee, LoxCallable) before
# calling anything — if the value is not a LoxCallable a runtime error is raised.

# Source: Crafting Interpreters by Robert Nystrom
# Chapter 10 - "Functions" / Section: "The Call Expression" & "Lox Callable"
# https://craftinginterpreters.com/functions.html#the-call-expression

from abc import ABC, abstractmethod


class LoxCallable(ABC):

    @abstractmethod
    def arity(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def call(self, interpreter, arguments: list):
        raise NotImplementedError