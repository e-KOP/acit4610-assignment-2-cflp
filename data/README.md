# OR-Library instances

Author/maintainer: J. E. Beasley.

- Format: https://people.brunel.ac.uk/~mastjjb/jeb/orlib/capinfo.html
- Files: https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/
- Provenance: `checksums.json` records the exact URL, retrieval timestamp, raw byte
  length and SHA-256 for each file. No additional data license is asserted here.

Required instances: **cap61, cap62, cap101, cap102, cap121, cap122**.
Small instances have 16 facilities, Medium 25, Large 50; each has 50 customers.
The small benchmark replacement follows the assignment update supplied on 2026-09-25.
Each manifest record includes its own retrieval timestamp; existing Medium/Large files
retain their original checksums and retrieval dates.

The six bundled `.txt` files are saved exactly as downloaded. Do not normalize,
replace or generate values in these files. Generate candidate solutions separately.

## Token order

```text
m n
capacity[0] fixed_cost[0]
... (m facilities)
demand[0] costs_to_facility_0 ... costs_to_facility_m_minus_1
... (n customers)
```

Line breaks are for formatting: one customer's cost vector can span multiple lines.
The reader uses whitespace tokens and expects `2 + 2*m + n*(m+1)` tokens.

| Raw field | Python attribute | Meaning |
|---|---|---|
| facility capacity | `capacities[i]` | S_i |
| facility fixed cost | `fixed_costs[i]` | F_i |
| customer demand | `demands[j]` | d_j |
| customer's cost to each facility | `allocation_costs[i][j]` | C_ij |

Allocation costs already include the customer's entire demand. Demand is used for
capacity checking, not as another multiplier in the allocation objective.
Zero opening costs in the originals are valid and must remain unchanged.

Run `python3 -m cflp --verify-data` from the project root to check file integrity.
If a file is accidentally edited, restore it from the exact recorded source URL
and verify the recorded hash; do not change the expected hash to hide the edit.

OR-Library's `capopt` lists single-objective reference values. Those are not this
assignment's two-objective Pareto front and are not used as such in this scaffold.
