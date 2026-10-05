"""Inspect data, run optimizers, and regenerate experiment outputs."""

import argparse
from pathlib import Path
from .data import INSTANCE_SIZES, load_instance, verify_data
from .experiments import (experiment_plan, load_experiment_config, run_experiment,
                          summarize_directory, ALGORITHMS)


def print_instance(name, detail=False):
    instance = load_instance(name)
    print(f"{name:7} facilities={instance.n_facilities:2} customers={instance.n_customers:2} "
          f"total_demand={sum(instance.demands):g} total_capacity={sum(instance.capacities):g}")
    if detail:
        print(f"  Facility 0: capacity={instance.capacities[0]:g}, fixed_cost={instance.fixed_costs[0]:g}")
        print(f"  Customer 0: demand={instance.demands[0]:g}")
        print(f"  C[0][0]={instance.allocation_costs[0][0]:g} (already includes all demand)")
        print("  Data inspection only: no optimizer has been run.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    parser.add_argument("--instance", choices=INSTANCE_SIZES, help="Inspect one instance")
    actions.add_argument("--all", action="store_true", help="Inspect all six instances")
    actions.add_argument("--verify-data", action="store_true", help="Verify checksums and structure")
    actions.add_argument("--plan", action="store_true", help="Preview planned experiments, without running")
    actions.add_argument("--run", action="store_true", help="Run one optimizer/instance/configuration/seed")
    actions.add_argument("--batch", action="store_true", help="Run all configurations and ten seeds")
    actions.add_argument("--summarize", action="store_true", help="Regenerate tables and SVG plots")
    parser.add_argument("--algorithm", default="nsga2", choices=["nsga2", "spea2"])
    parser.add_argument("--configuration", choices=["smaller_population", "reference", "larger_population"], default="reference")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--budget", type=int, help="Override budget for pilots; use a separate output directory")
    parser.add_argument("--output", type=Path, default=Path("results/nsga2"))
    parser.add_argument("--resume", action="store_true", help="Reuse matching completed run records")
    args = parser.parse_args()
    if args.summarize:
        rows = summarize_directory(args.output)
        print(f"Wrote {len(rows)} summary rows and Pareto plots to {args.output}")
        return
    if args.run or args.batch:
        if args.algorithm not in ALGORITHMS:
            parser.error(f"{args.algorithm} is not implemented yet.")
        config = load_experiment_config()
        config["algorithms"] = [args.algorithm]
        if args.instance or args.run:
            config["instances"] = [args.instance or "cap61"]
        if args.run:
            config["seeds"] = [args.seed]
            config["configurations"] = {args.configuration: config["configurations"][args.configuration]}
        if args.budget is not None:
            config["common"]["max_objective_evaluations"] = args.budget
        for job in experiment_plan(config):
            result = run_experiment(job, args.output, resume=args.resume)
            print(f"{job['instance']} {job['configuration']} seed={job['seed']} "
                  f"evaluations={result['evaluations']} HV={result['metrics']['hv']:.6f} "
                  f"ND={result['metrics']['nd']} time={result['runtime_seconds']:.3f}s", flush=True)
        summarize_directory(args.output)
        return
    if args.verify_data:
        for name in verify_data():
            print(f"OK {name}: SHA-256 and dimensions verified")
    elif args.plan:
        config = load_experiment_config()
        runs = list(experiment_plan(config))
        print(f"Status: {config['status']}; available optimizers: {list(ALGORITHMS)}.")
        print(f"{len(config['algorithms'])} algorithms x {len(config['instances'])} instances x "
              f"{len(config['configurations'])} configurations x {len(config['seeds'])} seeds = {len(runs)} planned runs")
        for name, overrides in config["configurations"].items():
            settings = {**config["common"], **overrides}
            print(f"  {name}: {settings}")
        print("No results have been generated; pilot and confirm these settings before experiments.")
    elif args.all:
        for name in INSTANCE_SIZES:
            print_instance(name)
    else:
        print_instance(args.instance or "cap61", detail=True)


if __name__ == "__main__":
    main()
