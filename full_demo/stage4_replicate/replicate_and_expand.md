---
name: replicate-and-expand
description: Replicates a published paper's interaction/heterogeneity tables and then runs the mega-replication sweep over every candidate moderator, recording the evidence the causal-forest agent decides `X` on. One agent per paper — spawn it with the paper's registry key (e.g. "run replicate-and-expand on W4412789100"). Use when a new paper is being ported into the interactions half of this codebase.
---

You are extending a replication codebase for a meta-analysis of interaction /
heterogeneity tables in published economics papers. Your job has two phases, in
order. Do not start Phase 2 until Phase 1 verifies.

## Your assignment

You are given a single `PAPER_KEY` (a registry key like `W0000000000`); its
replication package lives in `datasets/<PAPER_KEY>/`. If the spawn prompt did
not name one, stop and ask for it before doing anything else.

Work only on `PAPER_KEY`. Do not modify other papers' loaders or specs. The one
shared file you must edit is the registry, `data_scripts/__init__.py`.

If you are running in a git worktree, `datasets/` and `.venv/` are symlinks into
the main checkout. Treat `datasets/` as read-only. If you need to `pip install`
anything, it leaks into the shared `.venv` and persists after the worktree is
gone — so say so explicitly in your report.

### Scope — two projects share this codebase; only one is yours

This directory hosts **two independent research projects** that share a registry
and some plumbing. Read the boundary carefully, because most of the files here
belong to the project that is *not* yours.

**NOT your project — ignore it entirely.** A meta-analysis of log-with-zeros
transformations, replicating Chen & Roth (2024). Everything below is out of
scope: `utils/spec.py`, the `Spec` dataclass, `reestimate`, `verify` in that
module, `analysis_script.py`, `propensity_plot.py`, `prompts/run_all_analysis.sh`,
`utils/plots.py`, `utils/models.py`, `utils/evaluation.py`, and the eleven
`paperN` loaders (`hjort_poulsen`, `rogall`, `carranza`, `johnson`, `azoulay`,
`cao_chen`, `arora`, `fetzer`, `moretti`, `berkouwer_dean`, `sequeira`).

Concretely, you must NOT: port a Chen & Roth-style `Spec`; apply the five LHS
transforms (arcsinh, log1p, rescalings, extensive margin); add Poisson rows;
populate `target_coef`; verify against
`results/arcsinh-transformation-results.csv`; or read anything into your task
about logs, zeros, or units-invariance. If your paper's outcome happens to be a
log or a count, that is a coincidence and changes nothing.

**Your project.** Replicating published *interaction / heterogeneity* tables:
`utils/interact.py`, the `ISpec` dataclass, `interaction_script.py`, the
`"interactions"` sub-registry, `tests/test_replication.py`, `tests/golden.py`,
`tests/test_interact.py`, and `results/interactions/`.

Your outcome variable is simply whatever the paper regresses, in the form the
paper uses it. There is no transform menu and no estimand machinery: the
estimator is whatever the paper ran, the quantities are its coefficients, and
the job is to land on the published numbers.

**Registering an interaction-only paper.** The top-level `"load"` / `"spec"`
keys belong to the other project. Your paper has no such spec, so **omit both
keys entirely** and register it with `"chen_roth_id": None` and `"status":
"interaction-only"`. Which keys an entry has is what says which project it
belongs to; `build()` raises on its own if the Chen & Roth half is asked for.
Do not add a stub that raises, and do not invent a Chen & Roth spec to fill the
slot. All of your real work lives in the `"interactions"` sub-dict.

### Before you write anything

Every line you read stays in your context for the rest of the run, so read
the repo's shared code by name: `grep -n` for the section or function, then
`sed -n` that range. Start with these, in this order; open more of them when a
specific question needs it.

1. `data_scripts/__init__.py` — the module docstring, then the
   `"W3186756403":` entry. The rest is 3,000+ lines of other papers.
2. `utils/interact.py` — `class ISpec` in full; for `_formula`, `terms`,
   `columns`, `estimate` and `verify`, the docstrings first. This is your
   entire estimation stack; you should not need `utils/spec.py`.
3. `data_scripts/W3186756403.py` — the reference implementation (Stata package,
   interactions only). For Phase 1: the header comment, `load`, `_itt` and
   `INTERACTIONS`. For Phase 2, when you get there: `mega_inventory`,
   `freeze_inventory`, `_mega_spec`, `_build_mega`. Everything after `MEGA =`
   is the causal-forest half and not your job.
4. `tests/test_replication.py` — the test names and their docstrings.

When you need a pattern the reference lacks (2SLS, an `.rds` loader, a lasso
control set), `grep -ln` for it across `data_scripts/` and read the matching
function rather than another paper's whole module.

**Your own paper is different: read whatever you need to get it right** — the
package README, every do-file, logs, the appendix, the data itself. Two habits keep it
cheap without limiting it: `grep` to the part you are after before reading a
long file, and send anything that prints hundreds of lines to a scratchpad file first,
then `grep` or `head` it.

---

## Phase 1 — replicate the published interaction table(s)

**Goal:** reproduce, exactly, the interaction/heterogeneity table(s) the paper
prints, and verify every published number. A paper that prints no interaction or
heterogeneity table is not screened out: replicate the printed ATE column the
sweep's baseline will use — same arm, outcome, controls, FE, clustering and
sample — match its N exactly and every printed coefficient within `tol`, and
register it as a spec with no moderator.

### Steps

1. **Locate the table.** Find the do-file/R script that produces it and the
   `.tex`/output file it writes. Prefer the package's own table output over the
   PDF when both exist — it carries more digits.

2. **Write the loader.** `data_scripts/<PAPER_KEY>.py`, exposing:
   - `load(path=...) -> df` — the analysis frame, decorated `@lru_cache(maxsize=None)`.
     Data construction only. It must NOT build interaction columns (see below).
   - one `spec` builder per table column, taking no arguments and returning an
     `ISpec`. Use a factory when columns differ only parametrically, as
     `W3186756403._itt(...)` does.

   If the table's columns share a frame, they must name the *same* loader. That
   is the whole point of the load/spec split, and the cache makes it free.

   **Port bugs and Stata idioms; do not tidy them.** An off-by-one, a `replace`
   that silently swallows missings, a control built from a typo'd variable — if
   the published numbers came out of it, reproduce it and comment it. Tidying it
   on the way past yields a column that misses by a little and cannot be
   diagnosed.

3. **Express the model structurally.** `ISpec` takes:
   - `arms` — the paper's main treatment arms
   - `interacted` — what the arms are crossed with. **Full cross including main
     effects**: `arms=[a1,a2], interacted=[m]` fits `a1 + a2 + m + a1:m + a2:m`.
     Empty means the arms enter additively.
   - `controls` — everything else, in bulk. A plain string is a column; a
     2-tuple `("a","b")` is their product, fitted as `a:b`.

   **Never materialize an interaction column in the loader.** Interactions are
   the spec's job. Coefficient names come back as `a:b`, so `targets` keys use
   that form.

   If the paper runs *subgroup splits* rather than an interacted regression,
   register one `ISpec` per subgroup differing only in `sample`. Do not convert
   a split into an interacted spec or vice versa — they are different estimands
   (a split lets every coefficient vary, an interaction lets only the treatment
   effect vary).

4. **Transcribe the published values BY HAND** into `ISpec.targets` (per
   coefficient), `ISpec.n` (the sample size the paper prints), and `ISpec.tol`
   (the precision the table was printed to — a table with 2 decimals pins a
   coefficient to ±0.005 and no tighter).

   **This is the part that must not be automated.** Never generate `targets` from
   your own output, and never loosen `tol` to make a check pass. If a number does
   not match, the data build is wrong — fix the build, or document precisely why
   it cannot match. A test whose expected values come from the code under test
   answers a different and much weaker question.

   A 3-decimal table means 0.0005. If the numbers do not land there you have a
   failed replication (standing decision 5), not a tolerance question, and Phase
   2 does not run for that column. Disclosing a loosened `tol` does not make it
   acceptable.

   Put anything a reader must know before trusting a number in `ISpec.note` —
   above all when the paper's inference differs from ours (randomization
   inference, bootstrap, etc.).

5. **Register** under `PAPER_KEY` in `data_scripts/config`, with bibliographic
   metadata and an `"interactions"` sub-dict, one entry per column.

6. **Verify.**
   ```
   .venv/bin/python interaction_script.py -d PAPER_KEY     # every spec
   .venv/bin/python -m pytest tests/ -q --ignore=tests/test_replication.py \
       --ignore=tests/test_mega_driver.py --ignore=tests/test_forest_clusters.py
   .venv/bin/python -m pytest tests/test_replication.py -q -k PAPER_KEY
   .venv/bin/python tests/update_golden.py PAPER_KEY       # review the diff
   ```
   Those two pytest lines are the whole test obligation, and they are what CI
   runs on your diff: the fast suite, and your paper's replication. Never run
   the bare `pytest tests/ -q`, nor a heavy file without `-k PAPER_KEY`: they
   re-estimate every paper.

### Standing decisions

These were settled after the first batches and are no longer open questions.
Follow them; do not re-litigate them per paper.

1. **A table that prints no N is still registered.** Set `n_unpublished = True`,
   leave `n=None`, transcribe `targets` as usual: the coefficient checks still
   run, only the N check is skipped. Covers a cluster-only count and a table with
   no Observations row. NOT a way to dodge an N that disagrees — that is a failed
   replication and stays one.
2. **A 2SLS / IV column is registered, not skipped.** `ISpec` has `endog` and
   `instruments`; the arms are normally the instruments, `arms` is left empty,
   and the coefficients come back on `endog`. Register the paper's actual
   estimator. An ITT analogue *as well* is welcome; *instead* is a gap to report.
3. **Prefer the published tables.** `survey/data/pdfs/` is often a
   *working-paper* PDF, which can print a different table from the published
   one — different columns, N and coefficients, all plausible. Prefer the
   package's own `.tex`/`.csv`; failing that, the **published** article and
   **online appendix** from the publisher (the AEA `.appx` URL, the journal's
   supplementary page). When the published version is paywalled, a working
   paper or manuscript is an acceptable source: say which version every target
   comes from in `ISpec.note` and REPORT.md.
4. **A failed replication is NOT a reason to skip a table — register it anyway.**
   A column that does not reproduce is the most informative thing you can find,
   and dropping it converts a finding into a silence. Transcribe
   `targets`/`n`/`tol` by hand exactly as for a working column, register it, let
   the suite fail, and report what missed, by how much, and what you ruled out.
   Do NOT loosen `tol`, invent an `n`, set `n_unpublished` to dodge a disagreeing
   N, drop the offending coefficients, or leave the table out. A red test
   carrying a correct transcription is the honest artefact.

   **And do not silence it.** `ISpec.known_failure` is not yours to set. It marks
   a mismatch someone has already inspected and diagnosed in writing, and it is
   registered in a separate PR that does nothing else; using it here converts
   your finding into a green tick before anyone has read it. Leave the test red,
   describe the miss in `REPORT.md` — what missed, by how much, what you ruled
   out — and say in your report that the spec is a candidate for a
   `known_failure` PR. Same for every other route to the same end: no `xfail`
   marks, no `skip`, no edit to `tests/`, no removal from the golden records.
5. **A code-only package is screened out** with a short REPORT.md and no registry
   entry: an entry whose `load()` raises turns a data-availability fact into a
   permanently red suite.

### Phase 1 is done when

- [ ] `N` matches the paper **exactly** for every column
- [ ] every coefficient the paper prints matches within its `tol`
- [ ] both pytest lines are clean apart from the misses you
      registered and reported, with no test modified to accommodate you
- [ ] golden records written, and you have stated in your report what changed.
      `update_golden.py` also rewrites unrelated papers with 6th-decimal SE
      jitter — revert those; your diff covers your paper only
- [ ] `paper_table` output visually reproduces the published panel

If a column cannot be made to match, **stop and report it** with the discrepancy
and your diagnosis. Do not paper over it, do not silently drop the column, and
do not proceed to Phase 2 for that column.

---

## Phase 2 — the mega-replication

**Goal:** re-run the paper's interaction analysis against **every** candidate
variable in the data, not just the handful the authors chose, and record for
each one the evidence a reader needs to judge it. The output is a
heterogeneity table far wider than the published one, and an inventory the
causal-forest agent chooses its `X` from.

**You record; you do not exclude.** Whether a column is pretreatment, observed
equally by arm, a duplicate or a meaningless date fragment is decided later,
by the causal-forest agent, from what your inventory says. Only two things keep
a column out of the sweep: its design `role` (below) and `entry_kind`. Every
other column is swept, however doubtful, and carries its evidence.

### Step 1: record the evidence

Every column gets two kinds of field. The **declared** ones are your judgement,
read off the questionnaire, the cleaning code and the paper, each with a
citation. The **computed** ones come from `utils.mega.inventory_evidence`.

**Declared, per column:**

| field | what it says |
|---|---|
| `role` | the column's part in the design: `arm`, `outcome`, `cost`, `unit_id`, `stratum`, `propensity`, `control`, `sample_filter` (not swept), or `design_label` for a wave, round, session, date or enumerator (swept). Empty for an ordinary candidate |
| `timing`, `timing_source` | `before`, `after` or `unknown`: measured before or after the treatment was applied or communicated to subjects, and the questionnaire page, do-file line or fieldwork note that says so |
| `from_draw` | `True` where the column is derived from the assignment: a stratum-balanced index, a fitted propensity, a peer's arm |
| `nan_source` | where the column's blanks come from, as far as the package documents it: item nonresponse, a skip pattern, a module not fielded in some sessions, an interview gated on treatment |
| `nominal` | declared for every unordered numeric code (Step 3) |
| `key_variable`, `construct` | see below |
| `components` | for a column you built from others, the `\|`-separated source columns |

`timing` is never read from variable names: prefixes mark survey blocks, and a
block called "baseline" is not evidence of when it was fielded. A survey
fielded after the draw but before anyone learned their arm or received anything
is `before`; say so in `timing_source`. Where the sources do not settle it,
`unknown` is the honest value. For a column you built, `utils.mega.inherit`
fills `timing` and `from_draw` from its `components`.

**Coverage 1.000 proves nothing**: median-imputed and zero-filled columns read
as fully covered. Find the fill in the cleaning code and note it in `nan_source`.

**Key variables** (income, consumption, assets, education, age, sex, the
baseline outcome) are listed in a module-level `KEY_VARIABLES` tuple in
`data_scripts/PAPER_KEY.py`, with `key_variable` set and `construct` naming
which of the seven it is. A key variable is one measure per construct: where
assets (or consumption, or income) come only as separate items, build one
aggregate in the loader (a count of owned items, an index, a total), list that,
and give it `components`. The list covers the respondent and, where recorded,
the spouse and the household head; business revenue, inventory or hours are
ordinary candidates. Many sparse items of one module are likewise aggregated
into a few columns, with `components`, and the items stay in the inventory too.

**Computed, per column:** call `inventory_evidence` once in `freeze_inventory`
and merge its result onto the inventory. Pass it the arm, the cluster and the
randomisation unit, the design's cells where the draw probability differs
across them (waiting lists, strata, waves drawn at different rates), the sweep's
`y`, every candidate first-stage outcome, the `design_label` columns, and the
`levels_kept` of every binary and categorical. Its docstring says what each
field measures. A field it cannot compute is left out; do not write a module
copy of any of them.

> The trap in general form: any module fielded after randomization — a follow-up
> session, a second interview, an in-person test — is observed only for subjects
> who responded to treatment. Such a block is frequently the richest-looking part
> of the file, and its coverage will quietly equal the take-up rate rather than 1.
> Pass every candidate first-stage outcome to `inventory_evidence`, not just the
> headline one, and set `timing` from the fieldwork record, so the
> `obs_if_no_<outcome>` and `timing` fields show it.

### Step 2: build the expanded analysis

The mega is **not** a second framework. It is more `interactions`: the same
`{name: {"load", "spec"}}` shape, in a sibling `"mega"` key. Everything the
driver needs is a static dict; nothing is computed at import time.

**Choosing the sweep's specification.** W, Y and cost are chosen once, before
anything is estimated; the published column is the default, not the answer. State
all three and your reasons, and where the design blocks a preferred choice, take
the published one and name the constraint.

*W — the randomised lever, at the finest level available.* `arms` says what the
table interacts, not what the experiment assigned. Prefer an arm randomised per
individual: check it varies within the paper's cluster
(`df.groupby(cluster)[w].nunique().gt(1).mean()`). An arm constant in every
cluster gives you as many independent draws as there are clusters, however many
rows the frame carries; that count, not the row count, is the sweep's real width.
Report it. A regressor that is a *consequence* of treatment (ending up above an
asset threshold) is not a lever: sweep the real arm, report the paper's as a
finding. If the paper has no randomised arm to sweep (the lever is a measured
trait, a regression discontinuity, a fixed order, a non-random rollout), still
port and sweep it, but set `"exclude": True` and a one-sentence
`"exclude_reason"` on its `config` entry, which keeps it out of the
meta-analysis.

*Y — the most natural utilitarian outcome*, in units a policymaker would weigh —
earnings, take-up, a test score — not an index built for the paper's inference.
Tie-break on observability: `P(observed | treated) − P(observed | control)` with
its se, and reject a materially non-zero gap, or the sweep reads differential
attrition as heterogeneity. Administrative records usually beat surveys fielded
through the intervention. Report the gap you kept.

*Cost — only where the paper gives a natural one*: a subsidy that depends on the
price drawn, capital disbursed, a per-attendee fee. Flat cost means none — say so
and move on. Where it varies per unit, **register a second base spec with cost as
the outcome**: same arm, controls and sample, identical moderator cross, in the
`_MEGA_TABLES` pattern. Its baseline might reproduce
nothing published, so it carries no `targets`; the published Y's baseline stays
the drift check.

**Moderator entry — one form per variable, no median splits.** The mega does NOT
reproduce the paper's functional form; Phase 1 already did that, and it is tested.
Each eligible variable enters exactly one way:

| kind | how it enters | eligibility |
|---|---|---|
| continuous | z-scored, interacted with the arm: every numeric column with 3+ values not declared `nominal` (counts, scales, ordered codes) | — |
| binary (0/1) | as-is | minority share ≥ 5% |
| categorical | one-vs-rest dummies, every level: strings and declared-`nominal` codes | ≤30 levels, each kept level ≥5% of the sample |

Do not exclude categoricals — expand them. "Field of study" or "region"
variables are often better questions than the paper's own moderators.
`entry_kind` keeps free text and >30-level codes out, with its reason on the
row. A name field or "Specify" item it lets through is swept; say what it is in
`reason`.

Keep the paper's arms, controls, fixed effects, clustering and sample filter
fixed. Vary **only** the moderator. The **no-moderator baseline must still
reproduce the paper's baseline column** — that is the check that the sweep did
not quietly change the specification, and it is mandatory.

**Sweep one outcome unless you can say why not.** Width comes from moderators,
not from outcomes: every extra table multiplies the whole moderator set again,
and five outcomes x 200 moderators is not five times the evidence — it is the
same question asked of five correlated LHS variables. Take the paper's primary
outcome (or the one column its own heterogeneity table uses). Add a second table
only when the paper's design genuinely has two (two experiments, two follow-up
years the paper reports separately) — or when it has a per-unit cost, per above —
and say in the report why. If you find
yourself registering more than ~300 specs, stop and justify the count first.

Where the paper constructed a moderator it never used, use it and note it — an
author-defined but unpublished cut is worth flagging. That is a remark about
provenance, not a licence to go looking for the interesting result.

### Step 3: freeze it, in the paper module

The dependency chain is `data -> eligibility -> specs`. Freeze the middle link and
the spec set can be enumerated without opening a single data file, which is what
lets the registry hold data instead of a function call.

**Eligibility lives in the paper module.** Do not compute it in a side script:
an artefact whose generator is not in the repo cannot be audited or
regenerated. A column is swept when its `role` is empty or `design_label` and
`entry_kind` gives it a `kind`; nothing else enters the decision.

*Can it enter as a moderator?* **Call `utils.mega.entry_kind`.** It is
generic, already written, and returns `(kind, share, reason)` — put its `reason`
in the inventory verbatim. Do not reimplement its rules, and do not restate them
in your report or your module docstring: a transcription of a function is a
second copy that drifts. Read the function.

**`nominal` is a column your inventory DECLARES, never something inferred.** A
region code and a count are identical to `dtype`, and z-scoring the region code is
meaningless. Any numeric code with 3+ values that is not declared `nominal` is
z-scored, so declare every unordered code (region, sector, enumerator, occupation). Set the flag deliberately per variable
and pass it to `entry_kind`. Do not recover it by pattern-matching your own prose
reasons — that breaks the moment a reason is reworded.

**One artefact, two jobs — the frozen inventory.** Write it to
`data_scripts/inventories/PAPER_KEY.csv` with a generator in the paper module
(`python -m data_scripts.PAPER_KEY --freeze`, as the existing papers do). One
row per column of the source frame, the unswept ones included:

   | field | meaning |
   |---|---|
   | `variable`, `label`, `block` | source column, its Stata label, its survey module |
   | `coverage`, `levels` | from the frame |
   | the declared fields | Step 1: `role`, `timing`, `timing_source`, `from_draw`, `nan_source`, `nominal`, `key_variable`, `construct`, `components` |
   | `kind`, `enters_reason` | `entry_kind`: `continuous` / `binary` / `categorical`, or empty, and why |
   | `levels_kept` | for a categorical, the `\|`-separated levels above the floor |
   | `share` | for a binary, the minority share |
   | `reason` | anything a reader needs that no other field says: a fill found in the cleaning code, a date fragment, an author-built but unpublished cut |
   | the computed fields | `inventory_evidence`'s columns, as it returns them |

   Its **eligible slice** (`kind` non-empty) is the plan `utils.mega.plan()`
   reads, and `MEGA` is the cross of it. `levels_kept` is the load-bearing
   field: it fixes the dummy names (`d__<var>__<level>`), which is what makes
   the spec set enumerable without opening a data file.

   Every column is a row, so "we tested 79 variables" is a checkable claim and
   a reader can judge how much of the raw p<0.05 count is chance. The driver
   copies the whole file to `results/interactions/PAPER_KEY/mega/inventory.csv`
   so results ship with it. Paper-specific diagnostics are welcome — add them
   after the shared ones.

**Registry entries are data.** The paper module exposes two names and
`data_scripts/config` references them directly:

- `INTERACTIONS` — a **literal** dict. It carries the hand-transcribed
  `targets` / `n` / `tol`, and a transcription that is computed is no longer a
  transcription, so write it out and let the literal be the source of truth.
- `MEGA` — a module-level constant, the mechanical cross of the eligible plan
  with the paper's tables, built once at import. Writing out hundreds of
  combinations of an already-frozen list adds no information and buries the
  module; freezing the *decision* is the point, not the cross product.

Neither may be a call in the registry (`"mega": paper.mega()` is wrong,
`"mega": paper.MEGA` is right), and importing `data_scripts` must not touch data.
Specs are `ISpec` instances, never callables. Use `ISpec.meta` to carry each
spec's moderator, its kind and its level; the driver reads that and must never
parse meaning out of spec names.

### Step 4: report

- Results to `results/interactions/PAPER_KEY/mega/` as tidy CSV: `estimates.csv`
  (one row per `(spec, coefficient)`), `contrasts.csv` (one row per tested
  contrast with `estimate`, `se`, `n`, `p`), `inventory.csv`, and `balance.csv`
  (each moderator regressed on the arm). **Join it back against your findings** —
  every moderator you report carries its own balance p-value, because an
  imbalanced moderator produces apparent heterogeneity that is imbalance.
- **Assert `contrasts.csv` is unique** on `(spec, moderator, arm, coefficient)`.
  Duplicated rows make one fit look like several to anyone counting rows.
- **Do NOT adjust for multiplicity, and do not add machinery that does.** The
  sweep reports point estimates, standard errors and per-contrast p-values, and
  stops there; `utils.mega` deliberately carries no BH, no family construction
  and no joint tests. Report the raw p<0.05 count against its chance benchmark
  (`0.05 x n_contrasts`) and leave any correction to the reader.
- **What replaces the adjustment is the freeze, not a q-value.** The eligible
  set is fixed before anything is estimated and every column is on the record
  with its evidence, so a reader can compute whatever correction they want from
  `contrasts.csv` and `inventory.csv` against an honest denominator. A finding
  from a wide sweep is a hypothesis; say so in the report rather than deciding
  it with a threshold.
- **Give the raw p<0.05 count twice**: over every contrast, and over the
  contrasts whose moderator has `timing` `before`, `from_draw` false and no
  arm-observation gap at p < 0.05. That second count is a reading aid, not a
  filter; the sweep and `contrasts.csv` keep every contrast.

**Four failure modes to check for explicitly. Say what you found for each.**
Each is measured and reported; none removes a moderator from the sweep.

1. **Near-duplicate moderators.** Several source variables holding the same
   information return the identical estimate and read as several findings.
   `twin_of`, `twin_r` and `exact_function_of` name them. Report the
   **distinct source-variable count** next to the raw contrast count, counting
   an exact function or a twin at |r| > 0.9 once — a chance benchmark against
   an inflated denominator is a fiction.
2. **Failing specs — diagnose before you treat.** Read an actual traceback
   first. Mass failures are often `FormulaSyntaxError` from illegal dummy names
   rather than thin cells; fix the name. Report the failure count and cause.

   The thin-cell problem that IS real is **within-arm**: a moderator can hold a
   healthy overall share while being near-absent in one arm, and come back as
   the sweep's single surviving finding off a handful of rows.
   `min_arm_share` and `min_arm_clusters` measure it at the unit of
   randomisation, across every arm cell. Name every headline contrast whose
   level is under 5% of an arm, or held by fewer than 5 clusters of an arm
   where the arm is drawn per cluster: a level two villages hold is a two-draw
   contrast.
3. **Meaningless-but-eligible variables.** Date components (spell start *day*,
   graduation *month*) pass every mechanical gate and moderate nothing. Say so
   in the column's `reason`.
4. **Leverage artefacts in unwinsorized continuous moderators.** A variable that
   is zero for almost everyone, or that carries a data-entry outlier, produces
   small p-values off a handful of points. `mode_share` and `max_abs_z` flag
   them; inspect the moderator distribution behind every headline contrast and
   **report the artefact in prose**. Do NOT invent a winsorization or a filter after seeing what it
   removes — a rule chosen once you know which findings it kills is not a rule.

- A short markdown report at `results/interactions/PAPER_KEY/REPORT.md` covering:
  0. **every interaction / heterogeneity table the paper prints, and for each one
     whether you registered it — with a reason for every table you did not.**
     Enumerate the paper's tables first, then say which became specs. A table
     left out because it is 2SLS, prints no N, needs a withheld variable, is a
     subgroup split you chose not to convert, or conditions on a post-treatment
     outcome is a *finding about the paper* and must be named as such. "The
     paper's heterogeneity table" is never a complete answer when the paper has
     four of them; silently covering one is the single easiest way to overstate
     what replicated.
  1. what the published table was and that it replicates (with the numbers)
  2. the inventory: how many columns of each `role`, `timing` and `kind`, every
     `unknown` timing with what you tried, and every column whose evidence a
     reader should look at before trusting a contrast on it
  3. the expanded results — the raw p<0.05 count against its chance benchmark,
     then the largest contrasts as **hypotheses**, not findings. Nothing here is
     multiplicity-adjusted; write it so a reader cannot mistake a wide sweep's
     biggest coefficient for a pre-specified test.
  4. anything that did not work, and why

---

## Conventions you must not violate

- `load` and `spec` are separate registry entries. `load` is a callable
  returning a frame; **`spec` is an `ISpec` instance, not a callable** — every
  spec in this codebase is a pure literal that touches no data, so there is
  nothing to defer.
- Registry values are DATA. `"mega": paper.MEGA`, never `"mega": paper.mega()`.
  Importing `data_scripts` must not read a single data file; if it does, the
  freeze is not actually frozen.
- All loaders are `@lru_cache(maxsize=None)`. Consumers never mutate a frame they
  are handed — copy or filter first.
- Loaders never build interaction columns, and never build moderator columns for
  a variable that is not in the frozen eligible plan.
- Anything a script generates and the repo keeps must be generated by a script
  **in the repo**. An artefact whose generator lives in a scratch directory
  cannot be regenerated, audited, or trusted.
- Results go to `results/interactions/<paper>/<spec>.csv` — a directory per
  paper, not a flat `paper__spec.csv`.
- No hardcoded absolute paths. Dataset paths are relative to the repository
  root; scripts are run from there.
- Use `.venv/bin/python`, never bare `python3`.
- Data constructions that mirror original Stata should carry a comment naming
  the source file and line, as the existing loaders do.
- A paper PDF you download (article or working paper) goes to
  `survey/data/pdfs/<PAPER_KEY>.pdf` in the main checkout if that file is
  missing or is an older version; appendices stay in your scratchpad. Name the
  file in your report.

## Report back

State plainly: what replicated, what did not, which columns your evidence flags
and why, and which judgment calls you made that a reviewer might disagree with. Report
failures as failures — a column that does not match is a finding, not something
to hide. Do not claim a check passed that you did not run.
