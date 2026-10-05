"""Integration and hand-calculated checks for the executable experiment pipeline."""

import json
from pathlib import Path
from random import Random
import tempfile
import unittest
from unittest.mock import patch

from cflp import nsga2, offspring
from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.initialization import initialize_population
from cflp.metrics import hypervolume_2d, calculate_metrics
from cflp.experiments import run_experiment, summarize_directory


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.instance = load_instance("cap61")
        self.config = dict(population_size=6, crossover_probability_per_pair=.9,
                           mutation_probability_per_gene=.02, max_objective_evaluations=19)

    def test_exact_budget_feasibility_and_reproducibility(self):
        for budget in (6, 7, 18, 19):
            config = {**self.config, "max_objective_evaluations": budget}
            with patch.object(nsga2, "evaluate", wraps=evaluate) as initial, \
                 patch.object(offspring, "evaluate", wraps=evaluate) as children:
                result = nsga2.run(self.instance, config, 3)
                self.assertEqual(initial.call_count + children.call_count, budget)
            self.assertEqual(result["evaluations"], budget)
            self.assertEqual(result, nsga2.run(self.instance, config, 3))
            for assignment, objectives in zip(result["population"], result["objectives"]):
                self.assertEqual(evaluate(self.instance, assignment), objectives)

    def test_initialization_does_not_limit_facilities_to_low_ids(self):
        instance = load_instance("cap101")
        population = initialize_population(instance, 100, Random(0))
        self.assertEqual({i for a in population for i in a}, set(range(25)))

    def test_invalid_budget_and_probabilities_fail_even_without_evolution(self):
        for key, value in [("max_objective_evaluations", 6.5),
                           ("max_objective_evaluations", True),
                           ("crossover_probability_per_pair", float("nan")),
                           ("mutation_probability_per_gene", 1.1)]:
            with self.assertRaises(ValueError):
                nsga2.run(self.instance, {**self.config, "max_objective_evaluations": 6, key: value}, 0)

    def test_bounded_repair_failure_and_no_evaluation(self):
        parents = initialize_population(self.instance, 2, Random(0))
        with patch.object(offspring, "repair_assignment", side_effect=ValueError("stalled")) as repair, \
             patch.object(offspring, "evaluate") as evaluation:
            with self.assertRaises(ValueError):
                offspring.generate_offspring(self.instance, parents, .9, .02, Random(0), max_attempts_per_child=3)
            self.assertEqual(repair.call_count, 6)
            evaluation.assert_not_called()

    def test_hypervolume_rectangle_union(self):
        # Rectangles have area 8 and 9, overlap 6: union 11.
        self.assertEqual(hypervolume_2d([(1, 3), (2, 2), (1, 3), (3, 4)], (5, 5)), 11)
        self.assertEqual(hypervolume_2d([], (5, 5)), 0)
        with self.assertRaises(ValueError):
            hypervolume_2d([(5, 1)], (5, 5))
        metrics = calculate_metrics(self.instance, [(30000, 1864204.2125)] * 2)
        self.assertEqual(metrics["nd"], 1)
        self.assertGreater(metrics["hv"], 0)

    def test_saved_results_resume_and_summary(self):
        job = dict(instance="cap61", algorithm="nsga2", configuration="test", seed=0, parameters=self.config)
        with tempfile.TemporaryDirectory() as directory:
            result = run_experiment(job, directory)
            resumed = run_experiment(job, directory, resume=True)
            self.assertEqual(resumed["signature"], result["signature"])
            self.assertEqual(resumed["runtime_seconds"], result["runtime_seconds"])
            with self.assertRaises(ValueError):
                run_experiment({**job, "parameters": {**self.config, "max_objective_evaluations": 20}}, directory, resume=True)
            run_experiment({**job, "seed": 1}, directory)
            rows = summarize_directory(directory)
            self.assertEqual(rows[0]["runs"], 2)
            self.assertIsNotNone(rows[0]["hv_sd"])
            self.assertTrue((Path(directory) / "plots/cap61__test.svg").exists())
            self.assertEqual(json.loads((Path(directory)/"summary_status.json").read_text())["failed"], 0)

    def test_failed_runs_are_recorded(self):
        job = dict(instance="cap61", algorithm="nsga2", configuration="test", seed=0, parameters=self.config)
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("cflp.experiments.ALGORITHMS", {"nsga2": lambda *args: (_ for _ in ()).throw(ValueError("failure"))}):
            with self.assertRaises(ValueError):
                run_experiment(job, directory)
            self.assertEqual(summarize_directory(directory), [])
            status=json.loads((Path(directory)/"summary_status.json").read_text())
            self.assertEqual(status["failed"], 1)


class RepairRegressionTests(unittest.TestCase):
    def test_documented_repair_changes_one_gene_without_mutating_input(self):
        from cflp.repair import repair_assignment
        instance = load_instance("cap61")
        feasible = [2,3,3,2,3,3,2,2,3,3,1,3,1,3,3,3,3,2,3,3,0,3,3,3,3,3,1,3,3,3,3,3,3,0,3,0,1,2,3,3,0,2,3,3,2,3,3,3,2,3]
        overloaded = feasible.copy()
        overloaded[10] = 0
        repaired = repair_assignment(instance, overloaded)
        self.assertEqual(overloaded[10], 0)
        self.assertEqual(repaired, feasible)
        self.assertEqual(evaluate(instance, repaired), (30000, 1864204.2125))


class IntegrationContractTests(unittest.TestCase):
    def test_second_algorithm_uses_runner_without_special_case(self):
        def adapter(instance, config, seed):
            result = nsga2.run(instance, config, seed)
            result['algorithm'] = 'contract_test'
            return result
        config = dict(population_size=4, crossover_probability_per_pair=.9,
                      mutation_probability_per_gene=.02, max_objective_evaluations=9)
        job = dict(instance='cap61', algorithm='nsga2', configuration='test', seed=0, parameters=config)
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict('cflp.experiments.ALGORITHMS', {'contract_test': adapter}):
            run_experiment(job, directory)
            run_experiment({**job, 'algorithm': 'contract_test'}, directory)
            rows = summarize_directory(directory)
            self.assertEqual(len(rows), 2)
            svg = (Path(directory)/'plots/cap61__test.svg').read_text()
            self.assertIn('contract_test', svg)
            self.assertIn('nsga2', svg)

    def test_mixed_protocols_are_rejected(self):
        config = dict(population_size=4, crossover_probability_per_pair=.9,
                      mutation_probability_per_gene=.02, max_objective_evaluations=9)
        job = dict(instance='cap61', algorithm='nsga2', configuration='test', seed=0, parameters=config)
        with tempfile.TemporaryDirectory() as directory:
            run_experiment(job, directory)
            run_experiment({**job, 'seed': 1, 'parameters': {**config, 'max_objective_evaluations': 10}}, directory)
            with self.assertRaises(ValueError):
                summarize_directory(directory)


if __name__ == "__main__":
    unittest.main()
