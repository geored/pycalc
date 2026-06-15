"""Tests for calculator — intentionally incomplete."""
import pytest
from calc import add, subtract, multiply, divide, calculate

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

import pytest
from calc import divide, calculate, parse_args

def test_divide_by_zero_raises_value_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(5, 0)

def test_divide_by_zero_float():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(5, 0.0)

def test_calculate_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculate("div", 5, 0)

def test_parse_args_divide_by_zero(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "div", "5", "0"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Cannot divide by zero" in captured.out

def test_parse_args_divide_by_zero_not_in_history(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        parse_args(["calc", "div", "5", "0"])
    from calc import load_history
    assert load_history() == []

def test_divide_normal():
    assert divide(10, 2) == 5.0
