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
# Bug: no test for calculate with invalid op
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
