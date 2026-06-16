# pycalc

A simple calculator CLI with history and memory.

## Usage

```bash
python calc.py add 2 3      # Addition       → 5
python calc.py sub 10 4     # Subtraction    → 6
python calc.py mul 3 7      # Multiplication → 21
python calc.py div 15 3     # Division       → 5
python calc.py pow 2 8      # Power          → 256
python calc.py pct 25 200   # Percentage     → 12.5

python calc.py history      # Show calculation history
python calc.py clear        # Clear history
python calc.py mem          # Show memory value
python calc.py mem store 42 # Store value in memory
python calc.py mem recall   # Recall memory value
python calc.py mem clear    # Clear memory
```

Note: whole-number results are printed without a `.0` suffix (e.g. `5`, not `5.0`).
Floating-point noise is suppressed (e.g. `0.1 + 0.2` prints `0.3`).

## Testing

```bash
pip install -r requirements.txt
pytest -v
```
