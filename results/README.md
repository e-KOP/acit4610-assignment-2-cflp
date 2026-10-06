# Generated experiment output

The committed `comparison/` directory contains the 360 raw run records,
`summary.csv`, `comparison.csv`, and their two status JSON files. Records retain
final assignments, objective values, seeds, parameters, runtime, metrics, and
source/data/environment metadata. They contain final results, not generation histories.

Run these commands from the repository root to regenerate summaries and figures:

```bash
python3 -m cflp --summarize --output results/comparison
python3 -m pip install -r requirements-plotting.txt
python3 scripts/plot_comparison.py --results results/comparison

# Optional per-seed front view
python3 -m cflp --plot --output results/comparison
```

A completed batch generates 360 per-run records. Summarization produces
descriptive and comparison CSVs, completion/inference status JSON, and pooled
SVG summaries. The comparison
script exports six figures, one per instance, with Pareto points above HV mean ±
sample SD in matching A/B/C columns. The optional plot command exports per-seed
fronts for the three focus instances. A partial run produces descriptive output
only; no inferential rows are released before the entire declared comparison family is complete. See the root
README for timing, pairing, statistical assumptions and multiple-comparison rules.

To rerun the experiment, use a separate directory:

```bash
python3 -m cflp --batch --algorithm both --output results/reproduction --resume
python3 -m cflp --summarize --output results/reproduction
python3 scripts/plot_comparison.py --results results/reproduction --output results/reproduction/figures
```

The committed records retain the original execution environment. `--resume`
rejects records from a different environment or source version. Keep the original
records intact. Other experiment directories and additional plot exports remain
ignored by Git; the six README PNG figures are tracked in `docs/figures/`.
