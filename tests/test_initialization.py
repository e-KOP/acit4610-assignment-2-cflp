"""Tests for shared population initialization."""

from random import Random
import unittest

from cflp.data import load_instance
from cflp.feasibility import check_feasibility
from cflp.initialization import initialize_population


class InitializationTests(unittest.TestCase):

    def test_population_is_feasible(self):
        instance = load_instance("cap61")

        population = initialize_population(
            instance,
            20,
            Random(42),
        )

        self.assertEqual(len(population), 20)

        for individual in population:
            check_feasibility(instance, individual)

    def test_cap62_is_feasible(self):
        instance = load_instance("cap62")

        population = initialize_population(
            instance,
            20,
            Random(42),
        )

        for individual in population:
            check_feasibility(instance, individual)

    def test_same_seed_is_reproducible(self):
        instance = load_instance("cap61")

        first = initialize_population(
            instance,
            10,
            Random(7),
        )

        second = initialize_population(
            instance,
            10,
            Random(7),
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()