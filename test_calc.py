"""Tests for calculator — comprehensive coverage of all paths."""
import pytest
import subprocess
import sys
from calc import (
    add, subtract, multiply, divide, power,
    calculate,
    format_result,
    load_history, save_history,
    memory_store, memory_recall, memory_clear,
    parse_args, print_usage,
)


# ---------------------------------------------------------------------------
# Autouse fixture: reset global memory state between every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_memory():
    """Reset the module-level memory dict before each test to prevent leakage."""
    memory_clear()
    yield
    memory_clear()


# ---------------------------------------------------------------------------
# 1. Arithmetic unit tests — pure functions
# ---------------------------------------------------------------------------

def test_add():
    assert add(2, 3) == 5

def test_add_floats():
    assert add(1.5, 2.5) == 4.0

def test_add_negative():
    assert add(-4, 6) == 2

def test_subtract():
    assert subtract(5, 3) == 2

def test_subtract_floats():
    assert subtract(10.5, 0.5) == 10.0

def test_subtract_negative():
    assert subtract(-4, -6) == 2

def test_multiply():
    assert multiply(4, 3) == 12

def test_multiply_floats():
    assert multiply(2.5, 4.0) == 10.0

def test_multiply_negative():
    assert multiply(-3, 5) == -15

def test_multiply_by_zero():
    assert multiply(99, 0) == 0

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_floats():
    assert divide(7.5, 2.5) == 3.0

def test_divide_negative():
    assert divide(-6, 3) == -2.0

def test_divide_result_is_float():
    assert divide(7, 2) == 3.5

def test_divide_by_zero_raises_value_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

def test_divide_by_zero_float_raises_value_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0.0)

def test_power_integer_exponent():
    assert power(2, 8) == 256.0

def test_power_zero_exponent():
    assert power(5, 0) == 1.0

def test_power_one_exponent():
    assert power(7, 1) == 7.0

def test_power_float_base():
    assert power(4.0, 0.5) == pytest.approx(2.0)

def test_power_negative_exponent():
    assert power(2, -1) == pytest.approx(0.5)

def test_power_negative_base():
    assert power(-2, 3) == -8.0


# ---------------------------------------------------------------------------
# 2. calculate() dispatch
# ---------------------------------------------------------------------------

def test_calculate_add():
    assert calculate("add", 2, 3) == 5

def test_calculate_sub():
    assert calculate("sub", 10, 4) == 6

def test_calculate_mul():
    assert calculate("mul", 3, 7) == 21

def test_calculate_div():
    assert calculate("div", 15, 3) == 5.0

def test_calculate_pow():
    assert calculate("pow", 2, 8) == 256.0

def test_calculate_div_by_zero_raises_value_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculate("div", 10, 0)

def test_calculate_unknown_op_raises_value_error():
    with pytest.raises(ValueError, match="Unknown operation: modulo"):
        calculate("modulo", 10, 3)

def test_calculate_typo_op_raises_value_error():
    with pytest.raises(ValueError, match="Unknown operation: aad"):
        calculate("aad", 1, 2)

def test_calculate_empty_op_raises_value_error():
    with pytest.raises(ValueError, match="Unknown operation: "):
        calculate("", 1, 2)

def test_calculate_unknown_op_not_key_error():
    try:
        calculate("sqrt", 9, 0)
    except KeyError:
        pytest.fail("calculate() raised KeyError; expected ValueError for unknown op")
    except ValueError:
        pass

def test_valid_ops_unaffected_by_guard():
    assert calculate("add", 2, 3) == 5
    assert calculate("sub", 10, 4) == 6
    assert calculate("mul", 3, 7) == 21
    assert calculate("div", 15, 3) == 5.0
    assert calculate("pow", 2, 8) == 256.0


# ---------------------------------------------------------------------------
# 3. format_result tests
# ---------------------------------------------------------------------------

def test_format_result_integer_float():
    assert format_result(5.0) == "5.0"

def test_format_result_negative():
    assert format_result(-3.0) == "-3.0"

def test_format_result_zero():
    assert format_result(0.0) == "0.0"

def test_format_result_returns_string():
    assert isinstance(format_result(42.0), str)

def test_format_result_large_number():
    assert format_result(1000000.0) == "1000000.0"


# ---------------------------------------------------------------------------
# 4. Memory unit tests
# ---------------------------------------------------------------------------

def test_memory_default_is_zero():
    assert memory_recall() == 0

def test_memory_store_then_recall():
    memory_store(42)
    assert memory_recall() == 42

def test_memory_store_float():
    memory_store(3.14)
    assert memory_recall() == pytest.approx(3.14)

def test_memory_store_negative():
    memory_store(-99)
    assert memory_recall() == -99

def test_memory_clear_resets_to_zero():
    memory_store(100)
    memory_clear()
    assert memory_recall() == 0

def test_memory_store_overwrites_previous():
    memory_store(10)
    memory_store(20)
    assert memory_recall() == 20

def test_memory_clear_idempotent():
    memory_clear()
    memory_clear()
    assert memory_recall() == 0


# ---------------------------------------------------------------------------
# 5. History integration tests
# ---------------------------------------------------------------------------

def test_load_history_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_history() == []

def test_save_and_load_history_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = [{"op": "add", "a": 1.0, "b": 2.0, "result": 3.0}]
    save_history(data)
    assert load_history() == data

def test_successful_calculation_appends_one_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "add", "2", "3"])
    history = load_history()
    assert len(history) == 1
    assert history[0] == {"op": "add", "a": 2.0, "b": 3.0, "result": 5.0}

def test_multiple_calculations_append_multiple_records(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "add", "1", "2"])
    parse_args(["calc", "mul", "3", "4"])
    history = load_history()
    assert len(history) == 2
    assert history[0]["op"] == "add"
    assert history[1]["op"] == "mul"

def test_history_record_schema(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "sub", "10", "4"])
    record = load_history()[0]
    assert set(record.keys()) == {"op", "a", "b", "result"}
    assert isinstance(record["op"], str)
    assert isinstance(record["a"], float)
    assert isinstance(record["b"], float)
    assert isinstance(record["result"], float)

def test_clear_command_empties_history(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_history([{"op": "add", "a": 1.0, "b": 2.0, "result": 3.0}])
    parse_args(["calc", "clear"])
    assert load_history() == []

def test_divide_by_zero_no_history_entry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "div", "10", "0"],
        capture_output=True, text=True
    )
    assert load_history() == []

def test_unknown_op_no_history_entry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "modulo", "10", "3"],
        capture_output=True, text=True
    )
    assert load_history() == []

def test_non_numeric_no_history_entry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "add", "foo", "3"],
        capture_output=True, text=True
    )
    assert load_history() == []


# ---------------------------------------------------------------------------
# 6. parse_args in-process CLI integration tests
# ---------------------------------------------------------------------------

def test_no_args_shows_usage(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc"])
    captured = capsys.readouterr()
    assert result is None
    assert "Usage" in captured.out

def test_only_op_no_operands_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc", "add"])
    captured = capsys.readouterr()
    assert result is None
    assert "Error" in captured.out

def test_op_and_one_operand_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc", "add", "5"])
    captured = capsys.readouterr()
    assert result is None
    assert "Error" in captured.out

def test_help_flag_shows_usage(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc", "--help"])
    captured = capsys.readouterr()
    assert result is None
    assert "Usage" in captured.out

def test_help_command_shows_usage(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc", "help"])
    captured = capsys.readouterr()
    assert result is None
    assert "Usage" in captured.out

def test_history_command_returns_none(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc", "history"])
    assert result is None

def test_history_command_prints_output(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    save_history([{"op": "add", "a": 1.0, "b": 2.0, "result": 3.0}])
    parse_args(["calc", "history"])
    captured = capsys.readouterr()
    assert captured.out.strip() != ""

def test_clear_command_prints_confirmation(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "clear"])
    captured = capsys.readouterr()
    assert "cleared" in captured.out.lower() or "History" in captured.out

def test_mem_no_subcmd_prints_memory(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    memory_store(7)
    result = parse_args(["calc", "mem"])
    captured = capsys.readouterr()
    assert result is None
    assert "7" in captured.out

def test_mem_recall_prints_value(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    memory_store(55)
    parse_args(["calc", "mem", "recall"])
    captured = capsys.readouterr()
    assert "55" in captured.out

def test_mem_clear_resets_memory(tmp_path, monkeypatch):
    memory_store(99)
    parse_args(["calc", "mem", "clear"])
    assert memory_recall() == 0

def test_mem_store_stores_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "42"])
    assert memory_recall() == 42.0

def test_mem_store_prints_confirmation(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "42"])
    captured = capsys.readouterr()
    assert "Stored" in captured.out or "42" in captured.out

def test_parse_args_arithmetic_returns_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = parse_args(["calc", "add", "10", "5"])
    assert result == 15.0

def test_parse_args_arithmetic_prints_result(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mul", "6", "7"])
    captured = capsys.readouterr()
    assert "42" in captured.out

def test_parse_args_sub(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert parse_args(["calc", "sub", "10", "3"]) == 7.0

def test_parse_args_div(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert parse_args(["calc", "div", "20", "4"]) == 5.0

def test_parse_args_pow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert parse_args(["calc", "pow", "2", "10"]) == 1024.0


# ---------------------------------------------------------------------------
# 7. CLI subprocess tests (exit code assertions)
# ---------------------------------------------------------------------------

def test_divide_by_zero_cli_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "div", "10", "0"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_divide_by_zero_cli_friendly_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "div", "10", "0"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ZeroDivisionError" not in result.stderr

def test_unknown_op_cli_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "modulo", "10", "3"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_unknown_op_cli_friendly_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "modulo", "10", "3"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "KeyError" not in result.stderr
    assert "modulo" in result.stdout or "modulo" in result.stderr

def test_non_numeric_first_arg_cli_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "add", "foo", "3"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_non_numeric_first_arg_cli_friendly_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "add", "foo", "3"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ValueError" not in result.stderr
    assert "foo" in result.stdout or "foo" in result.stderr

def test_non_numeric_second_arg_cli_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "add", "3", "bar"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_non_numeric_second_arg_cli_friendly_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "add", "3", "bar"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "bar" in result.stdout or "bar" in result.stderr

def test_both_args_non_numeric(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mul", "abc", "xyz"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr

def test_mem_store_missing_value_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_mem_store_missing_value_friendly_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "IndexError" not in result.stderr

def test_mem_store_non_numeric_value_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "notanumber"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_mem_store_non_numeric_value_friendly_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "notanumber"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ValueError" not in result.stderr

def test_mem_store_valid_value_still_works(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "42"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Stored" in result.stdout


# ---------------------------------------------------------------------------
# 8. print_usage coverage
# ---------------------------------------------------------------------------

def test_print_usage_outputs_usage(capsys):
    print_usage()
    captured = capsys.readouterr()
    assert "Usage" in captured.out

def test_print_usage_mentions_operations(capsys):
    print_usage()
    captured = capsys.readouterr()
    assert any(op in captured.out for op in ["add", "sub", "mul", "div", "pow"])
