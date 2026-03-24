import math
import unittest

from fuzzy_student_evaluator import FuzzyStudentEvaluator, evaluate_student


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


if __name__ == "__main__":
    unittest.main()
