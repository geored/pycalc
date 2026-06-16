# Feature: Add Percentage Operation
Status: done
Priority: high

## Description
Add a percentage calculation operation to the calculator. Users should be able to calculate what percentage one number is of another.

## Requirements
- Add pct operation: calc.py pct 25 200 prints "12.5" (25 is 12.5% of 200)
- Add pct to the usage text
- Handle edge case: second number is zero, error message not crash

## Acceptance Criteria
- [x] python calc.py pct 25 200 prints "12.5"
- [x] python calc.py pct 50 100 prints "50"
- [x] python calc.py pct 10 0 prints an error message and exits non-zero
- [x] python calc.py help shows pct in the operations list
- [x] Calculation is saved to history
- [x] Test exists for percentage calculation
- [x] Test exists for percentage with zero denominator
