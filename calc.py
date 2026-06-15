#!/usr/bin/env python3
"""Simple calculator CLI with history and memory."""
import sys
import json
import os

HISTORY_FILE = "calc_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def power(a, b):
    return a ** b

def calculate(op, a, b):
    ops = {
        "add": add,
        "sub": subtract,
        "mul": multiply,
        "div": divide,
        "pow": power,
    }
    # Bug: no validation of op
    func = ops[op]
    result = func(a, b)
    return result

def format_result(result):
    # Bug: doesn't handle float precision (0.1 + 0.2 = 0.30000000000000004)
    return str(result)

# Bug: memory feature stores in global mutable state with no thread safety
memory = {"value": 0}

def memory_store(value):
    memory["value"] = value

def memory_recall():
    return memory["value"]

def memory_clear():
    memory["value"] = 0

def parse_args(args):
    if len(args) < 2:
        print_usage()
        return None

    cmd = args[1]

    if cmd == "help" or cmd == "--help":
        print_usage()
        return None

    if cmd == "history":
        history = load_history()
        # Bug: prints raw list, not formatted
        print(history)
        return None

    if cmd == "clear":
        save_history([])
        print("History cleared")
        return None

    if cmd == "mem":
        if len(args) < 3:
            print(f"Memory: {memory_recall()}")
            return None
        subcmd = args[2]
        if subcmd == "store":
            # Bug: no validation of args[3]
            memory_store(float(args[3]))
            print(f"Stored: {args[3]}")
        elif subcmd == "recall":
            print(f"Memory: {memory_recall()}")
        elif subcmd == "clear":
            memory_clear()
            print("Memory cleared")
        return None

    # Main calculation: calc <op> <a> <b>
    if len(args) < 4:
        print("Error: need operation and two numbers")
        print("Usage: calc <add|sub|mul|div|pow> <num1> <num2>")
        return None

    op = args[1]
    # Bug: no validation that a and b are numbers
    a = float(args[2])
    b = float(args[3])

    try:
        result = calculate(op, a, b)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save to history — only reached on success
    entry = {"op": op, "a": a, "b": b, "result": result}
    history = load_history()
    history.append(entry)
    save_history(history)

    print(format_result(result))
    return result

def print_usage():
    # Bug: usage text is incomplete, missing mem and clear commands
    print("Usage: calc <operation> <num1> <num2>")
    print("Operations: add, sub, mul, div, pow")

def main():
    parse_args(sys.argv)

if __name__ == "__main__":
    main()
