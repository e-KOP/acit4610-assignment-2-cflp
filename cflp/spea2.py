"""SPEA2 implementation using the shared CFLP evolutionary pipeline."""

from math import hypot, sqrt
from random import Random

from .configuration import validate_run_config
from .evaluation import evaluate
from .initialization import initialize_population
from .offspring import generate_offspring
from .pareto import dominates, nondominated_indices
from .metrics import normalization_spec


# ==========
# Strength
# ==========


def calculate_strengths(objective_vectors):
    """
    Calculate SPEA2 strength for every individual.

    Strength is the number of other individuals dominated
    by that individual.
    """

    strengths = []

    for i in range(len(objective_vectors)):

        strength = 0

        for j in range(len(objective_vectors)):

            if i == j:
                continue

            if dominates(
                objective_vectors[i],
                objective_vectors[j],
            ):
                strength += 1

        strengths.append(strength)

    return strengths


# =============
# Raw fitness
# =============


def calculate_raw_fitness(
    objective_vectors,
    strengths,
):
    """
    Calculate SPEA2 raw fitness for every individual.

    Raw fitness is the sum of the strengths of all
    individuals that dominate the current individual.

    Lower values are better. A non-dominated individual
    has raw fitness zero.
    """

    raw_fitness = []

    for i in range(len(objective_vectors)):

        fitness = 0

        for j in range(len(objective_vectors)):

            if i == j:
                continue

            if dominates(
                objective_vectors[j],
                objective_vectors[i],
            ):
                fitness += strengths[j]

        raw_fitness.append(fitness)

    return raw_fitness


# ==========================
# Objective normalization
# ==========================


def normalize_objectives(
    instance,
    objective_vectors,
):
    """
    Normalize objective values using the same fixed
    instance-based scaling used by the project metrics.
    """

    specification = normalization_spec(instance)
    scales = specification["scale"]

    return [
        (
            objectives[0] / scales[0],
            objectives[1] / scales[1],
        )
        for objectives in objective_vectors
    ]


# ==========
# Density
# =========


def calculate_density(
    normalized_objectives,
):
    """
    Calculate SPEA2 nearest-neighbour density.

    k is floor(sqrt(N)). Lower density is preferred.
    """

    size = len(normalized_objectives)

    if size == 0:
        return []

    k = max(
        1,
        int(sqrt(size)),
    )

    densities = []

    for i in range(size):

        distances = []

        for j in range(size):

            if i == j:
                continue

            distance = hypot(
                normalized_objectives[i][0]
                - normalized_objectives[j][0],

                normalized_objectives[i][1]
                - normalized_objectives[j][1],
            )

            distances.append(distance)

        distances.sort()

        if not distances:
            sigma_k = 0.0

        else:
            neighbour_index = min(
                k - 1,
                len(distances) - 1,
            )

            sigma_k = distances[
                neighbour_index
            ]

        density = 1.0 / (
            sigma_k + 2.0
        )

        densities.append(density)

    return densities


# ==================
# Total SPEA2 fitness
# ==================


def calculate_fitness(
    instance,
    objective_vectors,
):
    """
    Calculate SPEA2 total fitness.

    fitness = raw fitness + density

    Lower values are better.
    """

    strengths = calculate_strengths(
        objective_vectors
    )

    raw_fitness = calculate_raw_fitness(
        objective_vectors,
        strengths,
    )

    normalized_objectives = normalize_objectives(
        instance,
        objective_vectors,
    )

    densities = calculate_density(
        normalized_objectives
    )

    total_fitness = [
        raw_fitness[i] + densities[i]
        for i in range(len(objective_vectors))
    ]

    return (
        strengths,
        raw_fitness,
        densities,
        total_fitness,
        normalized_objectives,
    )


# ===================
# Archive truncation
# ===================


def truncate_archive(
    candidate_indices,
    normalized_objectives,
    archive_size,
):
    """
    Truncate an oversized SPEA2 archive.

    Repeatedly remove the individual in the most crowded
    region. Distance vectors are compared lexicographically.
    """

    selected = list(candidate_indices)

    while len(selected) > archive_size:

        distance_vectors = {}

        for i in selected:

            distances = []

            for j in selected:

                if i == j:
                    continue

                distance = hypot(
                    normalized_objectives[i][0]
                    - normalized_objectives[j][0],

                    normalized_objectives[i][1]
                    - normalized_objectives[j][1],
                )

                distances.append(distance)

            distances.sort()

            distance_vectors[i] = tuple(
                distances
            )

        remove_index = min(
            selected,
            key=lambda i: (
                distance_vectors[i],
                i,
            ),
        )

        selected.remove(
            remove_index
        )

    return selected


# ===============
# Archive update
# ===============


def update_archive(
    instance,
    population,
    objective_vectors,
    archive_size,
):
    """
    Build the next SPEA2 archive.

    First keep non-dominated individuals.

    If there are too few, fill remaining positions with
    the lowest-fitness dominated individuals.

    If there are too many, truncate crowded individuals.
    """

    (
        strengths,
        raw_fitness,
        densities,
        total_fitness,
        normalized_objectives,
    ) = calculate_fitness(
        instance,
        objective_vectors,
    )

    nondominated = [
        i
        for i, value in enumerate(raw_fitness)
        if value == 0
    ]

    if len(nondominated) > archive_size:

        selected_indices = truncate_archive(
            nondominated,
            normalized_objectives,
            archive_size,
        )

    elif len(nondominated) < archive_size:

        selected_indices = list(
            nondominated
        )

        remaining = [
            i
            for i in range(len(population))
            if i not in selected_indices
        ]

        remaining.sort(
            key=lambda i: (
                total_fitness[i],
                i,
            )
        )

        required = (
            archive_size
            - len(selected_indices)
        )

        selected_indices.extend(
            remaining[:required]
        )

    else:

        selected_indices = list(
            nondominated
        )

    archive = [
        list(population[i])
        for i in selected_indices
    ]

    archive_objectives = [
        objective_vectors[i]
        for i in selected_indices
    ]

    archive_fitness = [
        total_fitness[i]
        for i in selected_indices
    ]

    return (
        archive,
        archive_objectives,
        archive_fitness,
    )


# ====================
# Tournament selection
# =====================


def tournament_winner(
    first,
    second,
    fitness,
    rng,
):
    """
    SPEA2 binary tournament.

    Lower SPEA2 fitness is preferred.
    Remaining ties are resolved randomly.
    """

    if fitness[first] < fitness[second]:
        return first

    if fitness[second] < fitness[first]:
        return second

    return rng.choice(
        (first, second)
    )


def select_parents(
    archive,
    fitness,
    number_of_parents,
    rng,
):
    """
    Select parents from the SPEA2 archive
    using binary tournaments.
    """

    parents = []

    for _ in range(number_of_parents):

        first, second = rng.sample(
            range(len(archive)),
            2,
        )

        winner = tournament_winner(
            first,
            second,
            fitness,
            rng,
        )

        parents.append(
            list(archive[winner])
        )

    return parents


# ===============
# Complete SPEA2
# ================


def run(instance, config, seed):
    """
    Run SPEA2 within the objective-evaluation budget.

    Initialization counts toward the evaluation budget.
    The external archive stores elite solutions.
    """

    validate_run_config(config)

    rng = Random(seed)

    population_size = config[
        "population_size"
    ]

    crossover_probability = config[
        "crossover_probability_per_pair"
    ]

    mutation_probability = config[
        "mutation_probability_per_gene"
    ]

    max_evaluations = config[
        "max_objective_evaluations"
    ]

    archive_rule = config.get(
        "archive_size_rule",
        "equal_to_population_size",
    )

    if archive_rule != "equal_to_population_size":
        raise ValueError(
            "Unsupported SPEA2 archive size rule."
        )

    archive_size = population_size

    # ====================
    # Initial population
    # ====================

    population = initialize_population(
        instance,
        population_size,
        rng,
        max_attempts_per_individual=config.get(
            "initialization_attempts",
            100,
        ),
    )

    objective_vectors = [
        evaluate(
            instance,
            individual,
        )
        for individual in population
    ]

    evaluations = len(population)
    generations = 0

    archive = []
    archive_objectives = []

    # ===============
    # Evolution loop
    # ===============

    while evaluations < max_evaluations:

        combined_population = (
            population + archive
        )

        combined_objectives = (
            objective_vectors
            + archive_objectives
        )

        (
            archive,
            archive_objectives,
            archive_fitness,
        ) = update_archive(
            instance,
            combined_population,
            combined_objectives,
            archive_size,
        )

        remaining_evaluations = (
            max_evaluations
            - evaluations
        )

        offspring_count = min(
            population_size,
            remaining_evaluations,
        )

        number_of_parents = max(
            2,
            offspring_count,
        )

        parents = select_parents(
            archive,
            archive_fitness,
            number_of_parents,
            rng,
        )

        offspring, offspring_objectives = generate_offspring(
            instance,
            parents,
            crossover_probability,
            mutation_probability,
            rng,
            number_of_offspring=offspring_count,
            max_attempts_per_child=config.get(
                "offspring_attempts",
                50,
            ),
        )

        population = offspring
        objective_vectors = offspring_objectives

        evaluations += len(
            offspring
        )

        generations += 1

    # ======================
    # Final archive update
    # ======================

    combined_population = (
        population + archive
    )

    combined_objectives = (
        objective_vectors
        + archive_objectives
    )

    (
        archive,
        archive_objectives,
        archive_fitness,
    ) = update_archive(
        instance,
        combined_population,
        combined_objectives,
        archive_size,
    )

    # ==========================
    # Final non-dominated set
    # ==========================

    final_indices = nondominated_indices(
        archive_objectives
    )

    final_population = [
        archive[index]
        for index in final_indices
    ]

    final_objectives = [
        archive_objectives[index]
        for index in final_indices
    ]

    return {
        "algorithm": "spea2",
        "status": "completed",
        "seed": seed,
        "evaluations": evaluations,
        "generations": generations,
        "population": final_population,
        "objectives": final_objectives,
    }