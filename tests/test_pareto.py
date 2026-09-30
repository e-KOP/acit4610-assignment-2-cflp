"""Hand-checkable fronts, equal values, ties, and malformed objectives."""

import unittest
from cflp.pareto import dominates, nondominated_indices, nondominated_sort


class ParetoTests(unittest.TestCase):
    def test_dominance_requires_one_strict_improvement(self):
        self.assertTrue(dominates((1, 2), (1, 3)))
        self.assertFalse(dominates((1, 2), (1, 2)))
        self.assertFalse(dominates((1, 3), (2, 2)))

    def test_layers_with_duplicates_and_tradeoffs(self):
        points = [(1, 4), (2, 3), (3, 4), (4, 5), (2, 3)]
        self.assertEqual(nondominated_sort(points), [[0, 1, 4], [2], [3]])
        self.assertEqual(nondominated_indices(points), [0, 1, 4])

    def test_empty_and_single_point(self):
        self.assertEqual(nondominated_sort([]), [])
        self.assertEqual(nondominated_indices([]), [])
        self.assertEqual(nondominated_sort([(1, 2)]), [[0]])

    def test_invalid_single_point_is_rejected(self):
        for point in ((1, float("nan")), (1, float("inf")), (1, 2, 3)):
            with self.subTest(point=point), self.assertRaises(ValueError):
                nondominated_sort([point])


if __name__ == "__main__":
    unittest.main()
