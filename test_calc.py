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
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
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


# ---------------------------------------------------------------------------
# 18. parse_args — in-process error-path coverage (Issue #27)
#     Covers lines 169–182, 210, 213 that subprocess tests cannot reach.
# ---------------------------------------------------------------------------

def test_parse_args_invalid_a_exits(tmp_path, monkeypatch, capsys):
    """Non-numeric first operand exits 1 and echoes the bad token (lines 169–171)."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        parse_args(["calc", "add", "foo", "3"])
    assert exc.value.code == 1
    assert "foo" in capsys.readouterr().out


def test_parse_args_invalid_b_exits(tmp_path, monkeypatch, capsys):
    """Non-numeric second operand exits 1 and echoes the bad token (lines 174–176)."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        parse_args(["calc", "add", "3", "bar"])
    assert exc.value.code == 1
    assert "bar" in capsys.readouterr().out


def test_parse_args_unknown_op_exits(tmp_path, monkeypatch, capsys):
    """Unknown operator exits 1 and echoes the bad op name (lines 180–182)."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        parse_args(["calc", "modulo", "10", "3"])
    assert exc.value.code == 1
    assert "modulo" in capsys.readouterr().out


def test_parse_args_div_by_zero_exits(tmp_path, monkeypatch, capsys):
    """Division by zero exits 1 with a friendly error message (lines 180–182)."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        parse_args(["calc", "div", "10", "0"])
    assert exc.value.code == 1
    assert "Error" in capsys.readouterr().out


def test_main_calls_parse_args(tmp_path, monkeypatch, capsys):
    """main() delegates to parse_args(sys.argv) and prints a result (line 210)."""
    import calc as calc_module
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(calc_module.sys, "argv", ["calc", "add", "1", "2"])
    calc_module.main()
    assert "3" in capsys.readouterr().out


def test_dunder_main_guard(tmp_path, monkeypatch):
    """The if __name__ == '__main__' guard runs main() when the module is the
    entry point (line 213).  We exercise it by running the file as a script
    and checking the exit code and output."""
    import subprocess as sp
    result = sp.run(
        [sys.executable, "/workspace/calc.py", "add", "4", "5"],
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert "9" in result.stdout


# ---------------------------------------------------------------------------
# 19. save_history OSError/TypeError handled gracefully — Issue #44
# ---------------------------------------------------------------------------

def test_save_history_oserror_in_arithmetic_branch_exits_1(tmp_path, monkeypatch, capsys):
    """OSError from save_history() during arithmetic must print friendly error and exit 1."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    with mock.patch("calc.save_history", side_effect=OSError("disk full")):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["calc", "add", "2", "3"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "disk full" in captured.err
    assert "Traceback" not in captured.err


def test_save_history_oserror_in_arithmetic_result_still_printed(tmp_path, monkeypatch, capsys):
    """Result must be printed to stdout before the history save fails."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    with mock.patch("calc.save_history", side_effect=OSError("disk full")):
        with pytest.raises(SystemExit):
            parse_args(["calc", "add", "2", "3"])
    captured = capsys.readouterr()
    assert "5" in captured.out


def test_save_history_typeerror_in_arithmetic_branch_exits_1(tmp_path, monkeypatch, capsys):
    """TypeError from save_history() during arithmetic must print friendly error and exit 1."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    with mock.patch("calc.save_history", side_effect=TypeError("not serialisable")):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["calc", "mul", "3", "4"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "Traceback" not in captured.err


def test_save_history_oserror_in_clear_branch_exits_1(tmp_path, monkeypatch, capsys):
    """OSError from save_history([]) during 'clear' must print friendly error and exit 1."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    with mock.patch("calc.save_history", side_effect=OSError("permission denied")):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["calc", "clear"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "permission denied" in captured.err
    assert "Traceback" not in captured.err


def test_save_history_typeerror_in_clear_branch_exits_1(tmp_path, monkeypatch, capsys):
    """TypeError from save_history([]) during 'clear' must print friendly error and exit 1."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    with mock.patch("calc.save_history", side_effect=TypeError("not serialisable")):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["calc", "clear"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "Traceback" not in captured.err


# ---------------------------------------------------------------------------
# 20. save_history() — narrow exception type + stderr warning (Issue #45)
# ---------------------------------------------------------------------------

def test_save_history_warns_to_stderr_on_oserror(tmp_path, monkeypatch, capsys):
    """save_history() must print a Warning to stderr before re-raising OSError."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)
    data = [{"op": "add", "a": 1.0, "b": 2.0, "result": 3.0}]

    with mock.patch("tempfile.NamedTemporaryFile", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            save_history(data)

    captured = capsys.readouterr()
    assert "Warning" in captured.err, (
        f"Expected 'Warning' in stderr but got: {captured.err!r}"
    )
    assert "disk full" in captured.err, (
        f"Expected the OSError message in stderr but got: {captured.err!r}"
    )


def test_save_history_warns_to_stderr_on_typeerror(tmp_path, monkeypatch, capsys):
    """save_history() must print a Warning to stderr before re-raising TypeError."""
    monkeypatch.chdir(tmp_path)

    class Unserializable:
        pass

    bad_data = [Unserializable()]
    with pytest.raises(TypeError):
        save_history(bad_data)

    captured = capsys.readouterr()
    assert "Warning" in captured.err, (
        f"Expected 'Warning' in stderr when json.dump() fails but got: {captured.err!r}"
    )


def test_save_history_reraises_oserror_after_warning(tmp_path, monkeypatch, capsys):
    """save_history() must still re-raise OSError after emitting the warning."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)

    with mock.patch("tempfile.NamedTemporaryFile", side_effect=OSError("permission denied")):
        with pytest.raises(OSError, match="permission denied"):
            save_history([])

    # Warning must still have been emitted
    captured = capsys.readouterr()
    assert "Warning" in captured.err


def test_save_history_reraises_typeerror_after_warning(tmp_path, monkeypatch, capsys):
    """save_history() must still re-raise TypeError after emitting the warning."""
    monkeypatch.chdir(tmp_path)

    class Unserializable:
        pass

    bad_data = [Unserializable()]
    with pytest.raises(TypeError):
        save_history(bad_data)

    # Warning must still have been emitted
    captured = capsys.readouterr()
    assert "Warning" in captured.err


def test_save_history_does_not_catch_other_exceptions(tmp_path, monkeypatch, capsys):
    """save_history() must NOT swallow exceptions outside (OSError, TypeError)."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)

    # RuntimeError is outside the (OSError, TypeError) catch — must propagate unmodified
    with mock.patch("tempfile.NamedTemporaryFile", side_effect=RuntimeError("unexpected")):
        with pytest.raises(RuntimeError, match="unexpected"):
            save_history([])


def test_save_history_warning_message_contains_save_history_context(tmp_path, monkeypatch, capsys):
    """The stderr warning should be diagnostic enough to identify the save failure."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)

    with mock.patch("tempfile.NamedTemporaryFile", side_effect=OSError("no space left")):
        with pytest.raises(OSError):
            save_history([])

    captured = capsys.readouterr()
    # The warning must include the exception message so operators know what went wrong
    assert "no space left" in captured.err, (
        f"Warning must include the exception message; stderr was: {captured.err!r}"
    )


def test_save_history_warning_goes_to_stderr_not_stdout(tmp_path, monkeypatch, capsys):
    """The warning must go to stderr, not stdout, consistent with load_history()."""
    import unittest.mock as mock
    monkeypatch.chdir(tmp_path)

    with mock.patch("tempfile.NamedTemporaryFile", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            save_history([])

    captured = capsys.readouterr()
    assert "Warning" not in captured.out, (
        "Warning must go to stderr, not stdout"
    )
    assert "Warning" in captured.err


# ---------------------------------------------------------------------------
# 21. format_result() — input validation: complex and non-finite floats (#48)
# ---------------------------------------------------------------------------

def test_format_result_complex_raises_type_error():
    """format_result() must raise TypeError when given a complex number."""
    with pytest.raises(TypeError):
        format_result(complex(0, 1))


def test_format_result_complex_nonzero_real_raises_type_error():
    """format_result() must raise TypeError for complex numbers with a non-zero real part."""
    with pytest.raises(TypeError):
        format_result(complex(3, 4))


def test_format_result_nan_raises_value_error():
    """format_result() must raise ValueError for float('nan')."""
    with pytest.raises(ValueError):
        format_result(float('nan'))


def test_format_result_inf_raises_value_error():
    """format_result() must raise ValueError for float('inf')."""
    with pytest.raises(ValueError):
        format_result(float('inf'))


def test_format_result_negative_inf_raises_value_error():
    """format_result() must raise ValueError for float('-inf')."""
    with pytest.raises(ValueError):
        format_result(float('-inf'))


def test_format_result_complex_error_message_is_readable():
    """TypeError from format_result() on complex input must include a user-readable message."""
    with pytest.raises(TypeError, match="complex"):
        format_result(complex(1, 2))


def test_format_result_nan_error_message_is_readable():
    """ValueError from format_result() on nan must include a user-readable message."""
    with pytest.raises(ValueError, match="[Nn]aN|nan|finite|not a number"):
        format_result(float('nan'))


def test_format_result_inf_error_message_is_readable():
    """ValueError from format_result() on inf must include a user-readable message."""
    with pytest.raises(ValueError, match="[Ii]nf|finite"):
        format_result(float('inf'))


# Regression: valid inputs must continue to work correctly after the guard is added

def test_format_result_valid_integer_float_regression():
    """Regression: format_result(5.0) must still return '5' after the guard."""
    assert format_result(5.0) == "5"


def test_format_result_valid_float_noise_regression():
    """Regression: 0.1 + 0.2 must still format as '0.3' after the guard."""
    assert format_result(0.1 + 0.2) == "0.3"


def test_format_result_valid_large_float_regression():
    """Regression: format_result(256.0) must still return '256' after the guard."""
    assert format_result(256.0) == "256"


# ---------------------------------------------------------------------------
# 22. Memory volatility warning — Issue #49
#     mem store must warn user that memory is session-only.
#     print_usage() must note memory is not persisted between invocations.
# ---------------------------------------------------------------------------

def test_mem_store_prints_volatility_warning(tmp_path, monkeypatch, capsys):
    """'mem store' must print a warning that memory is session-only."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "42"])
    captured = capsys.readouterr()
    # The warning must mention session-only or similar wording
    combined = captured.out.lower()
    assert "session" in combined or "not persisted" in combined or "lost" in combined, (
        f"Expected a session-only volatility warning in stdout but got: {captured.out!r}"
    )


def test_mem_store_volatility_warning_is_on_stdout(tmp_path, monkeypatch, capsys):
    """Volatility warning from 'mem store' must go to stdout (it is informational)."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "42"])
    captured = capsys.readouterr()
    combined = captured.out.lower()
    # Warning must be on stdout, consistent with the "Stored: …" confirmation line
    assert "session" in combined or "not persisted" in combined or "lost" in combined, (
        "Volatility warning must appear on stdout, not only stderr"
    )


def test_mem_store_still_prints_stored_confirmation_with_warning(tmp_path, monkeypatch, capsys):
    """'mem store' must still print 'Stored: 42' alongside the warning (no regression)."""
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "mem", "store", "42"])
    captured = capsys.readouterr()
    assert "Stored" in captured.out, (
        f"'Stored' confirmation line missing from stdout: {captured.out!r}"
    )
    assert "42" in captured.out


def test_mem_store_volatility_warning_subprocess(tmp_path, monkeypatch):
    """Subprocess: 'calc mem store 42' must emit the session-only warning on stdout."""
    monkeypatch.chdir(tmp_path)
    import subprocess as sp
    result = sp.run(
        [sys.executable, "/workspace/calc.py", "mem", "store", "42"],
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 0
    combined = result.stdout.lower()
    assert "session" in combined or "not persisted" in combined or "lost" in combined, (
        f"Expected session-only warning in subprocess stdout but got: {result.stdout!r}"
    )


def test_print_usage_mem_store_mentions_session_only(capsys):
    """print_usage() must document that 'mem store' memory is session-only / not persisted."""
    print_usage()
    captured = capsys.readouterr()
    combined = captured.out.lower()
    assert "session" in combined or "not persisted" in combined or "session-only" in combined, (
        f"print_usage() must note that memory is session-only; output was:\n{captured.out}"
    )


def test_print_usage_mem_store_line_contains_session_note(capsys):
    """The 'mem store' line in print_usage() specifically must contain the session note."""
    print_usage()
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    mem_store_lines = [l for l in lines if "mem store" in l]
    assert mem_store_lines, "print_usage() must contain a line with 'mem store'"
    mem_store_line = mem_store_lines[0].lower()
    assert "session" in mem_store_line or "not persisted" in mem_store_line or "session-only" in mem_store_line, (
        f"The 'mem store' line must note that memory is session-only; line was: {mem_store_lines[0]!r}"
    )


def test_mem_recall_and_clear_not_affected_by_warning(tmp_path, monkeypatch, capsys):
    """'mem recall' and 'mem clear' must NOT print the volatility warning."""
    monkeypatch.chdir(tmp_path)
    memory_store(42)

    parse_args(["calc", "mem", "recall"])
    recall_out = capsys.readouterr().out.lower()

    parse_args(["calc", "mem", "clear"])
    clear_out = capsys.readouterr().out.lower()

    for output, cmd in [(recall_out, "mem recall"), (clear_out, "mem clear")]:
        assert "session" not in output and "not persisted" not in output, (
            f"'{cmd}' must not print the session-only warning; got: {output!r}"
        )


# ---------------------------------------------------------------------------
# 23. power() with negative base and fractional exponent — Issue #59
#     power(-1, 0.5) must raise ValueError (not produce a complex result)
# ---------------------------------------------------------------------------

def test_power_complex_result_raises_value_error():
    """power(-1, 0.5) must raise ValueError — complex results are not allowed."""
    with pytest.raises(ValueError, match="[Cc]omplex|non-negative"):
        power(-1, 0.5)


def test_power_negative_base_fractional_exp_raises_value_error():
    """power(-4, 0.5) must raise ValueError — sqrt of negative is complex."""
    with pytest.raises(ValueError, match="[Cc]omplex|non-negative"):
        power(-4, 0.5)


def test_calculate_pow_complex_raises_value_error():
    """calculate('pow', -1, 0.5) must raise ValueError via the dispatch table."""
    with pytest.raises(ValueError, match="[Cc]omplex|non-negative"):
        calculate("pow", -1, 0.5)


def test_parse_args_pow_complex_exits_1(tmp_path, monkeypatch, capsys):
    """parse_args(['calc','pow','-1','0.5']) must exit 1 with a friendly Error: message."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["calc", "pow", "-1", "0.5"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "Traceback" not in captured.out
    assert "TypeError" not in captured.out


def test_pow_complex_cli_exits_nonzero(tmp_path, monkeypatch):
    """subprocess: python calc.py pow -1 0.5 must exit with non-zero status."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "-1", "0.5"],
        capture_output=True, text=True
    )
    assert result.returncode != 0


def test_pow_complex_cli_friendly_message(tmp_path, monkeypatch):
    """subprocess: python calc.py pow -1 0.5 must print friendly Error: message, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "-1", "0.5"],
        capture_output=True, text=True
    )
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback" not in result.stderr
    assert "TypeError" not in result.stderr


def test_pow_complex_no_history_entry(tmp_path, monkeypatch):
    """Failed pow (complex result) must NOT write a history entry."""
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "-1", "0.5"],
        capture_output=True, text=True
    )
    assert load_history() == []


def test_pow_valid_cases_still_work(tmp_path, monkeypatch):
    """Valid pow cases must be unaffected: 2**8, 4**0.5, 2**-1."""
    monkeypatch.chdir(tmp_path)
    assert power(2, 8) == 256.0
    assert power(4, 0.5) == pytest.approx(2.0)
    assert power(2, -1) == pytest.approx(0.5)


def test_power_negative_base_integer_exponent_still_works():
    """power(-2, 3) must still return -8 — only fractional exponents on negative bases fail."""
    assert power(-2, 3) == -8.0


def test_power_zero_base_fractional_exponent_still_works():
    """power(0, 0.5) must return 0.0 — zero base with fractional exponent is valid."""
    assert power(0, 0.5) == 0.0


# ---------------------------------------------------------------------------
# 24. Non-finite / oversized results from power() — Issue #60
#     Covers: mul 0 inf → nan, pow 1e308 2 → inf, pow 2 10000 → huge int
# ---------------------------------------------------------------------------

def test_mul_zero_inf_exits_nonzero(tmp_path, monkeypatch):
    """0 * inf = nan; must exit non-zero with a friendly message, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mul", "0", "inf"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_mul_zero_inf_friendly_message(tmp_path, monkeypatch):
    """0 * inf = nan; stdout/stderr must contain an Error: message, not a raw traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "mul", "0", "inf"],
        capture_output=True, text=True,
    )
    combined = result.stdout + result.stderr
    assert "Error" in combined
    assert "Traceback" not in result.stderr


def test_mul_zero_inf_no_history_entry(tmp_path, monkeypatch):
    """Failed mul (nan result) must NOT write a history entry."""
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "mul", "0", "inf"],
        capture_output=True, text=True,
    )
    assert load_history() == []


def test_pow_overflow_exits_nonzero(tmp_path, monkeypatch):
    """1e308 ** 2 overflows to inf; must exit non-zero with a friendly message, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "1e308", "2"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_pow_overflow_friendly_message(tmp_path, monkeypatch):
    """1e308 ** 2 → friendly Error: message, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "1e308", "2"],
        capture_output=True, text=True,
    )
    combined = result.stdout + result.stderr
    assert "Error" in combined
    assert "Traceback" not in result.stderr


def test_pow_overflow_no_history_entry(tmp_path, monkeypatch):
    """Failed pow (overflow to inf) must NOT write a history entry."""
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "1e308", "2"],
        capture_output=True, text=True,
    )
    assert load_history() == []


def test_pow_huge_int_overflow_exits_nonzero(tmp_path, monkeypatch):
    """2 ** 10000 produces a huge Python int; must exit non-zero, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "2", "10000"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_pow_huge_int_overflow_friendly_message(tmp_path, monkeypatch):
    """2 ** 10000 → friendly Error: message, no traceback."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "2", "10000"],
        capture_output=True, text=True,
    )
    combined = result.stdout + result.stderr
    assert "Error" in combined
    assert "Traceback" not in result.stderr


def test_pow_huge_int_no_history_entry(tmp_path, monkeypatch):
    """Failed pow (huge int result) must NOT write a history entry."""
    monkeypatch.chdir(tmp_path)
    save_history([])
    subprocess.run(
        [sys.executable, "/workspace/calc.py", "pow", "2", "10000"],
        capture_output=True, text=True,
    )
    assert load_history() == []


# ---------------------------------------------------------------------------
# 25. format_result() — int input handling + OverflowError → ValueError (#61)
# ---------------------------------------------------------------------------

def test_format_result_int_small():
    """format_result(5) — small int — must return '5' without error."""
    assert format_result(5) == "5"


def test_format_result_int_zero():
    """format_result(0) — int zero — must return '0' without error."""
    assert format_result(0) == "0"


def test_format_result_int_negative():
    """format_result(-3) — negative int — must return '-3' without error."""
    assert format_result(-3) == "-3"


def test_format_result_int_large_but_representable():
    """format_result(2**53) — large int still representable as float — must succeed."""
    result = format_result(2**53)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_result_huge_int_raises_value_error():
    """format_result(2**10000) — too large for float — must raise ValueError, not OverflowError."""
    with pytest.raises(ValueError, match="[Tt]oo large|finite|[Oo]verflow"):
        format_result(2**10000)


def test_format_result_huge_int_not_overflow_error():
    """format_result(2**10000) must NOT raise a bare OverflowError (must be converted to ValueError)."""
    try:
        format_result(2**10000)
    except ValueError:
        pass  # expected — correct behaviour
    except OverflowError:
        pytest.fail(
            "format_result(2**10000) raised OverflowError; "
            "it must be caught and re-raised as ValueError"
        )


def test_format_result_type_annotation_accepts_int():
    """format_result() with int input must not raise TypeError or AttributeError."""
    try:
        format_result(42)
    except (TypeError, AttributeError) as e:
        pytest.fail(f"format_result(42) raised {type(e).__name__}: {e}")


def test_format_result_int_result_matches_float_result():
    """format_result(5) and format_result(5.0) must produce the same string."""
    assert format_result(5) == format_result(5.0)


def test_format_result_existing_behaviour_unchanged_after_int_fix():
    """Regression: all previously passing format_result tests must still pass."""
    assert format_result(5.0) == "5"
    assert format_result(0.0) == "0"
    assert format_result(-3.0) == "-3"
    assert format_result(0.1 + 0.2) == "0.3"
    assert format_result(256.0) == "256"
    assert format_result(1 / 3) == "0.3333333333"


# ---------------------------------------------------------------------------
# 26. History cap at MAX_HISTORY records — Issue #64
# ---------------------------------------------------------------------------

def test_max_history_constant_exists():
    """MAX_HISTORY must be an exported positive int constant from the calc module."""
    import calc
    assert hasattr(calc, "MAX_HISTORY"), "calc module must define MAX_HISTORY"
    assert isinstance(calc.MAX_HISTORY, int), "MAX_HISTORY must be an int"
    assert calc.MAX_HISTORY > 0, "MAX_HISTORY must be positive"


def test_history_capped_at_max(tmp_path, monkeypatch):
    """After MAX_HISTORY + 1 calculations, history must contain at most MAX_HISTORY records."""
    from calc import MAX_HISTORY
    monkeypatch.chdir(tmp_path)
    # Pre-seed history with exactly MAX_HISTORY records
    records = [{"op": "add", "a": float(i), "b": 1.0, "result": float(i + 1)} for i in range(MAX_HISTORY)]
    save_history(records)
    # Add one more via parse_args — this must trigger the cap
    parse_args(["calc", "add", "999", "1"])
    history = load_history()
    assert len(history) <= MAX_HISTORY, (
        f"Expected at most {MAX_HISTORY} records after cap, got {len(history)}"
    )


def test_history_keeps_most_recent_record_at_cap(tmp_path, monkeypatch):
    """When the cap is exceeded, the newest record must be the last one in the file."""
    from calc import MAX_HISTORY
    monkeypatch.chdir(tmp_path)
    records = [{"op": "add", "a": float(i), "b": 1.0, "result": float(i + 1)} for i in range(MAX_HISTORY)]
    save_history(records)
    parse_args(["calc", "mul", "7", "6"])
    history = load_history()
    assert history[-1]["op"] == "mul", (
        f"Expected last record op to be 'mul', got {history[-1]['op']!r}"
    )
    assert history[-1]["result"] == 42.0, (
        f"Expected last record result to be 42.0, got {history[-1]['result']}"
    )
