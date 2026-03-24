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
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


def _validate_percent(value: float, name: str) -> None:
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100. Got {value}.")


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
                "medium": _triangular(marks, 45, 65, 80),
                "high": _trapezoidal(marks, 70, 85, 100, 100),
            },
            "attendance": {
                "low": _trapezoidal(attendance, 0, 0, 50, 65),
                "medium": _triangular(attendance, 60, 75, 90),
                "high": _trapezoidal(attendance, 80, 90, 100, 100),
            },
            "assignments": {
                "low": _trapezoidal(assignments, 0, 0, 45, 60),
                "medium": _triangular(assignments, 50, 65, 80),
                "high": _trapezoidal(assignments, 70, 85, 100, 100),
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
            "average": lambda v: _triangular(v, 40, 55, 65),
            "good": lambda v: _triangular(v, 60, 75, 85),
            "excellent": lambda v: _trapezoidal(v, 80, 90, 100, 100),
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
        # Evaluate memberships at the crisp score and pick the highest.
        memberships = {
            "poor": min(strengths["poor"], _trapezoidal(score, 0, 0, 35, 50)),
            "average": min(strengths["average"], _triangular(score, 40, 55, 65)),
            "good": min(strengths["good"], _triangular(score, 60, 75, 85)),
            "excellent": min(strengths["excellent"], _trapezoidal(score, 80, 90, 100, 100)),
        }
        return max(memberships.items(), key=lambda item: (item[1], item[0]))[0]

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


def evaluate_student(marks: float, attendance: float, assignments: float) -> EvaluationResult:
    """Helper for one-off evaluations."""
    return FuzzyStudentEvaluator().evaluate(marks, attendance, assignments)


def _cli() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Fuzzy Logic–Based Student Evaluation System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--marks", type=float, required=True, help="Exam/overall marks (0-100)")
    parser.add_argument("--attendance", type=float, required=True, help="Attendance percentage (0-100)")
    parser.add_argument("--assignments", type=float, required=True, help="Assignment performance (0-100)")
    args = parser.parse_args()

    result = evaluate_student(args.marks, args.attendance, args.assignments)
    print(f"Defuzzified score: {result.score:.2f}/100")
    print(f"Performance label: {result.label.capitalize()}")
    print("Rule activation strengths:")
    for label, strength in result.details.items():
        print(f" - {label.capitalize():<9}: {strength:.2f}")


if __name__ == "__main__":
    _cli()
