"""Numerical and final-generation regression checks for SPEA2."""

import unittest
from unittest.mock import patch
from cflp import spea2, offspring
from cflp.data import Instance, load_instance
from cflp.evaluation import evaluate


class SPEA2BoundaryTests(unittest.TestCase):
    def test_second_nearest_neighbour_is_used(self):
        self.assertEqual(spea2.calculate_density([(0,0),(3,0),(0,4),(3,4)]),[1/6]*4)

    def test_truncation_preserves_extremes(self):
        self.assertEqual(spea2.truncate_archive([0,1,2,3],[(0,5),(1,4),(4,1),(5,0)],2),[0,3])
        self.assertEqual(spea2.truncate_archive([0,1,2],[(0,2),(0,2),(2,0)],2),[1,2])

    def test_last_offspring_is_in_final_archive(self):
        instance=Instance('final_child',(1,1),(10,1),(1,),((10,),(1,)))
        config=dict(population_size=2,crossover_probability_per_pair=.9,
                    mutation_probability_per_gene=.02,max_objective_evaluations=3)
        with patch.object(spea2,'initialize_population',return_value=[[0],[0]]), \
             patch.object(spea2,'generate_offspring',return_value=([[1]],[(1,1)])):
            result=spea2.run(instance,config,0)
        self.assertEqual(result['population'],[[1]])
        self.assertEqual(result['objectives'],[(1,1)])

    def test_count_actual_calls_at_budget_boundaries(self):
        config=dict(population_size=6,crossover_probability_per_pair=.9,mutation_probability_per_gene=.02)
        for budget in (6,7,19):
            with self.subTest(budget=budget), \
                 patch.object(spea2,'evaluate',wraps=evaluate) as initial, \
                 patch.object(offspring,'evaluate',wraps=evaluate) as children:
                result=spea2.run(load_instance('cap61'),{**config,'max_objective_evaluations':budget},0)
                self.assertEqual(initial.call_count+children.call_count,budget)
                self.assertEqual(result['evaluations'],budget)


if __name__=='__main__':
    unittest.main()
