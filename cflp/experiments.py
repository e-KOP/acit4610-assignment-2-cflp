"""Run either registered optimizer, persist evidence, and regenerate summaries."""

import csv
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from time import perf_counter

from .data import PROJECT_ROOT, load_instance
from .configuration import validate_run_config
from .evaluation import evaluate
from .metrics import calculate_metrics, unique_front
from .plotting import pareto_svg
from .statistics import summarize_runs, compare_algorithms
from .protocol import validate_records
from . import nsga2, spea2

ALGORITHMS = {
    "nsga2": nsga2.run,
    "spea2": spea2.run,
}


def load_experiment_config():
    return json.loads((PROJECT_ROOT / "configs" / "experiments.json").read_text())


def experiment_plan(config):
    for instance in config["instances"]:
        for name, overrides in config["configurations"].items():
            for seed in config["seeds"]:
                # Alternate algorithm order across paired seeds to balance timing drift.
                algorithms = config["algorithms"][::1 if seed % 2 == 0 else -1]
                for algorithm in algorithms:
                    yield {"instance": instance, "algorithm": algorithm,
                           "configuration": name, "seed": seed,
                           "parameters": {**config["common"], **overrides,
                               **config.get("algorithm_specific", {}).get(algorithm, {})}}


def source_fingerprint():
    digest = hashlib.sha256()
    for path in sorted((PROJECT_ROOT / "cflp").glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def atomic_json(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(content, indent=2, allow_nan=False) + "\n")
    pending.replace(path)


def run_experiment(job, output_dir, resume=False):
    """Timing covers optimizer initialization through final front extraction.

    Loading, validation of returned results, metrics, and disk output are outside
    timing. Failed runs are recorded and raised; they cannot count as successes.
    Resume requires identical source, data, parameters, seed, and environment.
    """
    algorithm = job["algorithm"]
    if algorithm not in ALGORITHMS:
        raise ValueError(f"{algorithm} is not implemented; available: {', '.join(ALGORITHMS)}")
    validate_run_config(job["parameters"])
    instance = load_instance(job["instance"])
    source_hash = source_fingerprint()
    data_hash = hashlib.sha256((PROJECT_ROOT / "data" / "or_library" / f"{instance.name}.txt").read_bytes()).hexdigest()
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "machine": platform.machine(), "processor": platform.processor(),
                   "node": platform.node()}
    signature = hashlib.sha256(json.dumps([job, source_hash, data_hash, environment], sort_keys=True).encode()).hexdigest()
    path = Path(output_dir) / "runs" / f"{instance.name}__{algorithm}__{job['configuration']}__seed{job['seed']}.json"
    if path.exists():
        previous = json.loads(path.read_text())
        if resume and previous.get("signature") == signature and previous.get("status") == "completed":
            return previous
        raise ValueError(f"Existing result cannot be reused: {path}. Use a different output directory.")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    record = {**job, "schema_version": 1, "signature": signature,
              "source_sha256": source_hash, "data_sha256": data_hash,
              "git_revision": revision, "environment": environment}
    started = perf_counter()
    try:
        result = ALGORITHMS[algorithm](instance, job["parameters"], job["seed"])
        elapsed = perf_counter() - started
        if result.get("status") != "completed" or result["evaluations"] != job["parameters"]["max_objective_evaluations"]:
            raise ValueError("Optimizer did not complete the requested evaluation budget.")
        if result["algorithm"] != algorithm or result["seed"] != job["seed"]:
            raise ValueError("Optimizer returned inconsistent metadata.")
        population, objectives = result["population"], result["objectives"]
        if not population or len(population) != len(objectives):
            raise ValueError("Optimizer returned an empty or misaligned approximation set.")
        for assignment, objective in zip(population, objectives):
            if tuple(evaluate(instance, assignment)) != tuple(objective):
                raise ValueError("Returned objective values do not match the assignments.")
        if set(map(tuple, objectives)) != set(unique_front(objectives)):
            raise ValueError("Optimizer returned dominated objective vectors.")
        record.update(result, runtime_seconds=elapsed, metrics=calculate_metrics(instance, objectives))
    except Exception as error:
        record.update(status="failed", runtime_seconds=perf_counter()-started,
                      error=f"{type(error).__name__}: {error}")
        atomic_json(path, record)
        raise
    atomic_json(path, record)
    return record


def summarize_directory(output_dir):
    """Rebuild CSV and pooled-front plots; reject mixed protocols within groups."""
    output_dir = Path(output_dir)
    records = [json.loads(path.read_text()) for path in sorted((output_dir / "runs").glob("*.json"))]
    if not records:
        raise ValueError("No run records found.")
    successful = [r for r in records if r["status"] == "completed"]
    validate_records(records)
    rows = summarize_runs(successful)
    if rows:
        with (output_dir / "summary.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    plots = output_dir / "plots"
    plots.mkdir(exist_ok=True)
    groups = sorted({(r["instance"], r["configuration"]) for r in successful})
    for instance, configuration in groups:
        series = {}
        for record in successful:
            if (record["instance"], record["configuration"]) == (instance, configuration):
                series.setdefault(record["algorithm"], []).extend(record["objectives"])
        series = {name: unique_front(values) for name, values in series.items()}
        (plots / f"{instance}__{configuration}.svg").write_text(
            pareto_svg(series, f"{instance} / {configuration}: pooled non-dominated fronts"))
    comparison, comparison_status = compare_algorithms(records, load_experiment_config())
    comparison_path = output_dir / "comparison.csv"
    with comparison_path.open("w", newline="") as handle:
        fields = list(comparison[0]) if comparison else ["instance", "configuration", "metric", "p_raw", "p_holm"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(comparison)
    atomic_json(output_dir / "comparison_status.json", comparison_status)
    atomic_json(output_dir / "summary_status.json", {
        "completed": len(successful), "failed": len(records)-len(successful),
        "groups": len(rows), "minimum_runs_per_group": min((r["runs"] for r in rows), default=0),
        "plot_rule": "Non-dominated union of completed runs per algorithm and configuration; not a typical run.",
        "statistical_comparison": comparison_status["status"],
    })
    return rows
