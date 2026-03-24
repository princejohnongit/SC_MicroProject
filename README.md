# SC MicroProject – Fuzzy Logic–Based Student Evaluation

This repository contains a compact, fully testable **Mamdani fuzzy inference system** for evaluating student performance from three educational indicators:

- **Marks** (`0–100`)
- **Attendance** (`0–100`)
- **Assignments** (`0–100`)

The evaluator outputs:

1. A **defuzzified numeric score** (`0–100`)
2. A **qualitative label** (`poor`, `average`, `good`, `excellent`)
3. **Rule activation strengths** for each output class

---

## Table of contents

- [Project goals](#project-goals)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Command-line usage](#command-line-usage)
- [Python API usage](#python-api-usage)
- [How the fuzzy system works](#how-the-fuzzy-system-works)
  - [Input membership functions](#input-membership-functions)
  - [Rule base](#rule-base)
  - [Output membership functions](#output-membership-functions)
  - [Defuzzification and final label](#defuzzification-and-final-label)
- [Test suite](#test-suite)
- [Validation and constraints](#validation-and-constraints)
- [Design notes and extension points](#design-notes-and-extension-points)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)

---

## Project goals

This project is intended to demonstrate a practical educational use-case of fuzzy logic:

- Convert human-style reasoning (e.g., “high marks with medium attendance is still good”) into executable rules.
- Handle uncertainty and gray areas better than hard cutoffs.
- Provide both a **transparent explanation signal** (`details` activation strengths) and a final concise assessment label.

---

## Repository structure

```text
SC_MicroProject/
├── fuzzy_student_evaluator.py            # Core fuzzy system + CLI entry point
├── tests/
│   └── test_fuzzy_student_evaluator.py   # Unit tests for evaluator and CLI behavior
└── README.md
```

---

## Requirements

- Python **3.9+** (no third-party dependencies required)
- Standard library modules only (`dataclasses`, `typing`, `unittest`, `unittest.mock`, `math`)

---

## Quick start

From the repository root:

```bash
python fuzzy_student_evaluator.py
```

Then enter prompted values for marks, attendance, and assignments.

### Example interactive session

```text
Enter marks (0-100): 82
Enter attendance (0-100): 90
Enter assignments (0-100): 78
Defuzzified score: 87.39/100
Performance label: Excellent
Rule activation strengths:
 - Poor     : 0.00
 - Average  : 0.00
 - Good     : 0.20
 - Excellent: 0.67
```

---

## Command-line usage

The file `fuzzy_student_evaluator.py` is executable as a script.

```bash
python fuzzy_student_evaluator.py
```

### CLI behavior

- Prompts for three numeric inputs.
- Rejects non-numeric input with `SystemExit` and a clear message:
  - `Invalid numeric input: ...`
- Rejects out-of-range numeric values (`<0` or `>100`) with `SystemExit`:
  - `<field> must be between 0 and 100. Got <value>.`
- Prints:
  - Defuzzified score
  - Capitalized performance label
  - Per-label activation strengths (`poor`, `average`, `good`, `excellent`)

---

## Python API usage

You can use either the helper function or the evaluator class directly.

### Option 1: Helper function

```python
from fuzzy_student_evaluator import evaluate_student

result = evaluate_student(marks=82, attendance=90, assignments=78)
print(result.score)    # 87.39 (approx)
print(result.label)    # "excellent"
print(result.details)  # {'poor': ..., 'average': ..., 'good': ..., 'excellent': ...}
```

### Option 2: Reusable evaluator instance

```python
from fuzzy_student_evaluator import FuzzyStudentEvaluator

evaluator = FuzzyStudentEvaluator()  # default resolution=201
result = evaluator.evaluate(75, 84, 80)
```

### Returned object

`evaluate(...)` returns `EvaluationResult`:

- `score: float` (rounded to 2 decimals)
- `label: str`
- `details: Dict[str, float]` (output activation strengths)

---

## How the fuzzy system works

The implementation follows a classic Mamdani flow:

1. **Fuzzification** of each input
2. **Rule evaluation** using `min`/`max`
3. **Aggregation** of output membership functions
4. **Centroid defuzzification** over `[0, 100]`
5. **Final label** from strongest output activation

### Input membership functions

All three inputs use trapezoidal membership functions for `low`, `medium`, and `high`.

#### Marks

- `low`: trapezoidal `(0, 0, 40, 55)`
- `medium`: trapezoidal `(45, 60, 70, 80)`
- `high`: trapezoidal `(70, 85, 100, 100)`

#### Attendance

- `low`: trapezoidal `(0, 0, 50, 65)`
- `medium`: trapezoidal `(60, 72, 82, 92)`
- `high`: trapezoidal `(80, 90, 100, 100)`

#### Assignments

- `low`: trapezoidal `(0, 0, 45, 60)`
- `medium`: trapezoidal `(50, 60, 70, 80)`
- `high`: trapezoidal `(70, 82, 100, 100)`

> Note: The module includes a triangular membership helper for future extensibility and experimentation, but the current production rule set and output aggregation intentionally use trapezoidal functions only.

### Rule base

Rules map input conditions to output classes:

1. `excellent` ← `marks.high` AND `attendance.high` AND `assignments.high`
2. `good` ← `marks.high` AND `attendance.medium`
3. `good` ← `marks.medium` AND `attendance.high`
4. `good` ← `marks.high` AND `attendance.high` AND `assignments.medium`
5. `good` ← `marks.medium` AND `attendance.medium` AND `assignments.high`
6. `average` ← `marks.medium` AND `attendance.medium` AND `assignments.medium`
7. `average` ← `assignments.low` AND (`marks.medium` OR `marks.high`)
8. `poor` ← `marks.low` OR `attendance.low`
9. `poor` ← `marks.low` AND `assignments.low`

Rule composition uses:

- `AND` → `min(...)`
- `OR` → `max(...)`
- Multiple rules targeting the same output label are merged using `max(...)`.

### Output membership functions

The output universe (`0–100`) defines fuzzy sets:

- `poor`: trapezoidal `(0, 0, 35, 50)`
- `average`: trapezoidal `(40, 50, 60, 70)`
- `good`: trapezoidal `(65, 72, 82, 90)`
- `excellent`: trapezoidal `(80, 88, 100, 100)`

### Defuzzification and final label

- Defuzzification uses the **centroid** method over a discretized universe.
- Default resolution is `201` points:
  - `self._universe = [i * (100 / (resolution - 1)) for i in range(resolution)]`
- Final score is rounded to 2 decimals.
- Final label is selected by strongest activation from `details`.
- Tie breaking is deterministic: `max(strengths.items(), key=lambda item: (item[1], item[0]))` is used, so if two labels have equal strength, the one that comes later alphabetically is selected (for example, `"poor"` beats `"good"` because `"p"` > `"g"`).

---

## Test suite

Run tests with:

```bash
python -m unittest tests.test_fuzzy_student_evaluator -v
```

Current tests validate:

- Input bounds checking
- High-performance classification behavior
- Low-performance classification behavior
- CLI success path output formatting
- CLI invalid-input handling

---

## Validation and constraints

- Inputs must be numeric values in `[0, 100]`.
- Any out-of-range input raises `ValueError` in API usage and exits in CLI mode.
- If no rule fires (denominator `0` during centroid), defuzzified score defaults to `0.0`.

---

## Design notes and extension points

You can customize system behavior by adjusting:

1. **Membership function boundaries** in `_fuzzify(...)` and `_aggregate_output(...)`
2. **Rule base** in `_apply_rules(...)`
3. **Defuzzification granularity** by changing `resolution` in `FuzzyStudentEvaluator(...)`

Potential enhancement directions:

- Add weighted rule confidence
- Add more input dimensions (e.g., project work, quizzes)
- Export inference traces for explainability dashboards
- Provide batch evaluation for CSV datasets

---

## Troubleshooting

- **`ModuleNotFoundError` when running tests**
  - Ensure command is run from repository root.
- **Unexpected label**
  - Inspect `result.details` to see which output set dominates.
  - Review rule interactions where `poor` can be activated by low marks or attendance.
- **Different score than expected after edits**
  - Small boundary or resolution changes can shift centroid output.

---

## Known limitations

- Single-file implementation keeps things simple but is not modularized for larger production systems.
- No external persistence or API endpoint layer is included.
- No plotting/visualization of membership curves is provided.
- No explicit project license file is included in this repository.
