"""Check normalized neighbor gaps and the strict rank-first selection rule."""

from math import inf
from random import Random
import unittest

from cflp.nsga2 import crowding_distance, rank_and_crowding, tournament_winner


class SelectionTests(unittest.TestCase):
    def test_hand_calculated_distances(self):
        points = [(1, 10), (2, 7), (5, 4), (9, 1)]
        distances = crowding_distance(points, [0, 1, 2, 3])
        self.assertEqual(distances[0], inf)
        self.assertEqual(distances[3], inf)
        self.assertAlmostEqual(distances[1], 7 / 6)
        self.assertAlmostEqual(distances[2], 37 / 24)

    def test_scaling_and_translation_leave_distances_unchanged(self):
        points = [(1, 10), (2, 7), (5, 4), (9, 1)]
        scaled = [(100 * x + 20, 3 * y + 8) for x, y in points]
        front = [3, 1, 0, 2]
        self.assertEqual(crowding_distance(points, front), crowding_distance(scaled, front))
        self.assertEqual(front, [3, 1, 0, 2])

    def test_constant_objectives_and_small_fronts(self):
        self.assertEqual(crowding_distance([], []), {})
        self.assertEqual(crowding_distance([(1, 1)], [0]), {0: inf})
        self.assertEqual(crowding_distance([(1, 1)] * 3, [0, 1, 2]), {0: 0, 1: 0, 2: 0})
        # Constant first objective must not cause division by zero.
        self.assertEqual(crowding_distance([(1, 1), (1, 2), (1, 3)], [0, 1, 2]),
                         {0: inf, 1: 1, 2: inf})

    def test_ranks_and_distances_use_original_indices(self):
        fronts, ranks, distances = rank_and_crowding([(4, 5), (1, 4), (2, 3), (3, 4)])
        self.assertEqual(fronts, [[1, 2], [3], [0]])
        self.assertEqual(ranks, [3, 1, 1, 2])
        self.assertEqual(distances, [inf] * 4)

    def test_rank_precedes_distance(self):
        self.assertEqual(tournament_winner(0, 1, [1, 2], [0, inf], Random(1)), 0)
        self.assertEqual(tournament_winner(0, 1, [2, 1], [inf, 0], Random(1)), 1)

    def test_same_rank_prefers_larger_distance_and_ties_are_reproducible(self):
        self.assertEqual(tournament_winner(0, 1, [1, 1], [1, 2], Random(1)), 1)
        a, b = Random(42), Random(42)
        first = [tournament_winner(0, 1, [1, 1], [inf, inf], a) for _ in range(20)]
        second = [tournament_winner(0, 1, [1, 1], [inf, inf], b) for _ in range(20)]
        self.assertEqual(first, second)
        self.assertEqual(set(first), {0, 1})


if __name__ == "__main__":
    unittest.main()
