#!/usr/bin/env python3
"""Simple calculator CLI with history and memory."""
import sys
import json
import os
import stat
import tempfile
import threading
from collections.abc import Callable

HISTORY_FILE = "calc_history.json"
MEMORY_FILE = "calc_memory.json"
MAX_HISTORY = 1000

# Type alias for a single history record: op is str, a/b/result are float.
HistoryRecord = dict[str, float | str]


def load_history() -> list[HistoryRecord]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            try:
                data: list[HistoryRecord] = json.load(f)
                return data
            except json.JSONDecodeError:
                print("Warning: history file is corrupt; starting fresh.", file=sys.stderr)
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
    except (OSError, TypeError) as e:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        print(f"Warning: could not save history: {e}", file=sys.stderr)
        raise

def load_memory() -> float:
    """Load the persisted memory value from MEMORY_FILE.

    Returns 0.0 if the file does not exist or is corrupt.
    """
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            try:
                data = json.load(f)
                return float(data.get("value", 0.0))
            except (json.JSONDecodeError, TypeError, ValueError):
                print("Warning: memory file is corrupt; resetting to 0.", file=sys.stderr)
                return 0.0
    return 0.0

def save_memory(value: float) -> None:
    """Persist the memory value to MEMORY_FILE atomically with 0600 permissions."""
    dir_name = os.path.dirname(os.path.abspath(MEMORY_FILE))
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=dir_name, delete=False, suffix=".tmp"
        ) as tmp:
            tmp_path = tmp.name
            json.dump({"value": value}, tmp)
        # Enforce 0600 (owner read/write only) before moving into place
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, MEMORY_FILE)
    except (OSError, TypeError) as e:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        print(f"Warning: could not save memory: {e}", file=sys.stderr)
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
    try:
        result = a ** b
    except OverflowError:
        raise ValueError(
            f"Result of {a} ** {b} is too large to represent as a finite number"
        )
    if isinstance(result, complex):
        raise ValueError(
            "Result is a complex number and cannot be displayed "
            "(try a non-negative base)"
        )
    return result


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

def format_result(result: int | float) -> str:
    # Format choice (Option A -- deliberately chosen, Issue #29):
    #
    # We use :.10g, which means:
    #   - Up to 10 significant figures of precision (sufficient for all practical inputs).
    #   - Trailing zeros are stripped: 5.0 -> "5", 256.0 -> "256".
    #   - The ".0" suffix is intentionally omitted for whole-number results.
    #     README examples and docs must reflect this (e.g. "# -> 5", not "# -> 5.0").
    #   - IEEE 754 floating-point noise is suppressed: 0.1 + 0.2 -> "0.3" (not "0.30000000000000004").
    #   - Scientific notation engages automatically for very large/small values
    #     (e.g. 1e-10, 1e15), which is appropriate for a CLI calculator.
    #
    # Do NOT change this to :.10f or str() -- both would reintroduce noise or
    # always show trailing zeros, breaking the noise-suppression guarantee.
    import math
    if isinstance(result, complex):
        raise TypeError(
            f"format_result() does not accept complex numbers; got {result!r}"
        )
    try:
        result = float(result)
    except OverflowError:
        raise ValueError("Result too large to represent as a finite float")
    if not math.isfinite(result):
        raise ValueError(
            f"format_result() requires a finite float; got {result!r} (nan or inf is not allowed)"
        )
    return f"{result:.10g}"

# Memory feature: protected by a threading.Lock so concurrent reads/writes
# are serialised and cannot produce race conditions (fixes B4).
# Memory is persisted to MEMORY_FILE (calc_memory.json) across invocations --
# analogous to history persistence in calc_history.json (Issue #65).
memory: dict[str, float] = {"value": 0}
_memory_lock = threading.Lock()

def memory_store(value: float) -> None:
    """Store value in the in-process memory dict and persist it to MEMORY_FILE."""
    with _memory_lock:
        memory["value"] = value
        try:
            save_memory(value)
        except (OSError, TypeError) as e:
            # Warn but do not crash: in-process state is already updated.
            print(f"Warning: could not persist memory to disk: {e}", file=sys.stderr)

def memory_recall() -> float:
    """Return the current memory value, loading from MEMORY_FILE if present."""
    with _memory_lock:
        # Sync from disk on every recall so that values stored by a previous
        # process invocation are visible.
        disk_value = load_memory()
        memory["value"] = disk_value
        return disk_value

def memory_clear() -> None:
    """Reset memory to 0 in-process and persist the reset to MEMORY_FILE."""
    with _memory_lock:
        memory["value"] = 0
        try:
            save_memory(0.0)
        except (OSError, TypeError) as e:
            print(f"Warning: could not persist memory clear to disk: {e}", file=sys.stderr)

def parse_args(args: list[str]) -> float | None:
    if len(args) < 2:
        print_usage()
        sys.exit(1)

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
            print("Note: memory is persisted to disk (session values are not lost on exit).")
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
    except (ValueError, OverflowError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save to history -- only reached on successful calculation
    try:
        formatted = format_result(result)
    except (TypeError, ValueError, OverflowError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    print(formatted)

    entry: HistoryRecord = {"op": op, "a": a, "b": b, "result": result}
    try:
        history = load_history()
        history.append(entry)
        history = history[-MAX_HISTORY:]
        save_history(history)
    except (TypeError, OSError) as e:
        print(f"Error: Could not save history: {e}", file=sys.stderr)
        sys.exit(1)

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
    print("  calc mem store <num>    Store a value in memory (session-only in-process; persisted to disk across sessions)")
    print("  calc mem recall         Recall the stored memory value (reads from disk)")
    print("  calc mem clear          Reset memory to 0 (persists the reset to disk)")
    print("  calc help               Show this help message")
    print("")
    print("Memory persistence (session values survive restarts):")
    print("  Memory values are saved to calc_memory.json and survive process restarts.")
    print("  Use 'calc mem clear' to explicitly reset the stored value to 0.")

def main() -> None:
    parse_args(sys.argv)

if __name__ == "__main__":  # pragma: no cover
    main()
