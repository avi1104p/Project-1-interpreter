# runtime_error.py
# A custom exception for Lox runtime errors. Stores the Token that caused the
# error so the interpreter can report the exact line number. Raised by the
# Interpreter when operations go wrong at runtime (e.g. dividing by zero,
# calling a non-callable, using an undeclared variable, wrong argument count).

# runtime_error.py
#
# Raised by the Interpreter when a runtime error occurs (e.g. dividing by zero,
# calling a non-callable, wrong number of arguments, etc.).
#
# We store the token so we can report the line number where the error happened.

class RuntimeError(Exception):
    def __init__(self, token, message: str):
        super().__init__(message)
        self.token   = token    # Token — carries the line number for reporting
        self.message = message