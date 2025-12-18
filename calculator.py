#!/usr/bin/env python3
import argparse
import sys


def add(a: float, b: float) -> float:
    return a + b


def sub(a: float, b: float) -> float:
    return a - b


def mul(a: float, b: float) -> float:
    return a * b


def div(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


OPS = {"add": add, "sub": sub, "mul": mul, "div": div}


def interactive() -> None:
    print("Simple calculator (interactive mode). Type 'q' to quit.")
    while True:
        try:
            op = input("Operation [add/sub/mul/div or q]: ").strip().lower()
        except EOFError:
            print("\n(no input; exiting)")
            break
        if op in {"q", "quit", "exit"}:
            break
        if op not in OPS:
            print("Unsupported operation. Try again.")
            continue
        try:
            a = float(input("First number: ").strip())
            b = float(input("Second number: ").strip())
            result = OPS[op](a, b)
            print(f"Result: {result}")
        except ValueError as exc:
            print(f"Error: {exc}")
        print("-" * 30)


def main() -> None:
    # If no arguments, fall back to interactive mode (helps when double-clicked)
    if len(sys.argv) == 1:
        interactive()
        input("Press Enter to close...")
        return

    parser = argparse.ArgumentParser(description="Simple CLI calculator")
    parser.add_argument("operation", choices=list(OPS.keys()), help="Operation to perform")
    parser.add_argument("x", type=float, help="First operand")
    parser.add_argument("y", type=float, help="Second operand")
    args = parser.parse_args()
    try:
        result = OPS[args.operation](args.x, args.y)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    print(result)


if __name__ == "__main__":
    main()
