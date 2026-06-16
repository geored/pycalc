#!/usr/bin/env python3
"""Simple calculator CLI with history and memory."""
import sys
import json
import os
import tempfile

HISTORY_FILE = "calc_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: history file is corrupt; starting fresh.", file=sys.stderr)
                return []
    return []

def save_history(history: list) -> None:
    dir_name = os.path.dirname(os.path.abspath(HISTORY_FILE))
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, suffix=".tmp") as tmp:
        json.dump(history, tmp)
        tmp_path = tmp.name
    os.replace(tmp_path, HISTORY_FILE)

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
    func = ops.get(op)
    if func is None:
        raise ValueError(f"Unknown operation: {op}")
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
            if len(args) < 4:
                print("Error: 'mem store' requires a numeric value")
                sys.exit(1)
            try:
                value = float(args[3])
            except ValueError:
                print(f"Error: Invalid number: '{args[3]}'")
                sys.exit(1)
            memory_store(value)
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
    try:
        a = float(args[2])
    except ValueError:
        print(f"Error: Invalid number: '{args[2]}'")
        sys.exit(1)
    try:
        b = float(args[3])
    except ValueError:
        print(f"Error: Invalid number: '{args[3]}'")
        sys.exit(1)

    try:
        result = calculate(op, a, b)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save to history -- only reached on successful calculation
    entry = {"op": op, "a": a, "b": b, "result": result}
    history = load_history()
    history.append(entry)
    save_history(history)

    print(format_result(result))
    return result

def print_usage():
    print("Usage: calc <command> [arguments]")
    print("")
    print("Arithmetic:")
    print("  calc <add|sub|mul|div|pow> <num1> <num2>")
    print("")
    print("Commands:")
    print("  calc history            Show calculation history")
    print("  calc clear              Clear calculation history")
    print("  calc mem                Show current memory value")
    print("  calc mem store <num>    Store a value in memory")
    print("  calc mem recall         Recall the stored memory value")
    print("  calc mem clear          Reset memory to 0")
    print("  calc help               Show this help message")

def main():
    parse_args(sys.argv)

if __name__ == "__main__":
    main()
