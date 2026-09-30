"""Check genetic invariants, probability endpoints and independent copies."""

from random import Random
import unittest

from cflp.data import load_instance
from cflp.feasibility import check_feasibility
from cflp.operators import crossover, mutate


class OperatorTests(unittest.TestCase):
    def test_single_cut_swaps_complementary_tails(self):
        a, b = [0] * 6, [1] * 6
        x, y = crossover(a, b, 1, Random(42))
        cut = x.index(1)
        self.assertGreater(cut, 0)
        self.assertLess(cut, 6)
        self.assertEqual(x, a[:cut] + b[cut:])
        self.assertEqual(y, b[:cut] + a[cut:])
        self.assertEqual((a, b), ([0] * 6, [1] * 6))

    def test_no_crossover_still_returns_independent_lists(self):
        a = [0, 1, 2]
        x, y = crossover(a, a, 0, Random(1))
        x[0] = 2
        self.assertEqual(a, [0, 1, 2])
        self.assertEqual(y, a)
        self.assertIsNot(y, a)

    def test_one_gene_crossover(self):
        self.assertEqual(crossover([0], [1], 1, Random(1)), ([0], [1]))

    def test_mutation_probability_endpoints(self):
        original = [0, 1, 2, 3]
        unchanged = mutate(original, 4, 0, Random(1))
        self.assertEqual(unchanged, original)
        self.assertIsNot(unchanged, original)
        changed = mutate(original, 4, 1, Random(1))
        self.assertTrue(all(old != new and 0 <= new < 4 for old, new in zip(original, changed)))
        self.assertEqual(original, [0, 1, 2, 3])
        self.assertEqual(mutate([0, 0], 1, 1, Random(1)), [0, 0])

    def test_invalid_inputs(self):
        for probability in (-0.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                crossover([0], [1], probability, Random(1))
            with self.assertRaises(ValueError):
                mutate([0], 2, probability, Random(1))
        with self.assertRaises(ValueError):
            crossover([0], [0, 1], 1, Random(1))
        with self.assertRaises(ValueError):
            mutate([2], 2, 1, Random(1))

    def test_cap101_children_remain_feasible_and_reproducible(self):
        instance = load_instance("cap101")
        def produce(seed):
            rng = Random(seed)
            children = crossover([0] * 50, [10] * 50, 0.9, rng)
            return [mutate(child, 25, 0.02, rng) for child in children]
        children = produce(21)
        self.assertEqual(children, produce(21))
        for child in children:
            self.assertEqual(len(child), 50)
            check_feasibility(instance, child)


if __name__ == "__main__":
    unittest.main()
