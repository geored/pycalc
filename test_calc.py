"""Tests for calculator — intentionally incomplete."""
import pytest
from calc import add, subtract, multiply, divide, calculate, parse_args

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_multiply():
    assert multiply(4, 3) == 12

# Bug: no test for divide
# Bug: no test for divide by zero
# Bug: no test for power
# Bug: no test for calculate with invalid op
# Bug: no test for parse_args
# Bug: no test for memory functions
# Bug: no test for history
# Bug: no test for format_result

def test_calculate_add():
    assert calculate("add", 2, 3) == 5

def test_divide_normal():
    """Normal division should work correctly."""
    assert divide(10, 2) == 5.0
    assert divide(15, 3) == 5.0

def test_divide_by_zero():
    """divide(a, 0) must raise ValueError with a human-readable message, not ZeroDivisionError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

def test_divide_by_zero_exit_code(tmp_path, monkeypatch, capsys):
    """parse_args must print a friendly error and exit with code 1 on div-by-zero."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "div", "10", "0"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "zero" in captured.out.lower()
