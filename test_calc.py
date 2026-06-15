"""Tests for calculator — intentionally incomplete."""
import pytest
import subprocess
import sys
from calc import add, subtract, multiply, divide, calculate, load_history, save_history, memory_clear

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_multiply():
    assert multiply(4, 3) == 12

# Bug: no test for divide
# Bug: no test for power
# Bug: no test for parse_args
# Bug: no test for memory functions
# Bug: no test for history
# Bug: no test for format_result

def test_calculate_add():
    assert calculate("add", 2, 3) == 5


# --- B1: Division by zero ---

def test_divide_by_zero_raises_value_error():
    """divide() must raise ValueError, not ZeroDivisionError, when b == 0."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

def test_divide_by_zero_float_raises_value_error():
    """divide() must catch float 0.0 as well as integer 0."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0.0)

def test_calculate_div_by_zero_raises_value_error():
    """calculate('div', ...) must propagate the ValueError from divide()."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculate("div", 10, 0)

def test_divide_by_zero_cli_friendly_message(tmp_path, monkeypatch, capsys):
    """CLI must print a friendly error message, not a traceback, on div-by-zero."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "div", "10", "0"],
        capture_output=True, text=True
    )
    assert result.returncode != 0, "Process must exit non-zero on division by zero"
    assert "Error" in result.stdout or "Error" in result.stderr, (
        "A user-friendly error message must appear"
    )
    assert "Traceback" not in result.stderr, "Raw traceback must not reach the user"
    assert "ZeroDivisionError" not in result.stderr, "ZeroDivisionError must not be exposed"

def test_divide_by_zero_no_history_entry(tmp_path, monkeypatch):
    """A failed division must NOT append a record to history."""
    monkeypatch.chdir(tmp_path)
    # Start with a clean history
    save_history([])
    # Attempt the failing division via CLI so parse_args path is exercised
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "div", "10", "0"],
        capture_output=True, text=True
    )
    history = load_history()
    assert history == [], (
        "History must remain empty after a failed division by zero"
    )

def test_divide_normal_still_works():
    """Sanity check: divide() still works for valid, non-zero denominators."""
    assert divide(10, 2) == 5.0
    assert divide(7, 2) == 3.5
    assert divide(-6, 3) == -2.0


# --- B2: Unknown operation raises ValueError ---

def test_calculate_unknown_op_raises_value_error():
    """calculate() must raise ValueError with a descriptive message for unknown ops."""
    with pytest.raises(ValueError, match="Unknown operation: modulo"):
        calculate("modulo", 10, 3)

def test_calculate_typo_op_raises_value_error():
    """calculate() must raise ValueError for typos like 'aad'."""
    with pytest.raises(ValueError, match="Unknown operation: aad"):
        calculate("aad", 1, 2)

def test_calculate_empty_op_raises_value_error():
    """calculate() must raise ValueError for an empty string op."""
    with pytest.raises(ValueError, match="Unknown operation: "):
        calculate("", 1, 2)

def test_calculate_unknown_op_not_key_error():
    """calculate() must NOT raise KeyError — it must raise ValueError instead."""
    try:
        calculate("sqrt", 9, 0)
    except KeyError:
        pytest.fail("calculate() raised KeyError; expected ValueError for unknown op")
    except ValueError:
        pass  # correct behaviour

def test_calculate_unknown_op_cli_friendly_message(tmp_path, monkeypatch):
    """CLI must print a friendly error and exit non-zero for an unknown operation."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "modulo", "10", "3"],
        capture_output=True, text=True
    )
    assert result.returncode != 0, "Process must exit non-zero for unknown operation"
    assert "Error" in result.stdout or "Error" in result.stderr, (
        "A user-friendly error message must appear for unknown op"
    )
    assert "Traceback" not in result.stderr, "Raw traceback must not reach the user"
    assert "KeyError" not in result.stderr, "KeyError must not be exposed to the user"
    assert "modulo" in result.stdout or "modulo" in result.stderr, (
        "The unknown op name should appear in the error message"
    )

def test_calculate_unknown_op_no_history_entry(tmp_path, monkeypatch):
    """A failed unknown-op call must NOT append a record to history."""
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "modulo", "10", "3"],
        capture_output=True, text=True
    )
    history = load_history()
    assert history == [], (
        "History must remain empty after an unknown-operation error"
    )

def test_valid_ops_unaffected_by_guard():
    """All existing valid ops must continue working correctly after the fix."""
    assert calculate("add", 2, 3) == 5
    assert calculate("sub", 10, 4) == 6
    assert calculate("mul", 3, 7) == 21
    assert calculate("div", 15, 3) == 5.0
    assert calculate("pow", 2, 8) == 256.0
