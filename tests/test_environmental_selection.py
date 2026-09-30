"""Verify elitist whole-front acceptance and crowding-based truncation."""

from random import Random
import unittest

from cflp.nsga2 import environmental_selection


class EnvironmentTests(unittest.TestCase):
    def test_complete_fronts_have_priority_over_later_boundaries(self):
        points = [(1, 4), (2, 3), (3, 4), (4, 5)]
        self.assertEqual(environmental_selection(points, 2, Random(1)), [0, 1])
        self.assertEqual(environmental_selection(points, 3, Random(1)), [0, 1, 2])

    def test_partial_front_preserves_boundaries_then_larger_gap(self):
        points = [(1, 10), (2, 7), (5, 4), (9, 1)]
        original = list(points)
        selected = environmental_selection(points, 3, Random(1))
        self.assertEqual(set(selected), {0, 2, 3})
        self.assertEqual(points, original)

    def test_duplicates_are_individuals_and_ties_are_seeded(self):
        points = [(1, 1)] * 5
        selected = environmental_selection(points, 3, Random(11))
        self.assertEqual(selected, environmental_selection(points, 3, Random(11)))
        self.assertEqual(len(set(selected)), 3)

    def test_size_boundaries(self):
        self.assertEqual(environmental_selection([], 0, Random(1)), [])
        self.assertEqual(environmental_selection([(1, 2)], 0, Random(1)), [])
        self.assertEqual(environmental_selection([(1, 2)], 1, Random(1)), [0])
        for size in (-1, 2, 0.5, True):
            with self.subTest(size=size), self.assertRaises(ValueError):
                environmental_selection([(1, 2)], size, Random(1))


if __name__ == "__main__":
    unittest.main()
