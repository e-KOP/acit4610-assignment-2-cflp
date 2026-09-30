"""Distinguish data integrity, necessary conditions and actual feasibility."""

import unittest
from cflp.data import Instance, load_instance
from cflp.feasibility import necessary_feasibility_issues
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility


# A complete indivisible allocation, independently checked against both files.
SMALL_ASSIGNMENT = (
    2, 3, 3, 2, 3, 3, 2, 2, 3, 3, 1, 3, 1, 3, 3, 3, 3, 2, 3, 3,
    0, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 0, 3, 0, 1, 2, 3, 3,
    0, 2, 3, 3, 2, 3, 3, 3, 2, 3,
)


class NecessaryFeasibilityTests(unittest.TestCase):
    def test_small_benchmarks_have_complete_feasible_assignments(self):
        for name in ("cap61", "cap62"):
            with self.subTest(name=name):
                instance = load_instance(name)
                self.assertEqual(necessary_feasibility_issues(instance), ())
                loads = check_feasibility(instance, SMALL_ASSIGNMENT)
                self.assertEqual(loads[:4], (14997, 15000, 14993, 13278))
                self.assertEqual(sum(loads), sum(instance.demands))
                self.assertEqual(len(evaluate(instance, SMALL_ASSIGNMENT)), 2)

    def test_individually_valid_customers_can_overload_a_facility_together(self):
        for name in ("cap61", "cap62"):
            with self.subTest(name=name):
                instance = load_instance(name)
                self.assertLessEqual(instance.demands[10], instance.capacities[0])
                self.assertLessEqual(instance.demands[33], instance.capacities[0])
                self.assertGreater(instance.demands[10] + instance.demands[33], instance.capacities[0])
                candidate = list(SMALL_ASSIGNMENT)
                candidate[10] = candidate[33]
                with self.assertRaisesRegex(ValueError, "overloaded"):
                    evaluate(instance, candidate)

    def test_customer_larger_than_every_facility_is_rejected(self):
        instance = Instance("oversized_customer", (5, 5), (1, 1), (6,), ((1,), (1,)))
        issues = necessary_feasibility_issues(instance)
        self.assertEqual(len(issues), 1)
        self.assertIn("Customer 0", issues[0])

    def test_total_capacity_shortage(self):
        instance = Instance("capacity_shortage", (5,), (1,), (3, 3), ((1, 1),))
        self.assertEqual(necessary_feasibility_issues(instance), (
            "Total demand exceeds total facility capacity.",
        ))

    def test_passing_checks_does_not_prove_feasibility(self):
        # Three indivisible demands of 4 do not fit in two facilities of 6.
        instance = Instance("packing_counterexample", (6, 6), (1, 1), (4, 4, 4),
                            ((1, 1, 1), (1, 1, 1)))
        self.assertEqual(necessary_feasibility_issues(instance), ())


if __name__ == "__main__":
    unittest.main()
