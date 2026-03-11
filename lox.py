import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lox.py [script.lox]")
        return

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        source = f.read()

    print(source)

if __name__ == "__main__":
    main()