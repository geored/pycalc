"""Tests for calculator — comprehensive coverage of all paths."""
import pytest
import subprocess
import sys
import os
import json
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
    assert format_result(5.0) == "5"

def test_format_result_negative():
    assert format_result(-3.0) == "-3"

def test_format_result_zero():
    assert format_result(0.0) == "0"

def test_format_result_returns_string():
    assert isinstance(format_result(42.0), str)

def test_format_result_large_number():
    assert format_result(1000000.0) == "1000000"

def test_format_result_float_precision():
    """0.1 + 0.2 must not produce floating-point noise."""
    assert format_result(0.1 + 0.2) == "0.3"

def test_format_result_one_third():
    """1/3 should be rounded to 10 significant figures."""
    assert format_result(1 / 3) == "0.3333333333"

def test_format_result_power_of_two():
    """Whole-number results must have no trailing .0."""
    assert format_result(256.0) == "256"


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
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "add"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out

def test_op_and_one_operand_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "add", "5"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
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
    """History output must be human-readable numbered lines, not raw Python repr."""
    monkeypatch.chdir(tmp_path)
    save_history([{"op": "add", "a": 1.0, "b": 2.0, "result": 3.0}])
    parse_args(["calc", "history"])
    captured = capsys.readouterr()
    # Must contain the formatted separator and identifiable fields
    assert "=" in captured.out, "Expected '=' in history output (formatted record)"
    assert "add" in captured.out, "Expected op name 'add' in history output"
    assert "3" in captured.out, "Expected result '3' in history output"
    # Must NOT look like a raw Python list repr
    assert "[{" not in captured.out, "History output must not be a raw Python list repr"


def test_history_command_empty_prints_no_history(tmp_path, monkeypatch, capsys):
    """When history is empty, 'calc history' must print 'No history.'."""
    monkeypatch.chdir(tmp_path)
    # Ensure no history file exists
    parse_args(["calc", "history"])
    captured = capsys.readouterr()
    assert "No history." in captured.out, (
        f"Expected 'No history.' but got: {captured.out!r}"
    )

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


# ---------------------------------------------------------------------------
# 9. Corrupt history file — graceful recovery (Issue #5)
# ---------------------------------------------------------------------------

def test_load_history_corrupt_file(tmp_path, monkeypatch):
    """load_history() returns [] gracefully when the history file is corrupt."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "calc_history.json").write_text("this is not valid json{{{{")
    result = load_history()
    assert result == []

def test_load_history_empty_file(tmp_path, monkeypatch):
    """load_history() returns [] gracefully when the history file is empty."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "calc_history.json").write_text("")
    result = load_history()
    assert result == []

def test_load_history_partial_json(tmp_path, monkeypatch):
    """load_history() returns [] when the history file is truncated mid-write."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "calc_history.json").write_text('[{"op": "add"')
    result = load_history()
    assert result == []

def test_load_history_corrupt_emits_warning_to_stderr(tmp_path, monkeypatch, capsys):
    """load_history() emits a warning to stderr when the history file is corrupt."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "calc_history.json").write_text("not json at all")
    load_history()
    captured = capsys.readouterr()
    assert "Warning" in captured.err or "corrupt" in captured.err

def test_load_history_corrupt_does_not_crash_program(tmp_path, monkeypatch):
    """A corrupt history file must not raise any exception."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "calc_history.json").write_text("{bad json}")
    try:
        result = load_history()
    except Exception as e:
        pytest.fail(f"load_history() raised {type(e).__name__} on corrupt file: {e}")
    assert result == []


# ---------------------------------------------------------------------------
# 10. print_usage — complete command coverage (Issue #11)
# ---------------------------------------------------------------------------

def test_print_usage_contains_history(capsys):
    """print_usage() must document the 'history' command."""
    print_usage()
    captured = capsys.readouterr()
    assert "history" in captured.out

def test_print_usage_contains_clear(capsys):
    """print_usage() must document the 'clear' command."""
    print_usage()
    captured = capsys.readouterr()
    assert "clear" in captured.out

def test_print_usage_contains_mem_store(capsys):
    """print_usage() must document the 'mem store' sub-command."""
    print_usage()
    captured = capsys.readouterr()
    assert "mem store" in captured.out

def test_print_usage_contains_mem_recall(capsys):
    """print_usage() must document the 'mem recall' sub-command."""
    print_usage()
    captured = capsys.readouterr()
    assert "mem recall" in captured.out

def test_print_usage_contains_mem_clear(capsys):
    """print_usage() must document the 'mem clear' sub-command."""
    print_usage()
    captured = capsys.readouterr()
    assert "mem clear" in captured.out

def test_print_usage_contains_all_required_keywords(capsys):
    """Single omnibus check: help text must include all commands and sub-commands."""
    print_usage()
    captured = capsys.readouterr()
    for keyword in ["history", "clear", "mem store", "mem recall", "mem clear"]:
        assert keyword in captured.out, f"print_usage() output missing keyword: {keyword!r}"


# ---------------------------------------------------------------------------
# 11. mem store edge cases — float, negative, and zero inputs (Issue #4 / B5)
# ---------------------------------------------------------------------------

def test_mem_store_float_value_in_process(tmp_path, monkeypatch):
    """mem store with a float argument stores the correct value."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "3.14"])
    assert memory_recall() == pytest.approx(3.14)


def test_mem_store_float_value_cli_exits_zero(tmp_path, monkeypatch):
    """mem store with a float argument exits with code 0."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "3.14"],
        capture_output=True, text=True
    )
    assert result.returncode == 0


def test_mem_store_float_value_cli_prints_stored(tmp_path, monkeypatch):
    """mem store with a float argument prints confirmation."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "3.14"],
        capture_output=True, text=True
    )
    assert "Stored" in result.stdout
    assert "Traceback" not in result.stderr


def test_mem_store_negative_value_in_process(tmp_path, monkeypatch):
    """mem store with a negative number stores the correct value."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "-5"])
    assert memory_recall() == -5.0


def test_mem_store_negative_value_cli_exits_zero(tmp_path, monkeypatch):
    """mem store with a negative number exits with code 0."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "-5"],
        capture_output=True, text=True
    )
    assert result.returncode == 0


def test_mem_store_negative_value_cli_prints_stored(tmp_path, monkeypatch):
    """mem store with a negative number prints confirmation."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "-5"],
        capture_output=True, text=True
    )
    assert "Stored" in result.stdout
    assert "Traceback" not in result.stderr


def test_mem_store_zero_value_in_process(tmp_path, monkeypatch):
    """mem store with zero stores 0.0 correctly (not confused with falsy check)."""
    monkeypatch.chdir(tmp_path)
    memory_store(99)               # pre-load a non-zero value
    parse_args(["calc", "mem", "store", "0"])
    assert memory_recall() == 0.0


def test_mem_store_zero_value_cli_exits_zero(tmp_path, monkeypatch):
    """mem store with zero exits with code 0."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "0"],
        capture_output=True, text=True
    )
    assert result.returncode == 0


def test_mem_store_zero_value_cli_prints_stored(tmp_path, monkeypatch):
    """mem store with zero prints confirmation containing the value."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "0"],
        capture_output=True, text=True
    )
    assert "Stored" in result.stdout
    assert "Traceback" not in result.stderr


def test_mem_store_missing_value_message_content(tmp_path, monkeypatch):
    """Missing value error message specifically mentions 'mem store'."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "mem store" in combined
    assert "IndexError" not in result.stderr
    assert "Traceback" not in result.stderr


def test_mem_store_non_numeric_message_includes_bad_value(tmp_path, monkeypatch):
    """Non-numeric error message must echo back the bad argument supplied."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "abc"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "abc" in combined
    assert "Traceback" not in result.stderr
    assert "ValueError" not in result.stderr


# ---------------------------------------------------------------------------
# 12. Atomic history write — Issue #6 / B9
# ---------------------------------------------------------------------------

def test_save_history_uses_atomic_replace(tmp_path, monkeypatch):
    """save_history() must call os.replace() to atomically rename the temp file."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    data = [{"op": "add", "a": 1.0, "b": 2.0, "result": 3.0}]
    replace_calls = []
    original_replace = os.replace

    def spy_replace(src, dst):
        replace_calls.append((src, dst))
        return original_replace(src, dst)

    with mock.patch("os.replace", side_effect=spy_replace):
        save_history(data)

    assert len(replace_calls) == 1, (
        "save_history() must call os.replace() exactly once for atomic write; "
        f"got {len(replace_calls)} call(s)"
    )


def test_save_history_temp_file_in_same_dir(tmp_path, monkeypatch):
    """The temp file must be created in the same directory as HISTORY_FILE."""
    import unittest.mock as mock
    import calc as calc_module
    monkeypatch.chdir(tmp_path)
    data = [{"op": "sub", "a": 5.0, "b": 3.0, "result": 2.0}]
    replace_calls = []
    original_replace = os.replace

    def spy_replace(src, dst):
        replace_calls.append((src, dst))
        return original_replace(src, dst)

    with mock.patch("os.replace", side_effect=spy_replace):
        save_history(data)

    assert len(replace_calls) == 1
    tmp_file, target_file = replace_calls[0]
    # Both paths must share the same parent directory
    assert os.path.dirname(os.path.abspath(tmp_file)) == os.path.dirname(
        os.path.abspath(target_file)
    ), (
        "Temp file must be in the same directory as HISTORY_FILE so that "
        "os.replace() is a same-filesystem rename (not a cross-device copy)"
    )


def test_save_history_file_exists_and_valid_json(tmp_path, monkeypatch):
    """After save_history(), HISTORY_FILE must exist and contain valid JSON."""
    monkeypatch.chdir(tmp_path)
    data = [{"op": "mul", "a": 3.0, "b": 4.0, "result": 12.0}]
    save_history(data)
    history_path = tmp_path / "calc_history.json"
    assert history_path.exists(), "HISTORY_FILE was not created by save_history()"
    content = history_path.read_text()
    parsed = json.loads(content)
    assert parsed == data


def test_save_history_no_temp_file_left_behind(tmp_path, monkeypatch):
    """After a successful save_history(), no .tmp file should remain in the dir."""
    monkeypatch.chdir(tmp_path)
    data = [{"op": "pow", "a": 2.0, "b": 8.0, "result": 256.0}]
    save_history(data)
    leftover_tmp = list(tmp_path.glob("*.tmp"))
    assert leftover_tmp == [], (
        f"Leftover temp file(s) found after save_history(): {leftover_tmp}"
    )


def test_save_history_original_preserved_on_json_error(tmp_path, monkeypatch):
    """If json.dump() fails, the original history file must remain intact."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)

    # Seed an existing history file
    original_data = [{"op": "add", "a": 1.0, "b": 1.0, "result": 2.0}]
    save_history(original_data)

    # Now attempt a save with data that will fail during json.dump
    class Unserializable:
        pass

    bad_data = [Unserializable()]
    try:
        save_history(bad_data)
    except (TypeError, Exception):
        pass  # expected

    # Original file must still be intact
    assert load_history() == original_data, (
        "Original history file was corrupted when json.dump() raised an exception"
    )


def test_save_history_no_temp_file_left_behind_on_json_error(tmp_path, monkeypatch):
    """If json.dump() fails, no .tmp file should remain in the directory."""
    monkeypatch.chdir(tmp_path)

    class Unserializable:
        pass

    bad_data = [Unserializable()]
    try:
        save_history(bad_data)
    except (TypeError, Exception):
        pass  # expected — exception must be re-raised

    leftover_tmp = list(tmp_path.glob("*.tmp"))
    assert leftover_tmp == [], (
        f"Orphaned temp file(s) left after failed json.dump(): {leftover_tmp}"
    )


# ---------------------------------------------------------------------------
# 13. Memory thread-safety — Issue #7 / B4
# ---------------------------------------------------------------------------

def test_memory_lock_exists():
    """calc module must expose a _memory_lock threading.Lock instance."""
    import threading
    import calc as calc_module
    assert hasattr(calc_module, "_memory_lock"), (
        "calc module must define a module-level _memory_lock"
    )
    assert isinstance(calc_module._memory_lock, type(threading.Lock())), (
        "_memory_lock must be a threading.Lock instance"
    )


def test_memory_store_acquires_lock(monkeypatch):
    """memory_store() must acquire _memory_lock before writing."""
    import unittest.mock as mock
    import calc as calc_module
    acquired = []
    original_lock = calc_module._memory_lock

    class SpyLock:
        def __enter__(self):
            acquired.append(True)
            return original_lock.__enter__()
        def __exit__(self, *args):
            return original_lock.__exit__(*args)

    monkeypatch.setattr(calc_module, "_memory_lock", SpyLock())
    calc_module.memory_store(99)
    assert len(acquired) == 1, "memory_store() must acquire the lock exactly once"


def test_memory_recall_acquires_lock(monkeypatch):
    """memory_recall() must acquire _memory_lock before reading."""
    import unittest.mock as mock
    import calc as calc_module
    acquired = []
    original_lock = calc_module._memory_lock

    class SpyLock:
        def __enter__(self):
            acquired.append(True)
            return original_lock.__enter__()
        def __exit__(self, *args):
            return original_lock.__exit__(*args)

    monkeypatch.setattr(calc_module, "_memory_lock", SpyLock())
    calc_module.memory_recall()
    assert len(acquired) == 1, "memory_recall() must acquire the lock exactly once"


def test_memory_clear_acquires_lock(monkeypatch):
    """memory_clear() must acquire _memory_lock before writing."""
    import calc as calc_module
    acquired = []
    original_lock = calc_module._memory_lock

    class SpyLock:
        def __enter__(self):
            acquired.append(True)
            return original_lock.__enter__()
        def __exit__(self, *args):
            return original_lock.__exit__(*args)

    monkeypatch.setattr(calc_module, "_memory_lock", SpyLock())
    calc_module.memory_clear()
    assert len(acquired) == 1, "memory_clear() must acquire the lock exactly once"


def test_memory_concurrent_stores_no_corruption():
    """Concurrent memory_store() calls from many threads must not corrupt state."""
    import threading
    THREADS = 50
    ITERS = 200
    errors = []

    def writer(val):
        for _ in range(ITERS):
            memory_store(val)
            seen = memory_recall()
            # Each recall must return a value that was validly stored by some thread
            if seen not in range(THREADS):
                errors.append(seen)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], (
        f"memory_recall() returned invalid value(s) under concurrent access: {errors[:5]}"
    )


def test_memory_store_recall_still_works_after_lock_added():
    """Regression: store/recall round-trip must still work correctly with the lock."""
    memory_store(123)
    assert memory_recall() == 123


def test_memory_clear_still_resets_after_lock_added():
    """Regression: clear must still reset to 0 with the lock in place."""
    memory_store(456)
    memory_clear()
    assert memory_recall() == 0


def test_memory_api_surface_unchanged():
    """The public API (memory_store, memory_recall, memory_clear) must be callable."""
    # Verifies parse_args can still call these by name without modification
    memory_store(7)
    assert memory_recall() == 7
    memory_clear()
    assert memory_recall() == 0


# ---------------------------------------------------------------------------
# 14. mem store — in-process tests with pytest.raises(SystemExit) (Issue #4 / B5)
# ---------------------------------------------------------------------------

def test_mem_store_missing_value(tmp_path, monkeypatch, capsys):
    """'mem store' with no value exits 1 and prints the expected error message."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "mem", "store"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "mem store" in captured.out


def test_mem_store_non_numeric(tmp_path, monkeypatch, capsys):
    """'mem store abc' exits 1 and prints an error that echoes the bad value."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "mem", "store", "abc"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "abc" in captured.out


def test_mem_store_valid(tmp_path, monkeypatch):
    """'mem store 42' stores 42.0 in memory and exits normally (no SystemExit)."""
    monkeypatch.chdir(tmp_path)
    memory_clear()
    parse_args(["calc", "mem", "store", "42"])
    assert memory_recall() == 42.0


# ---------------------------------------------------------------------------
# 15. Percentage operation — pct feature (Issue: add-percentage.md spec)
# ---------------------------------------------------------------------------

def test_pct_normal():
    """25 is 12.5% of 200."""
    from calc import calculate
    assert calculate("pct", 25, 200) == 12.5

def test_pct_fifty_percent():
    """50 is 50.0% of 100."""
    from calc import calculate
    assert calculate("pct", 50, 100) == 50.0

def test_pct_one_hundred_percent():
    """200 is 100.0% of 200."""
    from calc import calculate
    assert calculate("pct", 200, 200) == 100.0

def test_pct_zero_numerator():
    """0 is 0.0% of any non-zero number."""
    from calc import calculate
    assert calculate("pct", 0, 50) == 0.0

def test_pct_zero_denominator_raises_value_error():
    """pct with zero denominator must raise ValueError, not ZeroDivisionError or crash."""
    from calc import calculate
    with pytest.raises(ValueError, match="[Cc]annot|zero"):
        calculate("pct", 25, 0)

def test_pct_in_ops_dict():
    """The 'pct' key must be present in calculate()'s dispatch table."""
    from calc import calculate
    # Should not raise ValueError("Unknown operation: pct")
    try:
        calculate("pct", 10, 100)
    except ValueError as e:
        if "Unknown operation" in str(e):
            pytest.fail(f"'pct' not registered in ops dict: {e}")

def test_pct_cli_basic(tmp_path, monkeypatch):
    """python calc.py pct 25 200 → prints '12.5'"""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pct", "25", "200"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "12.5" in result.stdout

def test_pct_cli_fifty_percent(tmp_path, monkeypatch):
    """python calc.py pct 50 100 → prints '50'"""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pct", "50", "100"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "50" in result.stdout

def test_pct_cli_zero_denominator_exits_nonzero(tmp_path, monkeypatch):
    """python calc.py pct 10 0 → exits non-zero with an error message."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pct", "10", "0"],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_pct_cli_zero_denominator_friendly_message(tmp_path, monkeypatch):
    """python calc.py pct 10 0 → prints a friendly error, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pct", "10", "0"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr

def test_pct_saved_to_history(tmp_path, monkeypatch):
    """A successful pct calculation must be appended to history."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "pct", "25", "200"])
    history = load_history()
    assert len(history) == 1
    assert history[0]["op"] == "pct"
    assert history[0]["a"] == 25.0
    assert history[0]["b"] == 200.0
    assert history[0]["result"] == 12.5

def test_pct_zero_denominator_no_history_entry(tmp_path, monkeypatch):
    """Failed pct (zero denominator) must NOT write a history entry."""
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "pct", "10", "0"],
        capture_output=True, text=True
    )
    assert load_history() == []

def test_help_includes_pct(capsys):
    """print_usage() must mention 'pct' in the help text."""
    print_usage()
    captured = capsys.readouterr()
    assert "pct" in captured.out, (
        "print_usage() does not mention 'pct' operation — update help text"
    )


# ---------------------------------------------------------------------------
# 16. parse_args — missing operands exit non-zero (Issue #31)
# ---------------------------------------------------------------------------

def test_parse_args_missing_both_operands_exits_nonzero():
    result = subprocess.run(["python", "calc.py", "add"], capture_output=True, cwd="/workspace")
    assert result.returncode != 0

def test_parse_args_missing_one_operand_exits_nonzero():
    result = subprocess.run(["python", "calc.py", "add", "5"], capture_output=True, cwd="/workspace")
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# 17. mem unknown subcommand — Issue #32
# ---------------------------------------------------------------------------

def test_mem_unknown_subcmd_exits_nonzero_in_process(tmp_path, monkeypatch, capsys):
    """'mem badsubcmd' must exit with code 1 and print an error message."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "mem", "badsubcmd"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "badsubcmd" in captured.out


def test_mem_unknown_subcmd_exits_nonzero_subprocess(tmp_path, monkeypatch):
    """subprocess: 'calc mem xyzzy 42' exits non-zero with an error message."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mem", "xyzzy", "42"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "xyzzy" in result.stdout or "xyzzy" in result.stderr


def test_mem_valid_subcommands_unaffected(tmp_path, monkeypatch):
    """store/recall/clear must still work correctly after the fix."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "7"])
    assert memory_recall() == 7.0
    parse_args(["calc", "mem", "clear"])
    assert memory_recall() == 0.0
