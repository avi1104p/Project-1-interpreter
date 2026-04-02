import sys
from scanner import Scanner
from parser  import Parser


class Lox:
    had_error = False

    @classmethod
    def main(cls):
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
        # ── Chapter 4: Scan ───────────────────────────────────────────────────
        scanner = Scanner(source, cls.scan_error)
        tokens  = scanner.scan_tokens()
        if cls.had_error:
            return

        # ── Chapter 6: Parse ──────────────────────────────────────────────────
        parser     = Parser(tokens, cls.parse_error)
        statements = parser.parse()
        if cls.had_error:
            return

        # Temporary: show what we parsed so we can verify Ch 6 works.
        # This will be replaced by the Interpreter in Chapter 7.
        for s in statements:
            print(s)

    # ── Error reporters ───────────────────────────────────────────────────────

    @classmethod
    def scan_error(cls, line: int, message: str):
        cls._report(line, "", message)

    @classmethod
    def parse_error(cls, token, message: str):
        cls._report(token.line, message, "")

    @classmethod
    def _report(cls, line: int, where: str, message: str):
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        cls.had_error = True


if __name__ == "__main__":
    Lox.main()