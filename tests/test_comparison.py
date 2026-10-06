"""Hand-calculated inference and cross-algorithm protocol regressions."""

from copy import deepcopy
import unittest
from cflp.protocol import validate_records
from cflp.statistics import paired_permutation_test, holm_adjust, compare_algorithms


def records_and_plan():
    plan = {'instances':['cap61'],'configurations':{'reference':{'population_size':100}},
            'seeds':list(range(10)), 'common':{'max_objective_evaluations':10000}}
    records=[]
    for seed in range(10):
        for algorithm in ('nsga2','spea2'):
            record=dict(instance='cap61', configuration='reference', algorithm=algorithm,
                        status='completed', seed=seed, evaluations=10000,
                        parameters={'population_size':100,'max_objective_evaluations':10000},
                        source_sha256='same-source',data_sha256='same-data',environment={'machine':'same'},
                        initial_population_sha256=f'initial-{seed}',
                        metrics={'hv':.8 if algorithm=='nsga2' else .7,'normalization':{'scale':[1,1]}})
            if algorithm=='spea2':
                record['parameters']['archive_size_rule']='equal_to_population_size'
            records.append(record)
    return records,plan


class ComparisonTests(unittest.TestCase):
    def test_hand_calculated_exact_test(self):
        self.assertEqual(paired_permutation_test([1,2,3],[0,0,0]),.25)
        self.assertEqual(paired_permutation_test([1,1],[1,1]),1)
        self.assertEqual(paired_permutation_test([1,0],[0,1]),1)
        self.assertEqual(paired_permutation_test([1]*10,[0]*10),2/1024)

    def test_holm_adjustment(self):
        self.assertEqual(holm_adjust([.01,.04,.03]),[.03,.06,.06])
        self.assertEqual(holm_adjust([]),[])

    def test_budget_mismatch_across_algorithms(self):
        records,_=records_and_plan()
        records[1]['parameters']['max_objective_evaluations']=20000
        records[1]['evaluations']=20000
        with self.assertRaises(ValueError): validate_records(records)

    def test_source_data_scaling_environment_mismatch(self):
        for key,value in [('source_sha256','other'),('data_sha256','other'),
                          ('environment',{'machine':'different'}),
                          ('metrics',{'hv':.7,'normalization':{'scale':[2,2]}})]:
            with self.subTest(key=key):
                records,_=records_and_plan();records[1][key]=value
                with self.assertRaises(ValueError): validate_records(records)

    def test_initialization_mismatch(self):
        records,_=records_and_plan();records[1]['initial_population_sha256']='different'
        with self.assertRaises(ValueError): validate_records(records)

    def test_complete_paired_comparison(self):
        records,plan=records_and_plan()
        rows,status=compare_algorithms(records,plan)
        self.assertEqual(status['status'],'complete')
        self.assertEqual(status['family_size'],1)
        self.assertAlmostEqual(rows[0]['mean_difference_nsga2_minus_spea2'],.1)
        self.assertEqual(rows[0]['paired_win_fraction_nsga2'],1)
        self.assertTrue(rows[0]['reject_at_0_05'])

    def test_missing_seeds_suppress_inference(self):
        records,plan=records_and_plan()
        rows,status=compare_algorithms(records[:-1],plan)
        self.assertEqual(rows,[])
        self.assertEqual(status['status'],'incomplete')

    def test_missing_initialization_evidence_rejects_pairing(self):
        records,plan=records_and_plan()
        for record in records: record.pop('initial_population_sha256')
        with self.assertRaises(ValueError): compare_algorithms(records,plan)

    def test_saved_parameters_must_match_declared_plan(self):
        records,plan=records_and_plan();plan['common']['max_objective_evaluations']=20000
        with self.assertRaises(ValueError): compare_algorithms(records,plan)

    def test_failed_run_suppresses_inference(self):
        records,plan=records_and_plan();records[-1]['status']='failed'
        rows,status=compare_algorithms(records,plan)
        self.assertEqual(rows,[])
        self.assertEqual(status['status'],'incomplete')


if __name__=='__main__':
    unittest.main()
