# lox.py
# Entry point for the Lox interpreter. Handles two modes: running a .lox script
# file passed as a command line argument, or an interactive REPL if no file is
# given. Wires together the Scanner, Parser, and Interpreter in sequence. Also
# owns all error reporting — scan errors, parse errors, and runtime errors each
# have their own handler that prints a message with a line number and sets a
# flag so the process exits with the correct error code.

import sys
from scanner     import Scanner
from parser      import Parser
from interpreter import Interpreter
from runtime_error import RuntimeError as LoxRuntimeError


class Lox:
    had_error         = False
    had_runtime_error = False
    interpreter       = None  # single interpreter instance reused across REPL lines

    @classmethod
    def main(cls):
        cls.interpreter = Interpreter(cls.runtime_error)
        args = sys.argv[1:]
        if len(args) > 1:
            print("Usage: lox.py [script]")
            sys.exit(64)
        elif len(args) == 1:
            cls.run_file(args[0])
        else:
            cls.run_prompt()

    @classmethod
    def run_file(cls, path: str):
        with open(path, encoding="utf-8") as f:
            source = f.read()
        cls.run(source)
        if cls.had_error:
            sys.exit(65)
        if cls.had_runtime_error:
            sys.exit(70)

    @classmethod
    def run_prompt(cls):
        print("Lox REPL (Ctrl-C or Ctrl-D to exit)")
        while True:
            try:
                line = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            cls.run(line)
            cls.had_error = False

    @classmethod
    def run(cls, source: str):
        # ── Scan ──────────────────────────────────────────────────────────────
        scanner = Scanner(source, cls.scan_error)
        tokens  = scanner.scan_tokens()
        if cls.had_error:
            return

        # ── Parse ─────────────────────────────────────────────────────────────
        parser     = Parser(tokens, cls.parse_error)
        statements = parser.parse()
        if cls.had_error:
            return

        # ── Interpret ─────────────────────────────────────────────────────────
        cls.interpreter.interpret(statements)

    # ── Error reporters ───────────────────────────────────────────────────────

    @classmethod
    def scan_error(cls, line: int, message: str):
        cls._report(line, "", message)

    @classmethod
    def parse_error(cls, token, message: str):
        cls._report(token.line, message, "")

    @classmethod
    def runtime_error(cls, error: LoxRuntimeError):
        print(f"[line {error.token.line}] RuntimeError: {error.message}",
              file=sys.stderr)
        cls.had_runtime_error = True

    @classmethod
    def _report(cls, line: int, where: str, message: str):
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        cls.had_error = True


if __name__ == "__main__":
    Lox.main()