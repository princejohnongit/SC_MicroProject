# SC MicroProject – Fuzzy Logic–Based Student Evaluation

This project implements a compact fuzzy inference system to evaluate student performance qualitatively using linguistic rules across three inputs:

- **Marks** (0–100)
- **Attendance** (0–100)
- **Assignments** (0–100)

The system produces a defuzzified score (0–100) and a qualitative label (`poor`, `average`, `good`, or `excellent`).

## Quick start

1. Ensure you have Python 3.9+ available.
2. Run the evaluator with your own inputs:

```bash
python fuzzy_student_evaluator.py --marks 82 --attendance 90 --assignments 78
```

Example output:

```
Defuzzified score: 82.39/100
Performance label: Excellent
Rule activation strengths:
 - Poor     : 0.00
 - Average  : 0.00
 - Good     : 0.52
 - Excellent: 0.62
```

## How it works

- **Fuzzification**: Triangular and trapezoidal membership functions map each input to linguistic terms (low, medium, high).
- **Rule base**: A Mamdani-style rule set combines input memberships to infer output strengths for `poor`, `average`, `good`, and `excellent`.
- **Defuzzification**: A centroid method across a discretized universe (0–100) yields the final score; the highest activated output label is reported as the qualitative result.
