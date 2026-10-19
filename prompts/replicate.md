# Replicate one paper's tables

You are given one paper ID, `<wid>`. Its PDF is `pdfs/<wid>.pdf`, its text `txt/<wid>.txt`,
its replication package `datasets/<wid>/` (read-only). Work only in `replications/<wid>/`.

**Goal:** re-estimate the paper's main regression table, and any table of treatment-effect
heterogeneity (interactions or subgroups), in Python, and check every published number.
Nothing beyond that.

## Steps

1. **Find the table** and the script in the package that produces it. Prefer the package's
   own table output (`.tex`, `.csv`, logs) over the PDF: it carries more digits.
2. **Write `replications/<wid>/replicate.py`.** Build the analysis data as the package does,
   then fit each column with `pyfixest`: same outcome, treatment, controls, fixed effects,
   sample and clustering. Port the authors' code as written, bugs and quirks included;
   tidying it makes a column miss by a little in a way no one can diagnose.
3. **Type the published numbers in by hand**: each coefficient, and each column's N.
   Never fill them in from your own output.
4. **Check.** The script prints one row per number: table, column, term, published, ours,
   MATCH or MISS, and exits non-zero if anything misses.
   - A coefficient matches within half a unit of its last printed digit
     (2 decimals means ±0.005).
   - N must match exactly.
   - Never loosen a tolerance to make a check pass.
5. **Write `replications/<wid>/REPORT.md`** in a few lines: which tables, which version
   of the paper the numbers came from, and the result.

## Rules

- **A miss is a result.** Keep the column, with its correct published numbers, and say in
  REPORT.md what missed, by how much and what you ruled out. Never drop it or hide it.
- **A package with code but no data** cannot be replicated: write a one-line REPORT.md and stop.
- **A table that prints no N:** check the coefficients and say so.
- **Inference that differs from ours** (randomization inference, bootstrap):
  check the point estimates only, and say so.
