#!/usr/bin/env python3
"""Simple calculator CLI with history and memory."""
import sys
import json
import os
import tempfile
import threading
from collections.abc import Callable

HISTORY_FILE = "calc_history.json"

# Type alias for a single history record: op is str, a/b/result are float.
HistoryRecord = dict[str, float | str]


def load_history() -> list[HistoryRecord]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            try:
                data: list[HistoryRecord] = json.load(f)
                return data
            except json.JSONDecodeError:
                print(f"Warning: history file is corrupt; starting fresh.", file=sys.stderr)
                return []
    return []

def save_history(history: list[HistoryRecord]) -> None:
    dir_name = os.path.dirname(os.path.abspath(HISTORY_FILE))
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, suffix=".tmp") as tmp:
        json.dump(history, tmp)
        tmp_path = tmp.name
    os.replace(tmp_path, HISTORY_FILE)

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

def multiply(a: float, b: float) -> float:
    return a * b

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return float(a / b)

def power(a: float, b: float) -> float:
    return a ** b

def calculate(op: str, a: float, b: float) -> float:
    ops: dict[str, Callable[[float, float], float]] = {
        "add": add,
        "sub": subtract,
        "mul": multiply,
        "div": divide,
        "pow": power,
    }
    func = ops.get(op)
    if func is None:
        raise ValueError(f"Unknown operation: {op}")
    return func(a, b)

def format_result(result: float) -> str:
    # Use :.10g to suppress IEEE 754 floating-point noise while preserving
    # meaningful precision. Trailing zeros and unnecessary ".0" suffixes are
    # dropped automatically; scientific notation kicks in for very large/small
    # numbers. 10 significant figures is sufficient for all practical inputs.
    return f"{result:.10g}"

# Memory feature: protected by a threading.Lock so concurrent reads/writes
# are serialised and cannot produce race conditions (fixes B4).
memory: dict[str, float] = {"value": 0}
_memory_lock = threading.Lock()

def memory_store(value: float) -> None:
    with _memory_lock:
        memory["value"] = value

def memory_recall() -> float:
    with _memory_lock:
        return memory["value"]

def memory_clear() -> None:
    with _memory_lock:
        memory["value"] = 0

def parse_args(args: list[str]) -> float | None:
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
    entry: HistoryRecord = {"op": op, "a": a, "b": b, "result": result}
    history = load_history()
    history.append(entry)
    save_history(history)

    print(format_result(result))
    return result

def print_usage() -> None:
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

def main() -> None:
    parse_args(sys.argv)

if __name__ == "__main__":
    main()
