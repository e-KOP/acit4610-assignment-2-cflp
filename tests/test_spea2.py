"""Tests for SPEA2."""

from random import Random
import unittest

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility
from cflp.pareto import dominates
from cflp.spea2 import (
    calculate_strengths,
    calculate_raw_fitness,
    calculate_density,
    calculate_fitness,
    truncate_archive,
    update_archive,
    tournament_winner,
    run,
)

class SPEA2Tests(unittest.TestCase):

    def test_strengths(self):

        objectives = [
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 3.0),
        ]

        strengths = calculate_strengths(objectives)

        self.assertEqual(
            strengths,
            [2, 1, 0],
        )


    def test_raw_fitness(self):

        objectives = [
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 3.0),
        ]

        strengths = calculate_strengths(
            objectives
        )

        raw_fitness = calculate_raw_fitness(
            objectives,
            strengths,
        )

        self.assertEqual(
            raw_fitness,
            [0, 2, 3],
        )


    def test_density_is_positive(self):

        objectives = [
            (0.1, 0.1),
            (0.2, 0.2),
            (0.8, 0.8),
            (0.9, 0.9),
        ]

        densities = calculate_density(
            objectives
        )

        self.assertEqual(
            len(densities),
            4,
        )

        for density in densities:
            self.assertGreater(
                density,
                0.0,
            )


    def test_tournament_prefers_lower_fitness(self):

        fitness = [
            0.2,
            1.5,
        ]

        winner = tournament_winner(
            0,
            1,
            fitness,
            Random(42),
        )

        self.assertEqual(
            winner,
            0,
        )


    def test_tournament_tie_is_reproducible(self):

        fitness = [
            0.5,
            0.5,
        ]

        first = tournament_winner(
            0,
            1,
            fitness,
            Random(42),
        )

        second = tournament_winner(
            0,
            1,
            fitness,
            Random(42),
        )

        self.assertEqual(
            first,
            second,
        )


    def test_archive_keeps_nondominated_solutions(self):

        population = [
            [0],
            [1],
            [2],
        ]

        objectives = [
            (1.0, 3.0),
            (2.0, 2.0),
            (3.0, 1.0),
        ]

        class FakeInstance:
            fixed_costs = [1.0, 1.0, 1.0]
            allocation_costs = [
                [3.0],
                [2.0],
                [1.0],
            ]
            n_customers = 1

        archive, archive_objectives, archive_fitness = update_archive(
            FakeInstance(),
            population,
            objectives,
            archive_size=3,
        )

        self.assertEqual(
            len(archive),
            3,
        )

        self.assertEqual(
            len(archive_objectives),
            3,
        )


    def test_archive_truncates_to_required_size(self):

        population = [
            [0],
            [1],
            [2],
            [3],
        ]

        objectives = [
            (1.0, 4.0),
            (2.0, 3.0),
            (3.0, 2.0),
            (4.0, 1.0),
        ]

        class FakeInstance:
            fixed_costs = [1.0, 1.0, 1.0, 1.0]
            allocation_costs = [
                [4.0],
                [3.0],
                [2.0],
                [1.0],
            ]
            n_customers = 1

        archive, archive_objectives, archive_fitness = update_archive(
            FakeInstance(),
            population,
            objectives,
            archive_size=2,
        )

        self.assertEqual(
            len(archive),
            2,
        )

        self.assertEqual(
            len(archive_objectives),
            2,
        )


    def test_complete_run_respects_budget(self):

        instance = load_instance(
            "cap61"
        )

        config = {
            "population_size": 20,
            "crossover_probability_per_pair": 0.9,
            "mutation_probability_per_gene": 0.02,
            "max_objective_evaluations": 200,
            "archive_size_rule":
                "equal_to_population_size",
        }

        result = run(
            instance,
            config,
            42,
        )

        self.assertEqual(
            result["evaluations"],
            200,
        )

        self.assertEqual(
            result["algorithm"],
            "spea2",
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertGreater(
            len(result["objectives"]),
            0,
        )


    def test_complete_run_is_reproducible(self):

        instance = load_instance(
            "cap61"
        )

        config = {
            "population_size": 20,
            "crossover_probability_per_pair": 0.9,
            "mutation_probability_per_gene": 0.02,
            "max_objective_evaluations": 200,
            "archive_size_rule":
                "equal_to_population_size",
        }

        first = run(
            instance,
            config,
            42,
        )

        second = run(
            instance,
            config,
            42,
        )

        self.assertEqual(
            first["objectives"],
            second["objectives"],
        )


    def test_total_fitness_matches_raw_plus_density(self):

        class FakeInstance:
            fixed_costs = [1.0, 1.0, 1.0]
            allocation_costs = [
                [1.0],
                [2.0],
                [3.0],
            ]
            n_customers = 1

        objectives = [
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 3.0),
        ]

        (
            strengths,
            raw_fitness,
            densities,
            total_fitness,
            normalized_objectives,
        ) = calculate_fitness(
            FakeInstance(),
            objectives,
        )

        self.assertEqual(
            strengths,
            [2, 1, 0],
        )

        self.assertEqual(
            raw_fitness,
            [0, 2, 3],
        )

        for i in range(3):
            self.assertAlmostEqual(
                total_fitness[i],
                raw_fitness[i] + densities[i],
            )

    def test_archive_fills_with_best_dominated_solutions(self):

        population = [
            [0],
            [1],
            [2],
            [3],
        ]

        objectives = [
            (1.0, 1.0),
            (2.0, 2.0),
            (3.0, 3.0),
            (4.0, 4.0),
        ]

        class FakeInstance:
            fixed_costs = [
                1.0,
                1.0,
                1.0,
                1.0,
            ]
            allocation_costs = [
                [1.0],
                [2.0],
                [3.0],
                [4.0],
            ]
            n_customers = 1

        (
            archive,
            archive_objectives,
            archive_fitness,
        ) = update_archive(
            FakeInstance(),
            population,
            objectives,
            archive_size=3,
        )

        self.assertEqual(
            archive_objectives,
            [
                (1.0, 1.0),
                (2.0, 2.0),
                (3.0, 3.0),
            ],
        )

    def test_complete_run_returns_feasible_nondominated_solutions(self):

        instance = load_instance(
            "cap61"
        )

        config = {
            "population_size": 20,
            "crossover_probability_per_pair": 0.9,
            "mutation_probability_per_gene": 0.02,
            "max_objective_evaluations": 200,
            "archive_size_rule":
                "equal_to_population_size",
        }

        result = run(
            instance,
            config,
            42,
        )

        population = result["population"]
        objectives = result["objectives"]

        self.assertEqual(
            len(population),
            len(objectives),
        )

        for individual, objective in zip(
            population,
            objectives,
        ):
            check_feasibility(
                instance,
                individual,
            )

            self.assertEqual(
                evaluate(
                    instance,
                    individual,
                ),
                objective,
            )

        for i in range(len(objectives)):
            for j in range(len(objectives)):

                if i == j:
                    continue

                self.assertFalse(
                    dominates(
                        objectives[j],
                        objectives[i],
                    )
                )



if __name__ == "__main__":
    unittest.main()