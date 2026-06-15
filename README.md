# pycalc

A simple calculator CLI with history and memory.

## Usage

```bash
python calc.py add 2 3      # Addition
python calc.py sub 10 4     # Subtraction
python calc.py mul 3 7      # Multiplication
python calc.py div 15 3     # Division
python calc.py pow 2 8      # Power

python calc.py history      # Show calculation history
python calc.py clear        # Clear history
python calc.py mem          # Show memory value
python calc.py mem store 42 # Store value in memory
python calc.py mem recall   # Recall memory value
python calc.py mem clear    # Clear memory
```

## Testing

```bash
pip install -r requirements.txt
pytest -v
```
