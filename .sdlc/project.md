# Project: pycalc

## Language & Runtime
- **Language:** Python 3.12
- **Runtime:** CPython (no async, no threads)
- **Entry point:** `calc.py` (also executable via `python calc.py`)
- **Test runner:** pytest >= 7.0
- **Dependencies:** `requirements.txt` — only `pytest`

---

## Architecture

### Style: Single-module procedural CLI
The entire application lives in one file (`calc.py`). There are no classes,
no packages, no layers — just plain functions called top-down from `main()`.

```
main()
  └── parse_args(sys.argv)
        ├── load_history() / save_history()          # persistence
        ├── memory_store/recall/clear()              # in-process state
        └── calculate(op, a, b)
              └── add / subtract / multiply / divide / power
                    └── format_result(result)
```

### Data Flow
```
stdin/argv → parse_args → calculate → format_result → stdout
                       ↘ load_history / save_history → calc_history.json
                       ↘ memory{} dict (process-local)
```

---

## File Map

| File | Role |
|------|------|
| `calc.py` | All application logic: arithmetic ops, CLI parsing, history I/O, memory |
| `test_calc.py` | pytest test suite (currently minimal — 4 tests) |
| `requirements.txt` | Single dep: `pytest>=7.0` |
| `README.md` | Usage examples for all CLI commands |
| `calc_history.json` | Runtime artefact — JSON array of `{op, a, b, result}` records; gitignored |
| `.sdlc/specs/add-percentage.md` | Pending feature spec: `pct` operation |
| `.sdlc/project.md` | This file |

---

## Key Patterns

### 1. Dispatch table for operations
`calculate()` maps string op-codes to callables via a plain `dict`. Adding a
new operation means: (a) write the function, (b) add one entry to `ops`.

```python
ops = {"add": add, "sub": subtract, "mul": multiply, "div": divide, "pow": power}
func = ops[op]   # KeyError = unrecognised op (currently unhandled)
```

### 2. JSON file as persistence layer
History is a flat JSON array appended on every calculation. `load_history()`
returns `[]` when the file is absent (cold start). `save_history()` overwrites
the file in full on every write.

### 3. Global mutable dict for memory
`memory = {"value": 0}` is module-level state. It resets to 0 on every new
process invocation. It is not persisted to disk and is not thread-safe.

### 4. `parse_args` as controller
`parse_args(sys.argv)` is the top-level dispatcher. It handles all commands
(`history`, `clear`, `mem`, and arithmetic). It returns the numeric result
for arithmetic calls and `None` for everything else.

---

## Invariants

These properties must hold at all times:

1. **Arithmetic purity** — `add`, `subtract`, `multiply`, `divide`, `power`
   are pure functions: same inputs always produce the same output, no side
   effects.

2. **History append-only** — Each successful arithmetic call appends exactly
   one `{op, a, b, result}` record. The `clear` command is the only
   destructive operation; it replaces history with `[]`.

3. **History record schema** — Every record in `calc_history.json` must have
   exactly the keys `op`, `a`, `b`, `result` with numeric `a`, `b`, `result`
   and string `op`.

4. **Memory neutral** — `memory_store(x)` followed by `memory_recall()`
   returns `x`. `memory_clear()` resets recall to `0`.

5. **Exit codes** — The program must exit with non-zero status on error
   conditions (invalid op, division by zero, non-numeric arguments).
   *(Currently violated — see known bugs.)*

6. **No silent crashes on bad input** — Unknown ops and non-numeric arguments
   must produce a user-readable error message, not a raw Python traceback.
   *(Currently violated — see known bugs.)*

---

## Known Bugs (source comments + analysis)

| # | Location | Description |
|---|----------|-------------|
| B1 | `divide()` | No zero-division guard — raises `ZeroDivisionError` traceback |
| B2 | `calculate()` | `ops[op]` raises `KeyError` on unknown op instead of friendly error |
| B3 | `format_result()` | No float rounding — `0.1 + 0.2` prints `0.30000000000000004` |
| B4 | `memory` dict | Global mutable state; not thread-safe; not persisted |
| B5 | `parse_args` / `mem store` | `args[3]` accessed without length check → `IndexError` |
| B6 | `parse_args` arithmetic | `float(args[2/3])` has no try/except → `ValueError` traceback on non-numeric input |
| B7 | `print_usage()` | Help text omits `mem`, `clear`, and `history` commands |
| B8 | `parse_args` history | `print(history)` prints raw Python list repr, not human-readable |
| B9 | `save_history()` | Non-atomic write — crash mid-write corrupts history file |
| B10 | All error paths | No `sys.exit(1)` — process always exits 0 even on errors |

---

## Commands

### Run the calculator
```bash
python calc.py add 2 3          # → 5.0
python calc.py sub 10 4         # → 6.0
python calc.py mul 3 7          # → 21.0
python calc.py div 15 3         # → 5.0
python calc.py pow 2 8          # → 256.0
python calc.py history          # show calculation history
python calc.py clear            # clear history
python calc.py mem              # show memory value
python calc.py mem store 42     # store value
python calc.py mem recall       # recall stored value
python calc.py mem clear        # reset memory to 0
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run tests
```bash
pytest -v
```

### Run tests with coverage (once pytest-cov is added)
```bash
pytest -v --cov=calc --cov-report=term-missing
```

### Lint (no linter configured yet; recommended)
```bash
ruff check calc.py test_calc.py        # fast linter
mypy calc.py                           # type checker
```

---

## Test Strategy

### Current state
4 tests pass; coverage is narrow (only `add`, `subtract`, `multiply`,
`calculate("add", ...)` are exercised). Critical paths are completely untested.

### Required test categories

#### 1. Arithmetic unit tests — pure functions
Each op tested with: normal case, float inputs, negative inputs.

```
test_add, test_subtract, test_multiply, test_divide, test_power
```

#### 2. Error / edge case tests — the most important gap

```python
# Division by zero
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):  # or check for clean error once fixed

# Unknown operator
def test_calculate_invalid_op():
    with pytest.raises(KeyError):           # or ValueError once fixed

# Non-numeric CLI args — requires parse_args integration test
```

#### 3. `format_result` precision tests

```python
def test_format_result_integer():    assert format_result(5.0) == "5.0"
def test_format_result_float():      # decide rounding policy then test it
```

#### 4. Memory unit tests

```python
def test_memory_store_recall()
def test_memory_clear()
def test_memory_default_is_zero()
```

#### 5. History integration tests
Use `tmp_path` (pytest fixture) to isolate `calc_history.json` per test.

```python
def test_history_appends_on_calculate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parse_args(["calc", "add", "2", "3"])
    history = load_history()
    assert len(history) == 1
    assert history[0] == {"op": "add", "a": 2.0, "b": 3.0, "result": 5.0}

def test_clear_empties_history(tmp_path, monkeypatch): ...
def test_history_file_missing_returns_empty(): ...
```

#### 6. `parse_args` CLI integration tests

```python
def test_parse_args_missing_operands(capsys): ...
def test_parse_args_unknown_op(capsys): ...
def test_parse_args_non_numeric(capsys): ...
def test_parse_args_mem_store_missing_value(capsys): ...
```

#### 7. Pending feature tests (from spec: `add-percentage.md`)

```python
def test_pct_normal():              assert calculate("pct", 25, 200) == 12.5
def test_pct_zero_denominator():    # must produce error, not crash
def test_pct_in_ops_dict():         # dispatch table includes "pct"
def test_pct_saved_to_history(): ...
def test_help_includes_pct(): ...
```

### Testing principles for this project
- **Isolate file I/O:** always use `monkeypatch.chdir(tmp_path)` or
  `monkeypatch.setattr` to redirect `HISTORY_FILE` so tests never touch the
  real working directory.
- **Isolate memory state:** call `memory_clear()` in an autouse fixture —
  the global dict leaks across tests otherwise.
- **Test error paths explicitly:** every `# Bug:` comment in `calc.py` must
  correspond to at least one test asserting the correct post-fix behaviour.
- **Use `capsys`** to assert stdout output in CLI tests rather than visual
  inspection.
- **Avoid mocking arithmetic** — these are pure functions; test them directly.

### Coverage target
Aim for >= 90% line coverage on `calc.py`. The current 4 tests cover roughly
20% of lines.

---

## Pending Work

| Priority | Item | Reference |
|----------|------|-----------|
| High | Implement `pct` operation | `.sdlc/specs/add-percentage.md` |
| High | Fix B1: divide-by-zero guard | `calc.py:divide()` |
| High | Fix B2: unknown op validation | `calc.py:calculate()` |
| High | Fix B6: non-numeric input validation | `calc.py:parse_args()` |
| High | Fix B10: exit non-zero on errors | all error paths |
| Medium | Fix B5: `mem store` arg count check | `calc.py:parse_args()` |
| Medium | Fix B9: atomic history writes | `calc.py:save_history()` |
| Medium | Fix B7: complete help text | `calc.py:print_usage()` |
| Medium | Fix B8: human-readable history output | `calc.py:parse_args()` |
| Low | Fix B3: float formatting | `calc.py:format_result()` |
| Low | Add `ruff` / `mypy` to dev deps | `requirements.txt` |
| Low | Add type annotations to all public functions | `calc.py` |
