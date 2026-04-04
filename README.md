# Lox Tree-Walk Interpreter
CPSC 323 - Compilers and Languages

A fully functional Tree-Walk Interpreter for the Lox language, built in Python
following Chapters 4-10 of Crafting Interpreters by Robert Nystrom.

---

## Project Structure

| File | Purpose |
|---|---|
| `lox.py` | Entry point — wires Scanner, Parser, and Interpreter together |
| `scanner.py` | Lexer — turns raw source text into a list of tokens |
| `token.py` | Token data class |
| `token_type.py` | Enum of every token type |
| `expr.py` | Expression AST node definitions |
| `stmt.py` | Statement AST node definitions |
| `parser.py` | Recursive descent parser — builds AST from tokens |
| `interpreter.py` | Tree-walk interpreter — executes the AST |
| `environment.py` | Variable storage and scope chain management |
| `runtime_error.py` | Custom exception for Lox runtime errors |
| `lox_callable.py` | Abstract interface for callable Lox values |
| `lox_function.py` | Lox function implementation and return handling |

---

## Requirements

- Python 3.10 or higher (required for the `match` statement in scanner.py)

Check your version with:
```
python3 --version
```

---

## How to Run

### Run a Lox script file
```
python3 lox.py yourfile.lox
```

### Run the interactive REPL
```
python3 lox.py
```
Type Lox code line by line. Exit with `Ctrl+C` or `Ctrl+D`.

---

## What Lox Supports

### Variables
```
var x = 10;
var name = "Lox";
print x;
print name;
```

### Arithmetic and String Operations
```
print 10 + 5;
print 10 / 4;
print "Hello, " + "world!";
```

### Control Flow
```
if (x > 5) {
    print "big";
} else {
    print "small";
}
```

### Loops
```
var i = 0;
while (i < 3) {
    print i;
    i = i + 1;
}

for (var j = 0; j < 3; j = j + 1) {
    print j;
}
```

### Scoping and Shadowing
```
var x = 1;
{
    var x = 99;  // shadows outer x, does NOT overwrite it
    print x;     // prints 99
}
print x;         // prints 1
```

### Functions and Recursion
```
fun factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
print factorial(5);  // 120
```

### Closures
```
fun makeCounter() {
    var count = 0;
    fun increment() {
        count = count + 1;
        return count;
    }
    return increment;
}
var counter = makeCounter();
print counter();  // 1
print counter();  // 2
```

---

## Error Reporting

All errors include the line number where they occurred.

**Scan error** — unrecognized character:
```
[line 3] Error: Unexpected character '@'.
```

**Parse error** — missing semicolon, bad syntax:
```
[line 5] Error at 'var': Expect ';' after expression.
```

**Runtime error** — division by zero, undefined variable:
```
[line 7] RuntimeError: Undefined variable 'x'.
[line 9] RuntimeError: Division by zero.
```

---

## Attribution

All core design patterns and algorithms follow:
**Crafting Interpreters** by Robert Nystrom
Free online at: https://craftinginterpreters.com

Implemented in Python with AI assistance (Claude by Anthropic).
All code reviewed, understood, and attributed per course policy.