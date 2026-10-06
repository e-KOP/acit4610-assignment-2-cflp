# Generated experiment output

Run both algorithms with the declared paired design:

```bash
python3 -m cflp --batch --algorithm both --output results/comparison --resume
python3 -m cflp --summarize --output results/comparison
python3 -m pip install -r requirements-plotting.txt
python3 scripts/plot_comparison.py --results results/comparison

# Optional per-seed front view
python3 -m cflp --plot --output results/comparison
```

The directory contains 360 per-run records, descriptive summary CSV, comparison
CSV, completion/inference status JSON, and pooled SVG summaries. The comparison
script exports six figures, one per instance, with Pareto points above HV mean ±
sample SD in matching A/B/C columns. The optional plot command exports per-seed
fronts for the three focus instances. A partial run produces descriptive output only; no inferential rows are
released before the entire declared comparison family is complete. See the root
README for timing, pairing, statistical assumptions and multiple-comparison rules.

Generated directories are ignored by Git. Preserve raw records, and use a new
output directory after code or protocol changes. The old `nsga2/` directory is
historical and must not be mixed with the common-source paired experiment.
