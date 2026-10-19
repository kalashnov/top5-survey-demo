# Replicate one paper's tables

You are given one paper ID, `<wid>`. Its PDF is `pdfs/<wid>.pdf`, its text `txt/<wid>.txt`,
its replication package `datasets/<wid>/` (read-only).

**Goal:** re-estimate the paper's main regression table, and any table of treatment-effect
heterogeneity (interactions or subgroups), and check every published number. Nothing beyond that.

Read `replications/spec.py` (the `Spec` every column is) and `replications/W4401126511.py`
(a worked paper) before you start.

## Steps

1. **Find the table** and the script in the package that produces it. Prefer the package's
   own table output (`.tex`, `.csv`, logs) over the PDF: it carries more digits.
2. **Write `replications/<wid>.py`** with:
   - one `load()` per analysis dataset (`@cache`), building it as the package does;
   - `SPECS = {"<table>_<column>": (load, Spec(...))}`, one entry per published column.
   Interactions go in the formula (`treat*female`); a subgroup column is its own spec
   with a `sample`. Port the authors' code as written, quirks included.
3. **Type the published numbers in by hand** into `targets` and `n`. Never fill them in from
   your own output. `tol` is half a unit of the last printed digit (2 decimals: 0.005);
   never loosen it to make a check pass.
4. **Check:** `pytest test_replications.py -k <wid>`.
5. **Write `replications/<wid>.md`** in a few lines: which tables, which version of the
   paper the numbers came from, and the result.

## Rules

- **A miss is a result.** Keep the spec with its correct published numbers, leave the test
  failing, and say in the report what missed, by how much and what you ruled out.
- **A package with code but no data** cannot be replicated: write a one-line report and stop.
- **A table that prints no N:** set `n=None` and say so.
- **Inference that differs from ours** (randomization inference, bootstrap):
  check the point estimates only, and say so in `note`.
