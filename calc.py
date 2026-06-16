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
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, suffix=".tmp") as tmp:
            tmp_path = tmp.name
            json.dump(history, tmp)
        os.replace(tmp_path, HISTORY_FILE)
    except Exception:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

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


def percentage(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot calculate percentage: denominator is zero")
    return (a / b) * 100
def calculate(op: str, a: float, b: float) -> float:
    ops: dict[str, Callable[[float, float], float]] = {
        "add": add,
        "sub": subtract,
        "mul": multiply,
        "div": divide,
        "pow": power,
        "pct": percentage,
    }
    func = ops.get(op)
    if func is None:
        raise ValueError(f"Unknown operation: {op}")
    return func(a, b)

def format_result(result: float) -> str:
    # Format choice (Option A — deliberately chosen, Issue #29):
    #
    # We use :.10g, which means:
    #   - Up to 10 significant figures of precision (sufficient for all practical inputs).
    #   - Trailing zeros are stripped: 5.0 → "5", 256.0 → "256".
    #   - The ".0" suffix is intentionally omitted for whole-number results.
    #     README examples and docs must reflect this (e.g. "# → 5", not "# → 5.0").
    #   - IEEE 754 floating-point noise is suppressed: 0.1 + 0.2 → "0.3" (not "0.30000000000000004").
    #   - Scientific notation engages automatically for very large/small values
    #     (e.g. 1e-10, 1e15), which is appropriate for a CLI calculator.
    #
    # Do NOT change this to :.10f or str() — both would reintroduce noise or
    # always show trailing zeros, breaking the noise-suppression guarantee.
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
        if not history:
            print("No history.")
        else:
            for i, r in enumerate(history, 1):
                print(f"  {i}. {r['op']} {r['a']} {r['b']} = {r['result']}")
        return None

    if cmd == "clear":
        try:
            save_history([])
        except (TypeError, OSError) as e:
            print(f"Error: Could not save history: {e}", file=sys.stderr)
            sys.exit(1)
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
        else:
            print(f"Error: Unknown mem subcommand: '{subcmd}'")
            sys.exit(1)
        return None

    # Main calculation: calc <op> <a> <b>
    if len(args) < 4:
        print("Error: need operation and two numbers")
        print("Usage: calc <add|sub|mul|div|pow|pct> <num1> <num2>")
        sys.exit(1)

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
    try:
        save_history(history)
    except (TypeError, OSError) as e:
        print(f"Error: Could not save history: {e}", file=sys.stderr)
        sys.exit(1)

    print(format_result(result))
    return result

def print_usage() -> None:
    print("Usage: calc <command> [arguments]")
    print("")
    print("Arithmetic:")
    print("  calc <add|sub|mul|div|pow|pct> <num1> <num2>")
    print("  calc pct <num1> <num2>       What percent num1 is of num2")
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
