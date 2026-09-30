"""Runnable data inspection and experiment-plan entry point."""

import argparse
from .data import INSTANCE_SIZES, load_instance, verify_data
from .experiments import experiment_plan, load_experiment_config


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
    actions.add_argument("--instance", choices=INSTANCE_SIZES, help="Inspect one instance")
    actions.add_argument("--all", action="store_true", help="Inspect all six instances")
    actions.add_argument("--verify-data", action="store_true", help="Verify checksums and structure")
    actions.add_argument("--plan", action="store_true", help="Preview planned experiments, without running")
    args = parser.parse_args()
    if args.verify_data:
        for name in verify_data():
            print(f"OK {name}: SHA-256 and dimensions verified")
    elif args.plan:
        config = load_experiment_config()
        runs = list(experiment_plan(config))
        print(f"Status: {config['status']}; optimizers are not implemented yet.")
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
