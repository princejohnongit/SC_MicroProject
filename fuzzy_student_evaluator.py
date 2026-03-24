from __future__ import annotations

"""
Fuzzy Logic–Based Student Evaluation System.

This module implements a compact fuzzy inference system to evaluate student
performance using linguistic rules across three inputs:
 - marks (0–100)
 - attendance (0–100)
 - assignment completion/quality (0–100)

The output is a qualitative performance label alongside a defuzzified score
between 0 and 100.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


_FUZZY_LEVELS = ("low", "medium", "high")


def _triangular(x: float, a: float, b: float, c: float) -> float:
    """Triangular membership function."""
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def _trapezoidal(x: float, a: float, b: float, c: float, d: float) -> float:
    """Trapezoidal membership function."""
    if x < a or x > d:
        return 0.0
    if x == a:
        return 1.0 if a == b else 0.0
    if x == d:
        return 1.0 if c == d else 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


def _validate_percent(value: float, name: str) -> None:
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100. Got {value}.")


def _normalize_fuzzy_level(value: str, name: str) -> str:
    level = value.strip().lower()
    if level not in _FUZZY_LEVELS:
        allowed = ", ".join(_FUZZY_LEVELS)
        raise ValueError(f"{name} must be one of: {allowed}. Got {value!r}.")
    return level


@dataclass
class EvaluationResult:
    score: float
    label: str
    details: Dict[str, float]


class FuzzyStudentEvaluator:
    """A simple Mamdani fuzzy inference system for student evaluation."""

    def __init__(self, resolution: int = 201) -> None:
        # Resolution controls discretization for defuzzification.
        self._universe = [i * (100 / (resolution - 1)) for i in range(resolution)]

    def _fuzzify(self, marks: float, attendance: float, assignments: float) -> Dict[str, Dict[str, float]]:
        inputs = {
            "marks": {
                "low": _trapezoidal(marks, 0, 0, 40, 55),
                "medium": _trapezoidal(marks, 45, 60, 70, 80),
                "high": _trapezoidal(marks, 70, 85, 100, 100),
            },
            "attendance": {
                "low": _trapezoidal(attendance, 0, 0, 50, 65),
                "medium": _trapezoidal(attendance, 60, 72, 82, 92),
                "high": _trapezoidal(attendance, 80, 90, 100, 100),
            },
            "assignments": {
                "low": _trapezoidal(assignments, 0, 0, 45, 60),
                "medium": _trapezoidal(assignments, 50, 60, 70, 80),
                "high": _trapezoidal(assignments, 70, 82, 100, 100),
            },
        }
        return inputs

    def _apply_rules(self, inputs: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        rules: Iterable[Tuple[str, float]] = [
            ("excellent", min(inputs["marks"]["high"], inputs["attendance"]["high"], inputs["assignments"]["high"])),
            ("good", min(inputs["marks"]["high"], inputs["attendance"]["medium"])),
            ("good", min(inputs["marks"]["medium"], inputs["attendance"]["high"])),
            ("good", min(inputs["marks"]["high"], inputs["attendance"]["high"], inputs["assignments"]["medium"])),
            ("good", min(inputs["marks"]["medium"], inputs["attendance"]["medium"], inputs["assignments"]["high"])),
            ("average", min(inputs["marks"]["medium"], inputs["attendance"]["medium"], inputs["assignments"]["medium"])),
            ("average", min(inputs["assignments"]["low"], max(inputs["marks"]["medium"], inputs["marks"]["high"]))),
            ("poor", max(inputs["marks"]["low"], inputs["attendance"]["low"])),
            ("poor", min(inputs["marks"]["low"], inputs["assignments"]["low"])),
        ]

        output_strength = {label: 0.0 for label in ["poor", "average", "good", "excellent"]}
        for label, strength in rules:
            output_strength[label] = max(output_strength[label], strength)
        return output_strength

    def _aggregate_output(self, strengths: Dict[str, float], x: float) -> float:
        membership_functions = {
            "poor": lambda v: _trapezoidal(v, 0, 0, 35, 50),
            "average": lambda v: _trapezoidal(v, 40, 50, 60, 70),
            "good": lambda v: _trapezoidal(v, 65, 72, 82, 90),
            "excellent": lambda v: _trapezoidal(v, 80, 88, 100, 100),
        }

        return max(
            min(strengths[label], membership_functions[label](x))
            for label in strengths
        )

    def _defuzzify(self, strengths: Dict[str, float]) -> float:
        numerator = 0.0
        denominator = 0.0
        for x in self._universe:
            mu = self._aggregate_output(strengths, x)
            numerator += x * mu
            denominator += mu
        return numerator / denominator if denominator else 0.0

    def _label_from_score(self, score: float, strengths: Dict[str, float]) -> str:
        # Prefer the label with the strongest activation; break ties alphabetically for determinism.
        return max(strengths.items(), key=lambda item: (item[1], item[0]))[0]

    def evaluate(self, marks: float, attendance: float, assignments: float) -> EvaluationResult:
        """Run fuzzy evaluation and return a qualitative performance summary."""
        _validate_percent(marks, "marks")
        _validate_percent(attendance, "attendance")
        _validate_percent(assignments, "assignments")

        fuzzified = self._fuzzify(marks, attendance, assignments)
        strengths = self._apply_rules(fuzzified)
        score = self._defuzzify(strengths)
        label = self._label_from_score(score, strengths)
        return EvaluationResult(score=round(score, 2), label=label, details=strengths)

    def evaluate_fuzzy(self, marks: str, attendance: str, assignments: str) -> EvaluationResult:
        """Evaluate directly from fuzzy linguistic levels (low/medium/high)."""
        marks_level = _normalize_fuzzy_level(marks, "marks")
        attendance_level = _normalize_fuzzy_level(attendance, "attendance")
        assignments_level = _normalize_fuzzy_level(assignments, "assignments")

        fuzzified = {
            "marks": {level: 1.0 if level == marks_level else 0.0 for level in _FUZZY_LEVELS},
            "attendance": {level: 1.0 if level == attendance_level else 0.0 for level in _FUZZY_LEVELS},
            "assignments": {level: 1.0 if level == assignments_level else 0.0 for level in _FUZZY_LEVELS},
        }
        strengths = self._apply_rules(fuzzified)
        score = self._defuzzify(strengths)
        label = self._label_from_score(score, strengths)
        return EvaluationResult(score=round(score, 2), label=label, details=strengths)


def evaluate_student(marks: float, attendance: float, assignments: float) -> EvaluationResult:
    """Helper for one-off evaluations."""
    return FuzzyStudentEvaluator().evaluate(marks, attendance, assignments)


def evaluate_student_fuzzy(marks: str, attendance: str, assignments: str) -> EvaluationResult:
    """Helper for one-off evaluations using fuzzy linguistic levels."""
    return FuzzyStudentEvaluator().evaluate_fuzzy(marks, attendance, assignments)


def _build_output_lines(result: EvaluationResult) -> str:
    lines = [
        f"Defuzzified score: {result.score:.2f}/100",
        f"Performance label: {result.label.capitalize()}",
        "Rule activation strengths:",
    ]
    for label, strength in result.details.items():
        lines.append(f" - {label.capitalize():<9}: {strength:.2f}")
    return "\n".join(lines)


def _evaluate_from_strings(marks_text: str, attendance_text: str, assignments_text: str) -> str:
    try:
        marks = float(marks_text)
        attendance = float(attendance_text)
        assignments = float(assignments_text)
    except ValueError as exc:
        return f"Invalid numeric input: {exc}"

    try:
        result = evaluate_student(marks, attendance, assignments)
    except ValueError as exc:
        return str(exc)
    return _build_output_lines(result)


def _evaluate_fuzzy_from_strings(marks_text: str, attendance_text: str, assignments_text: str) -> str:
    try:
        result = evaluate_student_fuzzy(marks_text, attendance_text, assignments_text)
    except ValueError as exc:
        return str(exc)
    return _build_output_lines(result)


def _run_tkinter_ui() -> None:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Fuzzy Student Evaluator")
    root.resizable(False, False)

    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

    numeric_tab = tk.Frame(notebook, padx=8, pady=8)
    fuzzy_tab = tk.Frame(notebook, padx=8, pady=8)
    notebook.add(numeric_tab, text="Numerical Input")
    notebook.add(fuzzy_tab, text="Categorical Input")

    tk.Label(numeric_tab, text="Marks (0-100):").grid(row=0, column=0, sticky="w", pady=(0, 6))
    marks_entry = tk.Entry(numeric_tab, width=16)
    marks_entry.grid(row=0, column=1, sticky="w", pady=(0, 6))

    tk.Label(numeric_tab, text="Attendance (0-100):").grid(row=1, column=0, sticky="w", pady=(0, 6))
    attendance_entry = tk.Entry(numeric_tab, width=16)
    attendance_entry.grid(row=1, column=1, sticky="w", pady=(0, 6))

    tk.Label(numeric_tab, text="Assignments (0-100):").grid(row=2, column=0, sticky="w", pady=(0, 10))
    assignments_entry = tk.Entry(numeric_tab, width=16)
    assignments_entry.grid(row=2, column=1, sticky="w", pady=(0, 10))

    numeric_output_text = tk.Text(numeric_tab, width=48, height=8, wrap="word")
    numeric_output_text.grid(row=4, column=0, columnspan=2, sticky="we")

    def on_evaluate_numeric() -> None:
        output = _evaluate_from_strings(
            marks_entry.get(),
            attendance_entry.get(),
            assignments_entry.get(),
        )
        numeric_output_text.delete("1.0", tk.END)
        numeric_output_text.insert("1.0", output)

    evaluate_numeric_button = tk.Button(numeric_tab, text="Evaluate", command=on_evaluate_numeric)
    evaluate_numeric_button.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 10))

    allowed = ", ".join(_FUZZY_LEVELS)
    tk.Label(fuzzy_tab, text=f"Marks ({allowed}):").grid(row=0, column=0, sticky="w", pady=(0, 6))
    fuzzy_marks_entry = tk.Entry(fuzzy_tab, width=16)
    fuzzy_marks_entry.grid(row=0, column=1, sticky="w", pady=(0, 6))

    tk.Label(fuzzy_tab, text=f"Attendance ({allowed}):").grid(row=1, column=0, sticky="w", pady=(0, 6))
    fuzzy_attendance_entry = tk.Entry(fuzzy_tab, width=16)
    fuzzy_attendance_entry.grid(row=1, column=1, sticky="w", pady=(0, 6))

    tk.Label(fuzzy_tab, text=f"Assignments ({allowed}):").grid(row=2, column=0, sticky="w", pady=(0, 10))
    fuzzy_assignments_entry = tk.Entry(fuzzy_tab, width=16)
    fuzzy_assignments_entry.grid(row=2, column=1, sticky="w", pady=(0, 10))

    fuzzy_output_text = tk.Text(fuzzy_tab, width=48, height=8, wrap="word")
    fuzzy_output_text.grid(row=4, column=0, columnspan=2, sticky="we")

    def on_evaluate_fuzzy() -> None:
        output = _evaluate_fuzzy_from_strings(
            fuzzy_marks_entry.get(),
            fuzzy_attendance_entry.get(),
            fuzzy_assignments_entry.get(),
        )
        fuzzy_output_text.delete("1.0", tk.END)
        fuzzy_output_text.insert("1.0", output)

    evaluate_fuzzy_button = tk.Button(fuzzy_tab, text="Evaluate", command=on_evaluate_fuzzy)
    evaluate_fuzzy_button.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 10))

    root.mainloop()


def _cli() -> None:
    mode = input("Choose input mode ([n]umerical/[f]uzzy): ").strip().lower()

    if mode in {"n", "numerical", "numeric", "number"}:
        try:
            marks = float(input("Enter marks (0-100): "))
            attendance = float(input("Enter attendance (0-100): "))
            assignments = float(input("Enter assignments (0-100): "))
        except ValueError as exc:
            raise SystemExit(f"Invalid numeric input: {exc}") from exc

        try:
            result = evaluate_student(marks, attendance, assignments)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    elif mode in {"f", "fuzzy"}:
        allowed = ", ".join(_FUZZY_LEVELS)
        try:
            marks = input(f"Enter marks level ({allowed}): ")
            attendance = input(f"Enter attendance level ({allowed}): ")
            assignments = input(f"Enter assignments level ({allowed}): ")
            result = evaluate_student_fuzzy(marks, attendance, assignments)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        raise SystemExit("Invalid mode selection. Choose numerical or fuzzy.")

    for line in _build_output_lines(result).splitlines():
        print(line)


if __name__ == "__main__":
    try:
        _run_tkinter_ui()
    except Exception:
        _cli()
