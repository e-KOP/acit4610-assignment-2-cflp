# Generated experiment output

Run `python3 -m cflp --batch --algorithm nsga2 --output results/nsga2 --resume`.
Each output directory holds per-run JSON, a descriptive summary CSV, a completion
status JSON, and pooled-front SVG scatter plots. See the root README for exact
metric, timing, and plotting conventions.

These directories are ignored by Git. A partial batch or a pilot budget must not
be represented as a completed formal experiment. Preserve raw run records so
metrics and plots can be regenerated. SPEA2 and inferential comparisons remain
pending; no second-algorithm results are fabricated.
