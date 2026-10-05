"""SPEA2 integration boundary; core algorithm is intentionally not implemented.

Implement strength/raw fitness, density, archive filling/truncation, and archive
parent selection here. Reuse initialization.initialize_population and
 offspring.generate_offspring, and call configuration.validate_run_config.
Follow the exact result contract documented in README.md. Update the archive
with the last evaluated offspring before extracting the final non-dominated set.
Register run in experiments.ALGORITHMS only after implementation and tests.
"""


def run(instance, config, seed):
    """Return algorithm, status, seed, evaluations, generations, population, objectives.

    population is the final non-dominated approximation set, not the working
    population or unfiltered archive. Initialization counts toward the budget.
    SPEA2 should resolve archive_size_rule=equal_to_population_size from config.
    """
    raise NotImplementedError("SPEA2 is not implemented; use the shared pipeline contract in README.md.")
