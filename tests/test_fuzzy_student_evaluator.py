import math
from unittest.mock import patch
import unittest

from fuzzy_student_evaluator import (
    FuzzyStudentEvaluator,
    _cli,
    _evaluate_from_strings,
    evaluate_student,
    evaluate_student_fuzzy,
)


class TestFuzzyStudentEvaluator(unittest.TestCase):
    def test_rejects_out_of_range_inputs(self):
        evaluator = FuzzyStudentEvaluator()
        with self.assertRaises(ValueError):
            evaluator.evaluate(-1, 50, 50)
        with self.assertRaises(ValueError):
            evaluator.evaluate(50, 101, 50)
        with self.assertRaises(ValueError):
            evaluator.evaluate(50, 50, 200)

    def test_high_performance_is_classified_excellent(self):
        result = evaluate_student(marks=82, attendance=90, assignments=78)
        self.assertEqual(result.label, "excellent")
        self.assertTrue(math.isclose(result.score, 87.39, rel_tol=0, abs_tol=0.75))
        self.assertGreater(result.details["excellent"], result.details["good"])

    def test_low_performance_is_classified_poor(self):
        result = evaluate_student(marks=25, attendance=30, assignments=20)
        self.assertEqual(result.label, "poor")
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 40)
        self.assertGreaterEqual(
            result.details["poor"],
            max(result.details["average"], result.details["good"], result.details["excellent"]),
        )

    def test_cli_interactive_prompts_with_valid_inputs_produces_expected_output(self):
        with patch("builtins.input", side_effect=["n", "82", "90", "78"]), patch("builtins.print") as mocked_print:
            _cli()
        output_lines = [call.args[0] for call in mocked_print.call_args_list]
        self.assertTrue(any(line.startswith("Defuzzified score: ") and line.endswith("/100") for line in output_lines))
        self.assertIn("Performance label: Excellent", output_lines)

    def test_cli_interactive_rejects_non_numeric_input(self):
        with patch("builtins.input", side_effect=["n", "abc"]), self.assertRaises(SystemExit) as ctx:
            _cli()
        self.assertIn("Invalid numeric input", str(ctx.exception))

    def test_cli_interactive_supports_fuzzy_inputs(self):
        with patch("builtins.input", side_effect=["f", "high", "high", "high"]), patch("builtins.print") as mocked_print:
            _cli()
        output_lines = [call.args[0] for call in mocked_print.call_args_list]
        self.assertIn("Performance label: Excellent", output_lines)

    def test_cli_interactive_rejects_unknown_mode(self):
        with patch("builtins.input", side_effect=["x"]), self.assertRaises(SystemExit) as ctx:
            _cli()
        self.assertIn("Invalid mode selection", str(ctx.exception))

    def test_evaluate_from_strings_formats_output_for_valid_values(self):
        output = _evaluate_from_strings("82", "90", "78")
        self.assertIn("Defuzzified score:", output)
        self.assertIn("Performance label: Excellent", output)
        self.assertIn("Rule activation strengths:", output)

    def test_evaluate_from_strings_handles_invalid_numeric_input(self):
        output = _evaluate_from_strings("abc", "90", "78")
        self.assertIn("Invalid numeric input", output)

    def test_evaluate_student_fuzzy_supports_linguistic_levels(self):
        result = evaluate_student_fuzzy("high", "high", "high")
        self.assertEqual(result.label, "excellent")
        self.assertGreater(result.details["excellent"], 0)


if __name__ == "__main__":
    unittest.main()
