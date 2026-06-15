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
