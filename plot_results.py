"""Render three configuration panels per focus instance from saved run records."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from cflp.metrics import unique_front

CONFIGURATIONS = [("A", "smaller_population", 50),
                  ("B", "reference", 100),
                  ("C", "larger_population", 200)]
ALGORITHMS = {"nsga2": ("NSGA-II", "#2563eb", "o"),
              "spea2": ("SPEA2", "#dc2626", "^")}


def plot_instance(records, instance, output):
    selected = [r for r in records if r["instance"] == instance and r["status"] == "completed"]
    if not selected:
        raise ValueError(f"No completed runs for {instance}.")
    points = [p for r in selected for p in r["objectives"]]
    seeds = sorted({r["seed"] for r in selected})
    colors = {seed: plt.get_cmap("tab10")(index % 10) for index, seed in enumerate(seeds)}
    limits = []
    for axis, scale in [(0, 1000), (1, 1000000)]:
        low, high = min(p[axis] for p in points)/scale, max(p[axis] for p in points)/scale
        pad = max((high-low)*.09, .01)
        limits.append((max(0, low-pad), high+pad))
    fig, axes = plt.subplots(1, 3, figsize=(16, 6.8), sharex=True, sharey=True)
    present = set()
    for ax, (letter, config, population) in zip(axes, CONFIGURATIONS):
        counts = []
        for algorithm, (label, color, marker) in ALGORITHMS.items():
            runs = [r for r in selected if r["configuration"] == config and r["algorithm"] == algorithm]
            if not runs:
                continue
            if len({r['seed'] for r in runs}) != len(runs):
                raise ValueError("Duplicate seeds in a plot group.")
            if any(r['parameters']['population_size'] != population for r in runs):
                raise ValueError("Population size differs from the panel label.")
            for run in sorted(runs, key=lambda r: r["seed"]):
                individual_front = unique_front(run["objectives"])
                ax.plot([p[0]/1000 for p in individual_front],
                        [p[1]/1000000 for p in individual_front],
                        color=colors[run["seed"]], alpha=.48, lw=1,
                        marker=marker, ms=3.5,
                        linestyle="-" if algorithm == "nsga2" else "--", zorder=2)
            present.add(algorithm)
            counts.append(f"{label}: {len(runs)} independent fronts")
        pending = [label + ": pending" for algorithm, (label, _, _) in ALGORITHMS.items()
                   if not any(r['configuration'] == config and r['algorithm'] == algorithm for r in selected)]
        ax.set_title(f"Configuration {letter} | population {population}", fontsize=11, pad=12)
        ax.text(.96, .96, '\n'.join(counts + pending), transform=ax.transAxes,
                va="top", ha="right", fontsize=8.5, color="#475569",
                bbox=dict(facecolor="white", edgecolor="none", alpha=.8))
        ax.set_xlim(*limits[0]); ax.set_ylim(*limits[1])
        ax.set_xlabel("Facility opening cost, f1 (thousands)", fontsize=10)
        ax.grid(alpha=.18, zorder=0)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel("Customer allocation cost, f2 (millions)", fontsize=10)
    category = {"cap61": "Small", "cap101": "Medium", "cap121": "Large"}.get(instance, "Benchmark")
    fig.suptitle(f"{instance} | {category} instance | Pareto approximation sets", fontsize=16, x=.06, ha="left", y=.98)
    handles = [Line2D([], [], color=colors[seed], marker="o", alpha=.6,
                      linewidth=1, markersize=4, label=f"Seed {seed}") for seed in seeds]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.53, .92),
               ncol=5, frameon=False, fontsize=9)
    budgets = sorted({r['evaluations'] for r in selected})
    budget_text = f"{budgets[0]:,} evaluations per run" if len(budgets) == 1 else "Mixed evaluation budgets"
    caption = (f"Colored lines: individual final fronts, one per seed. {budget_text}.\n"
               "Lines only guide the eye; intermediate locations are not necessarily feasible. Axes are shared across configurations."
               + (" SPEA2: pending." if "spea2" not in present else ""))
    fig.text(.06, .035, caption, fontsize=9, color="#475569", linespacing=1.6)
    fig.subplots_adjust(left=.06, right=.98, top=.73, bottom=.18, wspace=.10)
    output.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(output / f"{instance}_pareto.{extension}", dpi=200, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('results/nsga2'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    records = [json.loads(p.read_text()) for p in sorted((args.input/'runs').glob('*.json'))]
    output = args.output or args.input/'figures'
    for instance in ('cap61', 'cap101', 'cap121'):
        plot_instance(records, instance, output)
        print(f"Saved {instance}: PNG, PDF, SVG in {output}")


if __name__ == '__main__':
    main()
