"""Validate the common contract before either optimizer starts."""

from numbers import Integral
from .operators import validate_probability


def positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


def validate_run_config(config):
    for key in ("population_size", "max_objective_evaluations"):
        positive_integer(config[key], key)
    if config["population_size"] < 2:
        raise ValueError("Population size must be at least two.")
    if config["max_objective_evaluations"] < config["population_size"]:
        raise ValueError("Evaluation budget must cover initialization.")
    for key in ("crossover_probability_per_pair", "mutation_probability_per_gene"):
        validate_probability(config[key])
    for key, default in (("initialization_attempts", 100), ("offspring_attempts", 50)):
        positive_integer(config.get(key, default), key)
    if config.get("count_initial_population_evaluations", True) is not True:
        raise ValueError("Initialization must count toward the evaluation budget.")
    if config.get("cache_objective_values", False) is not False:
        raise ValueError("Candidate evaluation caching is not supported.")
    if config.get("termination", "objective_evaluation_budget") != "objective_evaluation_budget":
        raise ValueError("Only objective-evaluation termination is supported.")
    expected = {"initialization": "randomized_best_fit_top_three",
                "repair": "deterministic_capacity_relocation"}
    for key, value in expected.items():
        if config.get(key, value) != value:
            raise ValueError(f"Unsupported {key}: {config[key]}")
