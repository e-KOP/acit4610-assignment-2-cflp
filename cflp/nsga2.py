"""NSGA-II with shared feasible variation and an exact evaluation budget.

Order: nondominated sorting -> crowding distance -> tournament selection ->
shared variation/repair/evaluation -> elitist selection from parents + offspring.
"""

from math import inf
from numbers import Integral
from random import Random

from .pareto import dominates, nondominated_sort
from .evaluation import evaluate
from .offspring import generate_offspring
from .configuration import validate_run_config
from .initialization import initialize_population




def crowding_distance(objective_vectors, front):
    """Return {individual_index: distance}, calculated within one front.

    Normalize each objective by its range in this front. Skip constant
    objectives to avoid dividing by zero. For fronts of size <= 2, assign inf.
    Equal objective values use original index order as a deterministic tie-break.
    With >= 3 identical vectors all distances are zero, so selection is random.
    """
    if len(set(front)) != len(front):
        raise ValueError("A front must contain unique individual indices.")
    for i in front:
        if not 0 <= i < len(objective_vectors):
            raise ValueError("Front index is outside the population.")
        dominates(objective_vectors[i], objective_vectors[i])
    distances = {i: 0.0 for i in front}
    if len(front) <= 2:
        return {i: inf for i in front}

    for objective in range(2):
        ordered = sorted(front, key=lambda i: (objective_vectors[i][objective], i))
        minimum = objective_vectors[ordered[0]][objective]
        maximum = objective_vectors[ordered[-1]][objective]
        span = maximum - minimum
        if span == 0:
            continue
        distances[ordered[0]] = inf
        distances[ordered[-1]] = inf
        for position in range(1, len(ordered) - 1):
            previous_value = objective_vectors[ordered[position - 1]][objective]
            next_value = objective_vectors[ordered[position + 1]][objective]
            distances[ordered[position]] += (next_value - previous_value) / span
    return distances


def rank_and_crowding(objective_vectors):
    """Return fronts, one-based ranks, and distances aligned with the population."""
    fronts = nondominated_sort(objective_vectors)
    ranks = [0] * len(objective_vectors)
    distances = [0.0] * len(objective_vectors)
    for rank, front in enumerate(fronts, start=1):
        front_distances = crowding_distance(objective_vectors, front)
        for i in front:
            ranks[i] = rank
            distances[i] = front_distances[i]
    return fronts, ranks, distances


def tournament_winner(a, b, ranks, distances, rng):
    """Given two sampled indices, prefer lower rank, then greater crowding.

    Break complete ties with the caller's seeded random generator. Return an
    index only: selection does not mutate individuals or create offspring.
    """
    if ranks[a] != ranks[b]:
        return a if ranks[a] < ranks[b] else b
    if distances[a] != distances[b]:
        return a if distances[a] > distances[b] else b
    return rng.choice((a, b))


def environmental_selection(objective_vectors, population_size, rng):
    """Select original indices from the combined parent/offspring population.

    Accept complete fronts in rank order. If a front does not fit, take its
    greatest crowding distances, breaking equal distances randomly. Preserve
    separate individuals even when their objective vectors are equal.
    """
    if (isinstance(population_size, bool) or not isinstance(population_size, Integral)
            or not 0 <= population_size <= len(objective_vectors)):
        raise ValueError("Survivor count must be an integer between zero and candidate count.")
    fronts, ranks, distances = rank_and_crowding(objective_vectors)
    selected = []
    for front in fronts:
        remaining = population_size - len(selected)
        if remaining == 0:
            break
        if len(front) <= remaining:
            selected.extend(front)
        else:
            candidates = list(front)
            # Stable sorting after shuffling randomizes only equal-distance ties.
            rng.shuffle(candidates)
            candidates.sort(key=lambda i: distances[i], reverse=True)
            selected.extend(candidates[:remaining])
            break
    return selected


# ==========================
# Parent selection
# ==========================


def select_parents(
    population,
    ranks,
    distances,
    number_of_parents,
    rng,
):
    """
    Select parents using binary tournament selection.

    Two different individuals are sampled for each tournament.
    Lower non-dominated rank is preferred. If the ranks are equal,
    the individual with the larger crowding distance is preferred.
    Remaining ties are resolved randomly.
    """

    parents = []

    for _ in range(number_of_parents):

        first, second = rng.sample(
            range(len(population)),
            2,
        )

        winner = tournament_winner(
            first,
            second,
            ranks,
            distances,
            rng,
        )

        parents.append(
            list(population[winner])
        )

    return parents

def run(instance, config, seed):
    """
    Run NSGA-II within the specified objective-evaluation budget.

    Initialization counts toward the evaluation budget. Each generation
    ranks the current population, selects parents with binary tournaments,
    generates feasible offspring, and applies elitist environmental
    selection to the combined parent and offspring population.

    Returns the final non-dominated solutions together with run metadata.
    """

    validate_run_config(config)
    rng = Random(seed)

    population_size = config["population_size"]
    crossover_probability = config["crossover_probability_per_pair"]
    mutation_probability = config["mutation_probability_per_gene"]
    max_evaluations = config["max_objective_evaluations"]

    if population_size < 2:
        raise ValueError(
            "NSGA-II requires a population size of at least 2."
        )

    if max_evaluations < population_size:
        raise ValueError(
            "Evaluation budget must be at least the population size."
        )

    # ==========================
    # Initial population
    # ==========================

    population = initialize_population(
        instance,
        population_size,
        rng,
        max_attempts_per_individual=config.get("initialization_attempts", 100),
    )

    objective_vectors = [
        evaluate(instance, individual)
        for individual in population
    ]

    evaluations = len(population)
    generations = 0

    # ==========================
    # Evolution loop
    # ==========================

    while evaluations < max_evaluations:

        _, ranks, distances = rank_and_crowding(
            objective_vectors
        )

        remaining_evaluations = (
            max_evaluations - evaluations
        )

        offspring_count = min(
            population_size,
            remaining_evaluations,
        )

        # A mating pool the same size as the number of children
        # required in this generation.
        number_of_parents = max(
            2,
            offspring_count,
        )

        parents = select_parents(
            population,
            ranks,
            distances,
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
            max_attempts_per_child=config.get("offspring_attempts", 50),
        )

        evaluations += len(offspring)
        generations += 1

        # ==========================
        # Elitist replacement
        # ==========================

        combined_population = (
            population + offspring
        )

        combined_objectives = (
            objective_vectors + offspring_objectives
        )

        selected_indices = environmental_selection(
            combined_objectives,
            population_size,
            rng,
        )

        population = [
            combined_population[index]
            for index in selected_indices
        ]

        objective_vectors = [
            combined_objectives[index]
            for index in selected_indices
        ]

    # ==========================
    # Final non-dominated set
    # ==========================

    fronts = nondominated_sort(
        objective_vectors
    )

    final_indices = (
        fronts[0]
        if fronts
        else []
    )

    final_population = [
        population[index]
        for index in final_indices
    ]

    final_objectives = [
        objective_vectors[index]
        for index in final_indices
    ]

    return {
        "algorithm": "nsga2",
        "status": "completed",
        "generations": generations,
        "seed": seed,
        "evaluations": evaluations,
        "population": final_population,
        "objectives": final_objectives,
    }
