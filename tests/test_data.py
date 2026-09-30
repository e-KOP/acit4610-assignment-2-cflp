"""Guard source integrity, customer-major parsing, and malformed input."""

import unittest
import json
from cflp.data import INSTANCE_SIZES, PROJECT_ROOT, load_instance, parse_instance, verify_data
from cflp.experiments import load_experiment_config


class DataTests(unittest.TestCase):
    def test_required_instance_set_matches_data_and_experiments(self):
        expected = {"cap61", "cap62", "cap101", "cap102", "cap121", "cap122"}
        manifest = json.loads((PROJECT_ROOT / "data" / "checksums.json").read_text())
        config = load_experiment_config()
        self.assertEqual(set(INSTANCE_SIZES), expected)
        self.assertEqual(set(manifest["instances"]), expected)
        self.assertEqual(set(config["instances"]), expected)
        self.assertEqual(config["analysis_instances"], ["cap61", "cap101", "cap121"])

    def test_all_bundled_instances_and_checksums(self):
        self.assertEqual(set(verify_data()), set(INSTANCE_SIZES))
        for name, dimensions in INSTANCE_SIZES.items():
            with self.subTest(name=name):
                instance = load_instance(name)
                self.assertEqual((instance.n_facilities, instance.n_customers), dimensions)

    def test_customer_records_become_facility_rows(self):
        # Two facilities, three customers. Breaks intentionally cross records.
        text = "2 3\n10 100 20\n200\n1 11 21 2\n12 22\n3 13 23"
        instance = parse_instance(text)
        self.assertEqual(instance.capacities, (10, 20))
        self.assertEqual(instance.fixed_costs, (100, 200))
        self.assertEqual(instance.demands, (1, 2, 3))
        self.assertEqual(instance.allocation_costs, ((11, 12, 13), (21, 22, 23)))

    def test_raw_cap61_known_fields(self):
        instance = load_instance("cap61")
        self.assertEqual(instance.capacities[0], 15000)
        self.assertEqual(instance.fixed_costs[0], 7500)

    def test_missing_or_extra_tokens_are_rejected(self):
        for text in ("", "1 1 5 10 2", "1 1 5 10 2 7 99"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_instance(text)

    def test_invalid_dimensions_or_values_are_rejected(self):
        for text in ("0 1", "1.5 1", "1 1 5 10 2 nan", "1 1 5 -10 2 7", "1 1 5 10 2 inf"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_instance(text)


if __name__ == "__main__":
    unittest.main()
