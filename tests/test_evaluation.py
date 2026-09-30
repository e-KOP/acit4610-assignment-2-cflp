"""Hand-calculated cases check business constraints and objective semantics."""

import unittest
from cflp.data import Instance
from cflp.evaluation import evaluate
from cflp.feasibility import facility_loads
from cflp.representation import opened_facilities


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.instance = Instance(
            "teaching_example", (12, 7, 5), (100, 60, 70), (4, 3, 5),
            ((24, 18, 30), (8, 6, 40), (30, 24, 10)),
        )

    def test_boundary_capacity_and_costs(self):
        assignment = [1, 1, 2]
        self.assertEqual(facility_loads(self.instance, assignment), (0, 7, 5))
        self.assertEqual(opened_facilities(self.instance, assignment), (1, 2))
        self.assertEqual(evaluate(self.instance, assignment), (130, 24))
        self.assertEqual(assignment, [1, 1, 2])

    def test_opening_cost_counted_once_and_no_second_demand_multiplier(self):
        self.assertEqual(evaluate(self.instance, [0, 0, 0]), (100, 72))

    def test_overloaded_solution_has_no_objective_result(self):
        with self.assertRaisesRegex(ValueError, "overloaded"):
            evaluate(self.instance, [1, 1, 1])

    def test_invalid_customer_assignments(self):
        for assignment in ([0, 0], [0, 0, 3], [-1, 0, 0], [0.0, 0, 0], [True, 0, 0]):
            with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                evaluate(self.instance, assignment)


if __name__ == "__main__":
    unittest.main()
