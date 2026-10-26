---
name: causal-forest
description: Turns a paper's frozen mega specification into a causal-forest targeting problem — a registered `ForestData` prep, its Qini figures, and a written report. One agent per paper; spawn it with the registry key. Use when a paper already has a mega sweep and the question is whether ranking people by predicted benefit beats treating at random.
---

You are building a causal-forest prep for one paper in this repository. The
question every prep answers is the same: **if the intervention can only be given
to some people, does ranking them by predicted benefit beat picking at random?**
Everything below exists to make sure that question is being asked of something
real.

## Your assignment

You are given a single `PAPER_KEY`. If the spawn prompt did not name one, stop
and ask. If it named a variant to add to an existing prep, build only that.

**Prerequisite: the paper must already have a frozen mega inventory** at
`data_scripts/inventories/PAPER_KEY.csv`. Its eligible slice is where `X` starts
— the pretreatment timing judgements are the expensive part and they are already
done. If there is no inventory, stop and say so; the paper needs the
`replicate-and-expand` agent first.

Work only on `PAPER_KEY`. The one shared file you edit is
`data_scripts/__init__.py`, and only your own paper's rows in it; everything
downstream is derived from that entry.

**Not your project.** The log-with-zeros half — `utils/spec.py`, `utils/models.py`,
`analysis_script.py`, the eleven `paperN` loaders. It shares the registry and
nothing else. Do not port a `Spec`, and do not touch `utils/models.py`;
`utils/forest_models.py` is the module for this half.

**Nor is `dashboard/models.py`:** it is the model axis for every paper, and a
key added there refits all of them.

### Before you write anything

Every line you read stays in your context for the rest of the run, so read the
repo's shared code by name: `grep -n` for the function, then `sed -n` that
range. This brief is already in your context; there is no need to re-read its
file. Start with these, in this order; open more of them when a specific
question needs it.

1. the preps already built — `ds.papers_with_forests()`, `ds.forest_specs(key)`,
   and each variant's `FSpec.design_note`
2. `utils/forest.py` — `class FSpec`: the contract your registry entry fills.
3. `utils/uplift.py` — `LEARNERS`, then the docstrings of `compute`,
   `qini_curve` and `_cross_fit`; this is what consumes your prep. In
   `dashboard/models.py`, the model entries: which learners every prep is
   fitted under.
4. `data_scripts/W3186756403.py`, from `_FOREST_ARM` to the end — the reference
   prep: frame, covariates and the loader itself.
   Copy its shape.
5. **What runs on your prep.** `python -m dashboard.build_plots -d PAPER_KEY`
   fits it. `tests/test_forest_registry.py` checks the `FSpec` labels, and
   `tests/test_forest_clusters.py` checks the `ForestData` contract against your
   declared `exceptions`. Read a test only when it fails; its message says what
   it needs.

**Your own paper is different: read whatever you need to get the design
right** — its module, its mega inventory, its interactions `REPORT.md`, the
paper, and the replication package's randomisation and cleaning code. The paper
is `survey/data/pdfs/PAPER_KEY.pdf` in the main checkout. Two
habits keep it cheap without limiting it: `grep` to the part you are after
before reading a long file, and send anything that prints hundreds of lines to
a scratchpad file first, then `grep` or `head` it.

## Where each decision comes from

Two sources, and they are not interchangeable.

**The paper decides the design.** What was randomised, over what unit, at what
probability, inside what blocks, and what the intervention costs. The sections
worth reading, whatever they are called: the experimental-design or
randomisation section, its footnotes -- unequal probabilities are usually
demoted to one -- the design figure's note, the table notes, which say what the
authors clustered and absorbed, and the pre-analysis plan or appendix where the
body is vague. Quote the sentence you relied on.

**The frame decides nothing, but it confirms.** Counts, coverage, the spread of
cluster sizes, whether a column is constant within a group. Where the frame and
the paper disagree, the frame is a filtered slice of the experiment and the
filter is the thing to find -- the paper is not wrong about its own design.

**The replication package settles what a column is** when the paper does not:
the do-file or script that builds the variable says whether it is an assignment
label, a post-treatment quantity, or a survey weight. Read it before assuming
from a name.

## The output contract

Every prep is one callable returning a `utils.forest.ForestData`, built with
keywords:

```python
return ForestData(X=X, y=y, c=c, w=w, weight=weight, descriptions=descriptions,
                  rand_unit=rand_unit, strata=strata, propensity=propensity,
                  additional_adj=additional_adj)
```

| | what | shape |
|---|---|---|
| `X` | pretreatment covariates, all float | `(n, p)` |
| `y` | the outcome | `(n,)` |
| `c` | the cost of treating, usually borne only where treated -- see §5 | `(n,)` |
| `w` | the treatment, binary | `(n,)` |
| `weight` | the AUTHORS' own survey or sampling weight, else ones — never one that corrects for attrition, see §2 | `(n,)` |
| `descriptions` | `{column: label}` for `X`, in its column order, from `utils.mega.describe_columns` | `p` entries |
| `rand_unit` | the id of the randomisation unit, what the coin was flipped over: `np.arange(len(y))` where the draw is per row, the group where a group was drawn, the group drawn into a saturation in a saturation design | `(n,)` |
| `strata` | the id of the block within which the design purposefully balanced the treated share, or `None` -- §2 | `(n,)` |
| `propensity` | the probability of treatment conditional on the confounders, or `None` -- §2 | `(n,)` |
| `additional_adj` | what the outcome nuisance conditions on beyond `X`: the design's confounders, and the columns §3 takes out of `X` into it -- all float, like `X`. Never the strata, never the unit | `(n, k)` |

`weight` and `propensity` are different objects and never multiply into one
another -- see §2.

**`strata` and `propensity` together** -- blocks within which the treated share
was purposefully balanced, inside groups set to different shares, say -- are
returned together where the design has both. The
strata balance check then judges each stratum against its units' propensities.

**Shared code decides the clustering.** What the folds and grf's OOB hold out
whole comes from `rand_unit` and `strata` (`utils.forest.fold_groups`): the stratum
where strata average fewer than 10 units, so a held-out unit's stratum-mates
cannot give its arm away, and the unit otherwise. Strata of 10 units or more are
demeaned out of `y` and `c` instead (`utils.forest.demean_groups`). Neither id
is ever a covariate or fitted on.

Where `w` varies inside the unit -- a saturation, a unit redrawn each wave,
members moved after assignment, coverage that overlaps -- keep the unit: a
saturation is declared in `FSpec.exceptions`, anything else goes to the owner
(§2). Never split or reshape a unit to make `w` constant inside it.

Variants are keyword arguments on that one callable (`arm=`, `outcome=`,
`covariates=`), registered with `partial`. Do not write a second loader.

**One row per unit.** Where the source is a panel, pick a wave or collapse, and
state which. Repeated rows double-count a unit and let one land on both sides of
an honest split. Prefer a wave whose re-interview coverage is balanced across
arms over the paper's headline wave.

---

## Glossary

Each term names one thing, and they substitute for one another easily.

| | what it is | where it goes |
|---|---|---|
| **row** | what one row is -- a school, a household-year | `FSpec.row`; nothing else |
| **randomisation unit** | what the coin was flipped over. May be coarser than the row, in which case the row inherits its arm. Where the design **saturates** -- a group drawn into a saturation, then its rows drawn at that saturation -- we name the outer draw as the randomisation unit, so `w` varies inside it. The saturation is the propensity the group was drawn at, so it stays out of `X` like any other propensity | `rand_unit` |
| **stratum** | a block within which the design purposefully balanced the treated share, so it treats the same share of its units as every other block, give or take one unit for rounding. A block set to its own deliberate propensity is a confounder | `strata`; never `propensity`, never `additional_adj` |
| **confounder** | a variable the propensity genuinely depends on, because the design set it that way or something unrandomised does | `propensity`, `FSpec.confounding_variables` |
| **propensity** | the probability a unit was treated, as the design set it: one value where every unit was drawn alike, different values only where the design set them on purpose (a round over-weighted, seats over applicants, a redraw by an earlier arm). Never a realised share from rounding or chance | `propensity`, else `None` |
| **cluster** | what the folds, grf's OOB and the standard errors hold together: the stratum where strata average fewer than 10 randomisation units, else the randomisation unit. Derived by shared code from `rand_unit` and `strata`; the authors' own choice is "the authors' SE clustering" | nothing to return |
| **attrition** | units the design assigned whose outcome or cost was never recorded. Not something you correct for, and not something you drop -- §6 | the rows stay in what you return; measured downstream |
| **weight** | what the AUTHORS weighted by: a survey or sampling weight their own regressions carry. One they built to correct for **attrition** is a different object and does not go here | `weight`, normalised to mean one, else ones |

## The checks, in this order

**Which cases to register is your decision.** A case is one variant: one `w`,
one `y`, one `X`; choose them from the paper and say why in the report. Each
arm §1 does not pool is its own case. Each case has one outcome; register a second outcome or wave as its own case only where
the paper reports it as a main result. Add the compact variant wherever §3
requires one, on the same sample. Two variants whose outcomes are
near-duplicates, or a compact variant identical to the wide one, are one case.

### 1. Choose `w`

`w` must be something a coin flip assigned. This is the check that fails hardest.

A published heterogeneity table is a statement about the *table*, not the
experiment. Two failures to rule out explicitly: a sample filter that holds the
arm constant, leaving no experimental variation at all; and a contrast that is a
*post-treatment state* — whether a unit ended up above a threshold — which makes
the forest estimate the heterogeneous effect of having ended up there, with the
sign built in. Take the randomised variable, not the printed one.

**`w` is a costly intervention** -- something a planner spends a budget on, one
unit at a time -- against the paper's control arm. That is the question this
half of the project asks, and an arm with no cost behind it leaves the Qini's
x-axis as the treated share and nothing more. A costless lever -- an
information screen, a label, a nudge -- is not a `w`; in a design with both, it
is a randomised layer of `X` (§3).

**Pool costly arms when the interventions are close in spirit**, judged by the
type of what is given, not its size -- a loan and a grant are both money, two
curricula are both one preschool -- and make a separate case for each
otherwise. Say which you did and why.

### 2. Design: the randomisation unit, the strata and the propensity

**Start from the paper's randomisation sentence**, read in the paper itself:
its design or randomisation section, not the module header or the do-files.
Quote what it says was drawn, over what, within what, and at what propensities.
Every answer below has to agree with it; the frame only confirms the counts.
Fixed effects in the authors' regressions are not evidence of strata: blocks
used only as balance variables, in a re-randomisation, or as controls are not
blocks within which the treated share was purposefully balanced.

**The randomisation unit → `rand_unit`.** What the coin was flipped over.
Check the frame agrees:

```python
d.groupby(RAND_UNIT)[arm].nunique()   # >1 anywhere means `w` varies within
```

An arm constant in every unit means the effective draws are the units, however
many rows the frame carries — that count is the binding limit on anything
sayable about CATEs, and no amount of unit-level covariate detail relaxes it.
Report the number, and the spread of their sizes.
Name it in `FSpec.randomization_unit` as a label -- "a village" -- and the
blocks within which the treated share was purposefully balanced in
`FSpec.strata` -- "union x baseline-score tercile" -- left empty where the draw
is unstratified.

**`w` varying inside is the usual disqualifier, but not under saturation.**
There the outer draw sets a group's saturation and the inner draw takes rows
inside it, so `w` varies within the unit that was drawn and that unit is still
the randomisation unit. Ask which draw decided the propensity the other ran at.

**An arm-defined grouping is not a unit.** Where `w` is constant inside a
group because its label determines `w`, that is construction and not a draw.
Ask what would have varied had the coin landed the other way.

**Strata, confounders, or neither.** Any grouping within which the paper says
the treated share was balanced, or that the propensity depends on, is one of
these:

| what the paper and the data show | it is | it goes to |
|---|---|---|
| every block treats exactly the same share of its units, give or take one unit | a **stratum** | `strata`, with every unit whole inside one |
| a propensity the design set on purpose to differ, or one something nobody randomised sets | a **confounder** | `propensity`, `FSpec.confounding_variables` and `additional_adj` |
| shares that differ only because an integer count will not divide evenly | rounding | nowhere -- never `propensity` |
| a realised imbalance the design did not set | chance | nowhere |
| blocks within which each unit got its own independent draw at a common propensity, so shares balance only on average -- the realised counts scatter around the share as binomial draws do, not within one unit | **not a stratum**: the block never enforced balance | nowhere as a block; a characteristic a planner observes (group size, region) stays in `X` |
| blocks the paper calls strata whose realised shares are unbalanced *within* the draw due to 1) an implementation error or 2) authors not really trying to balance within strata and flipping a coin, a missed balance target -- rather than by a known later step (a sample filter, a dropped arm, leftovers drawn apart, in this case ask a question) | **not a stratum**: the stratification did not operate | nowhere; consider for `additional_adj` or `X` only where the blocks add information, are few, and no score summarises them -- the score goes there instead |
| blocks within which the treated share was purposefully balanced *and* a propensity that differs on purpose | both | `strata` and `propensity`; the balance check reads the strata against the propensity |

`propensity` is P(treatment | confounders), and the confounders are the ones
the randomisation sentence names. Most designs have none: one probability
reached every row, and `propensity` is `None`. A confounder looks like this:

* **the propensity changed over time** -- W3124047731 over-weighted the
  treatment arm to about 70% in rounds 1-3 and split later rounds evenly, so
  the round is the confounder;
* **capacity set the propensity** -- W2896469619 offered each waitlist's seats
  down a lottery ranking, so the waitlist's seats over its applicants (0.375 to
  0.909) is the propensity;
* **an earlier draw set the propensity** -- W2799563782 redrew year-2 loans
  within the year-1 arms at a different share in each, so the year-1 arm is
  the confounder.

For strata, report the number of strata and of units, and their sizes. Check
the whole design with `resid_w_ate` in the record: it should sit at 1.

**Computing the propensity.** Compute it at the level the paper sets it. It may
be estimated as a share within the confounder's groups where the paper gives no
number, but **only the named confounders condition it** -- a covariate that
predicts the arm in this sample is not one of them, and there would be no end
to the columns that qualify. It never multiplies into `weight`, which carries
the authors' own sampling weight and nothing else: every learner reads that slot
as a training weight. It is unclipped, since a group with no treated unit is
one to look at rather than to floor.

**What looks like a design variable and is not:**

* a **saturation** -- a group drawn into a propensity, its rows drawn at that
  propensity. The outer draw is the randomisation unit, and because the
  propensity was itself drawn there is nothing to carry in `propensity`.
* **attrition** -- a probability of being surveyed, re-interviewed, tracked or
  found again. It is not the propensity and does not belong in `propensity`. Do
  not estimate one, and where the paper publishes its own -- a shipped column,
  or a first stage in its appendix -- leave it out of `weight` too. The
  glossary's entry says where those rows do go.
* **a covariate.** The propensity itself is not one -- nor a treated share
  computed off `w` -- and stays out of `X` (§3). The confounder the propensity
  depends on is judged like any other column: a wave or recruitment cohort is
  out because it is not portable, a characteristic stays. A variable the
  propensity depends on only by accident is an ordinary column.

**Declare what the design breaks on purpose.** `tests/test_forest_clusters.py`
checks, on every prep, that each unit sits in one stratum, that `w` is constant
within the unit, and that each stratum treats its expected count within one unit
-- the common share, or the sum of its units' propensities where the prep has
one -- or, failing that, that the strata balance better than 95% of redraws that
ignore them (the arm reshuffled among units of one propensity).
Only the causes below may be declared in `FSpec.exceptions`, as
`(check, reason, limit)` with the most units or strata that may fail it:

| check | allowed cause |
|---|---|
| `w_within_unit` | a saturation design: groups drawn to a treated share, units drawn inside them |
| `strata_balance` | leftovers drawn apart: the units left over where a block does not divide by the arm split, drawn together across blocks or by a separate coin, as the paper or package describes the draw |

Any other failure is a prep to fix or a question for the owner: record it in
`questions.json` (the consultation table below) and declare nothing until the
owner answers. Never set `FSpec.exceptions_approved` yourself, not even for a
cause in the table above: the owner sets it.
Strata imbalanced only because units were lost after the draw -- attrition,
enrolment after the draw, a sample filter -- are still strata, and are never
declared as an exception: hand over every assigned unit (§6), and the check
passes. Where the package ships only part of the draw, so the lost units cannot
be restored, set `FSpec.full_draw_in_sample=False`: the balance check is skipped,
and the report says the attrition figures cover the shipped units only.

**Consult the owner** on the design cases below: record each in
`questions.json` (Report back), with what the table asks for and the reading
the prep takes meanwhile.

| case | how it shows | what to report |
|---|---|---|
| **strata off the common share** | a stratum misses the common treated share by more than one unit and the strata vary like an unstratified draw (the balance check fails), for any cause other than units lost after the draw or leftovers drawn apart | how many strata miss it and by how much, the permutation quantile (against 0.05), the causes found, and what the package and paper say about why |
| **unit crosses strata** | a randomisation unit sits in more than one stratum, so `tests/test_forest_clusters.py` fails on it | how many units, and what the package and paper say about why |
| **`w` varies inside a unit** | `w` differs between rows of one randomisation unit, so `tests/test_forest_clusters.py` fails on it, and the design is not a saturation | how many units, and what the package and paper say about why |
| **a saturation design** | groups drawn into different propensities, units drawn inside them | the saturations, and how the prep carries them |
| **an unusual draw** | a row reached by several randomisation units, a unit redrawn across waves, units moved after assignment | the structure in one paragraph, and why the contract does not fit |
| **authors' design description in doubt** | the authors' description of the design is ambiguous, contradicts these instructions, or is evidently wrong: the paper or package says one thing and the data or this prompt another, or says too little to decide | what each source says, and the reading you would take |

**Spillovers.** Set `FSpec.spillovers_prevalent`: `True` where a row's outcome
depends on other rows' treatment, within an arm or across arms -- controls
living among treated neighbours, or treated schools competing for the same
pupils, as in a saturation design -- `False` where the design or the paper rules
it out. Say in the report what the paper says about spillovers and what it
finds.

**The authors' SE clustering is a different question.** That grouping is where
the authors let outcomes correlate; the cluster is what shared code derives
from `rand_unit` and `strata`. Say where the two differ.

### 3. Choose `X`

`X` is what the forest may split on, so every column has to be something a
planner could target on: a fact about the unit, known before assignment, that a
new population would have too. The mega inventory clears one row per usable
column, which suits a sweep fitting moderators one at a time; a forest sees
them all at once, where near-duplicates split variable importance and
identifiers add noise, so more comes out here. Each column out is recorded with its
reason. It goes to `additional_adj` only where the table's last column says so.

| reason | what it is | how to decide | into `additional_adj` |
|---|---|---|---|
| **post-treatment** | measured after the treatment was applied or communicated to the unit | when the subjects learned their arm, against when the column was measured. Neither the draw's date nor the survey's is the line: a survey fielded after the draw but before anyone was told is pretreatment, and a whole module fielded after subjects knew is post-treatment | no |
| **propensity** | the probability of treatment itself: the propensity, a treated share computed from `w`, a saturation | is the column the propensity, or computed from `w`? It never enters `X` | yes |
| **not portable** | a label of the study's own timeline or logistics: wave, round, recruitment cohort, survey date, enumerator, session or batch id | would a planner targeting new units observe this value for them? A study's wave never recurs, so a rule split on it applies to no one outside the study. Age and birth cohort are characteristics and stay | yes |
| **leaking** | the column predicts the arm across held-out randomisation units, usually because it identifies the unit | constant within the randomisation unit and, with its kind, pinning the unit down; or the record's `arm_leakage_auc` well above 0.5, traced to the columns that carry it | no |
| **re-encoding** | carries nothing a kept column lacks: a variable beside its yes/no dummies, a median split, a sign flip, a complement (`employed` beside `unemployed`), a string beside its numeric recode | an exact or near-exact function of a kept column; keep the richer one. A tree finds its own threshold | no |
| **near-identifier or debris** | free text ("specify"), ids, date fragments, second and third spells of a repeated block | no stable meaning across rows | no |
| **no variation** | fewer than two levels reach the within-arm floor | the inventory's floor, already applied there | no |

**Low coverage is not a reason:** a partly observed column stays as `NaN`, and
sparse items of one module are aggregated, not dropped.

**Consult the owner** on the cases below: record each in `questions.json`
(Report back), with the numbers that show it and the reading the prep takes
meanwhile.

| case | how it shows | what to report |
|---|---|---|
| **key variable measured after treatment** | a key variable whose survey or module was fielded after the treatment was applied or communicated to subjects -- after the draw alone does not count | when it was measured, against when subjects received the treatment or learned their arm |
| **large baseline imbalance** | a kept column that differs by arm well beyond chance | the difference, in standard deviations, its p-value, and what the package and paper say about why |
| **observed differently by arm** | the observation rate differs by arm by at least 5 percentage points with p < 0.01, over every assigned row (within the propensity's cells where there is one) | both rates, the p-value, the source of the NaNs as far as it is known, and what the package and paper say about why |
| **a blank that encodes the design** | a column missing by date, session, wave or cohort, so that a split on the blank is a split on timing or on the arm | which rows are blank, and the design label that matches them |
| **leakage not traceable** | `arm_leakage_auc` well away from 0.5 with no column or block that explains it | the AUC, and the per-column or per-block AUCs tried |
| **top feature looks wrong** | after the fit, a column leading the importance table that is a design artefact, near-constant, or implausible as a moderator | the column, its rank, and why it looks wrong |

**Key variables** (income, consumption, assets, education, age, sex, baseline
outcome) are listed in the module's `KEY_VARIABLES` and are never excluded for
leaking or for observation by arm; one measured after treatment goes to the
owner, as above. Only a key variable that barely varies is left out, by the
inventory. A key variable is the inventory's one aggregate per construct (an
asset count or index), and that aggregate is the construct's column in the
compact variant too.

**Leakage is read off the record.** `arm_leakage_auc`
(`utils.uplift.arm_leakage_auc`) predicts `w` from all of `X` on whole held-out
units with the fit's own booster and folds: 0.5 is chance. Well above it, a
forest splits on what identifies the units and reports their difference as
effect heterogeneity: drop the columns that carry the arm, or disqualify the
arm. Well below it, the model learns the arm backwards and the prep is broken. Each variant is
its own record, so the same columns can reach opposite verdicts against
different arms. Never write a paper-specific leakage function.

**After the fit, scrutinise the top features.** Read each model's importance table from the
record (`importance`; the cached fit returns it without a refit) and look hard
at the top five of the two grf forests, which split on the residualised effect.
A feature can lead for a bad reason: a missingness pattern that marks units or
dates, a design artefact (an id, a date, a stratum or enumerator code), a
column imbalanced between arms, a post-treatment or outcome proxy, or a
near-identifier. Exclude one that is evidently bad, record why, and refit once;
that is a stated reason for the second fit. Keep one that is doubtful but not
evidently bad, and record it in `questions.json` (Report back). The baseline predictor's
importance ranks need, not effect.

**Another randomised layer** -- a second arm drawn independently of `w` --
belongs in `X`: conditioning on it lets the forest rediscover the paper's own
interaction. Not where that layer is the randomisation unit, and never where it
is post-treatment to `w`. The inventory usually sweeps it out as `design`;
restore it with `_FOREST_EXTRA`, and say either way.

**What the design stratified on may enter `X`.** A pretreatment characteristic
the strata were built from -- a baseline score, a size, a region -- is a fact
about the unit, in its continuous form or as recorded; restore it with
`_FOREST_EXTRA` where the inventory swept it out as `design`. Only the stratum
id itself stays out.

**No dummy expansion, in every prep.** An ordered categorical enters as its one
numeric column; a nominal one as a single integer code. Never the mega
inventory's one-vs-rest dummies — they split one variable across many sparse
columns and fragment importance. Where a raw categorical carries strictly more
than its derived dummy, keep the categorical.

**A compact variant is mandatory** when `p` / draws ≥ 0.15 (draws =
randomisation units). Below that, build one where pruning evidently
unimportant columns would perceivably improve the model. Register it
alongside the wide one on the same sample:

1. the paper's summary index in place of its items;
2. the paper's published moderators or controls;
3. one column per construct;
4. drop twins at |r| > 0.9, near-identifiers and partially-observed modules.

### 4. Choose `y`

**Start from the paper's headline outcome** for the arm, at its headline
follow-up, or the nearest wave observed equally by arm.

**An outcome a planner values.** A final outcome -- consumption, test scores,
health -- over an intermediate or compliance measure such as take-up or
attendance, unless take-up is itself the goal, as in a demand experiment.

**An outcome the arm moves.** Among outcomes valued equally -- several support
questions on one survey, two measures of the same health outcome -- take the one
where the paper's effect is clearest: an average effect near zero leaves the
forest little to rank. Report the ATE against its standard error. This never
trades a final outcome for an intermediate one that moves more.

Conditioning on *having* an outcome conditions on something the treatment may
move. Test every candidate before choosing:

```python
d.groupby(w)[candidate].apply(lambda s: s.notna().mean())   # want these equal
```

An outcome collected through the intervention itself — a platform survey, a
testing session, an attendance-gated module — is observed differentially by arm,
often by tens of points, and the gap shows up as effect. Administrative records
covering both arms are the fix where they exist. Report both rates for the
outcome you kept, and say which candidates you rejected on this. The same test
on a column of `X` is §3's "observed differently by arm" case.

Orientation: pick or construct `y` so that **uplift is a good thing**. Flipping
the sign of an adverse outcome in the loader is cleaner than asking every reader
of the Qini to invert it.

### 5. Choose `c`

`c` is a cost **level**. Often it is realised only where the unit was treated:
the cost column where it was, `0.0` where it was not, or a flat `c = w` where
every treated unit costs the same. Say whether the cost is gross or
incremental.

**Impute a missing cost where you can infer what it was.** Often you can: no
loan drawn is no capital, no visit is no fee -- the blank records an absence
and `0.0` is what that absence cost. Say which reading you applied. Where you
cannot tell -- the cost was simply not recorded -- leave it missing and let §6
hand the row over.

`c` is also the first stage of the grf instrumental forest (`grf_iv`), whose
leaves solve the Wald ratio of residualised outcome over residualised cost, so it decides what that second ranking is:

* **Flat `c = w`.** The first stage is 1 and the IV ranking is a second
  estimator of the same estimand. Report it as a robustness check, not as a
  second finding.
* **`c` a realised quantity.** The IV ranking is by effect per unit of cost.
  Report it as the separate question it is.

Say in the report which of the two your prep is.

### 5b. Check the first stage

Only where `c` is not flat, and before any fit:

```python
d.loc[w == 1, cost_var].describe()      # spread, and how close to zero
```

Report the mean cost per treated unit and the share of treated units at or
below zero. The Wald ratio divides by this, so costs near zero or of both
signs blow up the ranking on those leaves while the causal forest beside it
looks fine. Zero for a large minority means the IV ranking is not interpretable for
this prep — a finding, not a failure.

### 6. Missing data

Same pipeline every time:

1. Blank the source's missing codes (`-7`/`-8`/`-9` and the like), including
   where they survive as *levels* of a string categorical, which numeric blanking
   cannot see.
2. Drop rows only on non-finite `w`, `weight` and `propensity` — **never** on
   `X`, never on `y` or `c`, and never on anything post-treatment.
3. Leave `X`'s missing values missing.

**Do not drop for missing values in `y` or `c`.** Hand those rows over; what
becomes of them is decided downstream.

**An author's quality screen is attrition, not a filter.** Where the paper
excludes a respondent for how they answered -- an incoherent price-list, an
unfinished questionnaire, a failed attention check, a speeder -- keep the row
and set `y` missing on it.

**The rows you hand over are tested too.** `tests/test_forest_clusters.py`
builds the prep, not the fitted sample, so `rand_unit`, `strata` and `w` have to
be recorded for a unit that never came back. Take them off the assignment file
rather than the endline one: an id that is `NaN` for exactly the rows with no
outcome is a post-treatment id, and the test says so before a fit can hide it.

**Widening the frame must not narrow `X`.** The rows you restore usually come
from a file that carries fewer columns than the one you were using, so a
covariate the old frame had for everybody is now missing for exactly the
restored rows. Keep the column and let those entries be `NaN`

The cost is that `attrition_risk` will then separate the restored rows on the
missingness pattern alone and report an AUC near 1.0, which says nothing about
selection. That is a caption, not a reason to drop the column: say in the
report that the number reads the pattern rather than the design, and give the
observation rate by arm as the evidence instead.

### 7. Check the ATE against the paper

Read it off the analysis rather than computing your own: `utils.uplift.compute`
returns `resid_ate` and `resid_ate_se`, which already carry the prep's
`weight`, its `propensity` and its folds. A second estimator written beside
it would be testing your arithmetic, not the prep.

Report it beside the paper's own coefficient and say what separates them. They
will not agree exactly and do not need to. What matters is the sign, the rough
size, and that you can name the reason for the gap. A difference you cannot
explain is a prep to fix, not a number to publish. Set the paper's coefficient
as `FSpec.published_ate`, in `y`'s units as the prep builds it; the record
carries the gap as `ate_gap_published`.

---

## Register and wire it up

1. **Loader** in `data_scripts/PAPER_KEY.py`: module-level `_FOREST_ARM`,
   `_FOREST_RAND_UNIT`, `_FOREST_STRATUM` where the design is stratified, a cached
   `_forest_frame()`, `forest_covariates()`, and
   `cleaned_<name>_data_for_forest(...)` returning the `ForestData` above.
2. **Registry**: a `"forest"` sub-dict under `PAPER_KEY`, one key per variant,
   each `{"data": <callable>, "spec": FSpec(...)}` — `partial(loader, arm=...)`
   for the variant callables. `data` is a callable here, unlike `"mega"`;
   `forest_specs()` and `papers_with_forests()` read the sub-dict.
   The `FSpec` (`utils/forest.py`) is what says, in one sentence each, what the
   prep estimates, and all six of its fields are required:
   `y_name`/`y_description`, `w_name`/`w_description`, `c_name`/`c_description`.
   A `*_name` is the frame's column, or the short expression the loader builds
   the quantity with (`1 - under_18`, `ad_exploan_size x treatment`) — something
   greppable in your module, not a paraphrase. Each description is a **label,
   not a note**: dry, short, one line, in the register of a `.dta` variable
   label — "Takeup dummy: year 2011", "Gross Profit (USD)". Where the package
   carries a usable label, that label is what it says; the frozen inventory's
   `label` column is where to look first. No rationale, no direction-of-effect
   commentary, no reference to another variant. Sign flips, cluster counts,
   gross-vs-incremental and every other design fact go in the loader's
   docstring and in your report — the test rejects a description that reads
   as commentary.

   Two more carry the design, and the case page renders them: `row` (what
   a row is) and `confounding_variables` -- the glossary above says what each
   is. Blank renders as "not documented yet", which is honest; wrong is not.
   The kind of draw and what the folds hold out are inferred from `rand_unit` and
   `strata` and printed from the record; `exceptions` holds what §2 declares.

Those two are the whole of the wiring; everything downstream reads the
registry entry. A prep the registry does not name is dropped **in silence**,
and `tests/test_forest_registry.py` is the only thing that notices.

## Verify

**A forest fit is slow — minutes per case, growing with `n` and `p`.** Guard every
exploratory fit with a shell `timeout` while you are still testing the prep, and
do the cheap checks (shapes, leakage AUC, coverage by arm, the design's own
counts against the paper's)
before the first fit. Fit only what your registered variants require; a script
that fits several at once needs a reason worth stating. Cross-fitted prediction
is the standing exception, at no more than 5 folds.

```
.venv/bin/python -m pytest tests/ -q --ignore=tests/test_replication.py \
    --ignore=tests/test_mega_driver.py --ignore=tests/test_forest_clusters.py
.venv/bin/python -m pytest tests/test_forest_clusters.py -q -k PAPER_KEY
.venv/bin/python -m dashboard.build_plots -d PAPER_KEY
```

**Those two pytest lines are the whole test obligation**, and they are what CI
runs on your diff: the fast suite, and your paper's forest check. Never run the
bare `pytest tests/ -q`, nor a heavy file without `-k PAPER_KEY`: they
re-estimate every paper.

`build_plots -d PAPER_KEY` is the one full fit: it fits your paper's cases and
writes their records to `docs/data/PAPER_KEY_variant_model.json` -- **one file
per model**, from a single fit per prep, so a variant that wrote fewer records than
`dashboard/models.py` has entries is a fit that declined a model and you
should say which and why. **Name your own paper.** `-d all` fits every
registered case — tens of minutes of other papers' forests, none of it yours.
Don't also run `forest_script.py`: it repeats the same fit to draw PNGs nobody
commits.

Nothing runs after it: CI refits your paper and takes its records from there,
so a local fit is for your own numbers and your report. The wiring is guarded
by `tests/test_forest_registry.py` and `tests/test_registry_export.py`, both
above.

- [ ] `w` is randomly assigned — not a subgroup split, not a post-treatment state
- [ ] one row per unit; the wave or collapse is stated
- [ ] randomisation unit returned as `rand_unit` (the outer draw where it
      saturates) and the stratum as `strata` where the design is stratified --
      counts of strata and units reported, any different standard-error
      cluster distinguished, `resid_w_ate` ≈ 1
- [ ] every stratum treats its expected count within one unit, or the strata
      balance beyond redraws that ignore them (§2)
- [ ] only a cause in §2's table of allowed exceptions declared in
      `FSpec.exceptions`, with a reason and a limit; every other failure of
      `tests/test_forest_clusters.py` recorded in `questions.json`
- [ ] every column out of `X` recorded with its §3 reason; `arm_leakage_auc`
      read off the record and near 0.5
- [ ] outcome observation rate equal across arms, both rates reported, and
      the rows with no outcome still in what the prep returns
- [ ] the paper's randomisation sentence quoted, and what it names called a
      stratum or a confounder; a confounder returned as `propensity`, never as
      a weight, and rounding never returned as either; the data's counts
      checked against the paper's
- [ ] `c` is a cost level times treatment; gross vs incremental stated, and
      whether it is flat -- with what that makes the IV ranking (the same
      estimand again, or effect per unit of cost)
- [ ] first stage checked where `c` is not flat: mean cost per treated unit,
      and the share of treated units at or below zero
- [ ] no propensity or timing label left in `X`; every case in §3's
      consultation table recorded in `questions.json`
- [ ] `X` is no narrower than before the frame widened: a column the restored
      rows lack is kept and left `NaN`, not dropped
- [ ] `additional_adj` carries the design's confounders and the columns §3's
      table sends there, or is empty and says why -- never a stratum
- [ ] nothing in `additional_adj` identifies the randomisation unit: no
      draw-unit dummies, no columns constant within it, and no dummy block
      with `w` constant inside every level
- [ ] other randomised layers kept in `X`, not discarded -- including one the
      inventory swept out as `design`, restored with `_FOREST_EXTRA`
- [ ] `X`'s remaining missingness is real missingness, not an unblanked
      sentinel
- [ ] the ATE computed on `weight` and `propensity` together, reported beside
      the paper's own coefficient with the gap accounted for
- [ ] `FSpec` carries `row`, `randomization_unit`, `strata`,
      `confounding_variables`, `spillovers_prevalent` and, where the package
      lacks part of the draw, `full_draw_in_sample=False`
- [ ] every registered variant has an `FSpec` with every field filled -- no
      test checks this, a blank one stays blank -- and the three descriptions
      read as labels, not sentences
- [ ] every model wrote a record
- [ ] the grf forests' top features scrutinised: an evidently bad one excluded
      and refitted once, a doubtful one recorded in `questions.json`
- [ ] the scoped test suite is clean
- [ ] `results/forests/PAPER_KEY/REPORT.md` is written under Report back's
      headings, and `questions.json` holds only what the rules send to the
      owner or a genuinely hard case

## Conventions you must not violate

- One loader per paper; variants are keyword arguments registered with `partial`.
- Frames are cached; consumers never mutate a frame they are handed.
- `c` is post-treatment and never enters `X`. Neither does `propensity`, nor a
  treated share computed off `w`. Inventory-excluded columns never enter `X`.
- Anything the repo keeps must be generated by a script in the repo.
- `pictures/` and `docs/` are generated and git-ignored.
- The written report goes to `results/forests/PAPER_KEY/REPORT.md` — one per
  paper, and the only shared-tree file you write outside your own paper's rows.
- No hardcoded absolute paths; run from the repository root.
- Use `.venv/bin/python`, never bare `python3`.
- A paper PDF you download goes to `survey/data/pdfs/<PAPER_KEY>.pdf` in the
  main checkout if that file is missing or is an older version; name it in your
  report.

## Report back

**Write `results/forests/PAPER_KEY/REPORT.md`.** It is the only place the
reasoning survives; the registry keeps one `FSpec` and nothing else. One report
per paper, extended by later variants, as the interactions half's
`results/interactions/PAPER_KEY/REPORT.md` is. Use these headings, in this
order, each covering what its section of the checks asks you to report:

1. **Cases** -- which variants, and why: arms pooled or separate, the outcome
   and wave of each, the compact variant.
2. **Design** -- the paper's randomisation sentence, quoted with its section or
   page; the randomisation unit and its count and sizes; the strata and
   their sizes, or why there are none; the propensity and its confounders, or
   why there are none; the declared exceptions; spillovers; the authors' SE
   clustering where it differs.
3. **`X`** -- where it comes from, what was pruned and why, the leakage AUC,
   and the grf forests' top five with their importance and your verdict on each.
4. **`y`** -- the choice, its observation rate in each arm, and the ATE against
   its standard error.
5. **`c`** -- gross or incremental, flat or realised, and the first stage.
6. **Missing data** -- what was blanked, the rows with no outcome, and the
   attrition AUCs read as §6 says.
7. **ATE against the paper** -- `resid_ate` beside `published_ate`, and what
   separates them.
8. **Verdict** -- for each variant, the grf forests' lift at half budget against
   random (1) and against the better baseline ranking, and whether either
   forest beats both. The records carry every model's Qini numbers; don't copy
   them into a table.

Prose goes where a check failed or needed a judgement; a clean check is one
line. Report failures as failures: a prep that cannot be built honestly is a
finding about the paper, and the report is where it belongs.

**Questions go in `results/forests/PAPER_KEY/questions.json`,** beside the
report: a list with one object per question, each with exactly these fields --

```json
[{"case": "observed differently by arm",
  "variants": ["main", "compact"],
  "question": "Keep bl_income, the household's baseline income, in X?",
  "evidence": "**Rates by arm:** 94.1% of treated, 88.0% of controls\n**P-value:** 0.004\n**Source of the NaNs:** unknown\n**Package and paper on why:** silent; the baseline survey's dates are undocumented\n**Additional evidence:** some controls may have been surveyed after the draw, so a blank would mark a control",
  "options": ["Keep it in X", "Drop it from X", "Keep it, blanked for rows surveyed after the draw"],
  "proposal": "Keep it in X"}]
```

`case` is a label from §2's or §3's consultation table, or `"other"`;
`variants` names the registered variants it concerns; `evidence` gives one
line per item of the table's "what to report", the item in bold as the line's
title and its answer after it, and a last `**Additional evidence:**` line for
anything else that bears on the decision; `options` are two to four complete answers;
`proposal` is the option the prep takes until the owner answers.
`tests/test_forest_questions.py` checks the file. With nothing to ask, write
no file.

**Write each question for an owner reading it cold:**

* **Only what the decision needs.** `evidence` holds the facts that make the
  options differ and nothing else; each option says what it changes. The owner
  should be able to choose from the item alone, without opening the report.
* **One decision per item.** Split "A and B" unless one answer settles both.
* **Name each variable with what it is**: `bl_income`, the household's
  baseline income, not `bl_income` alone.
* **Give the mechanism as plain steps**: no test on control days, so a blank
  marks a control day, so the forest splits on the blank.
* **Quote numbers with their reference point** -- 94% of treated against 88%
  of controls, a leakage AUC of 0.62 where 0.5 means no signal -- and define a
  term of art at first use.
* **Show both counts** where the answer depends on what you count.
* **Say so when a proposal reverses an earlier owner decision**, citing it.

**Ask only what the rules send to the owner, or a genuinely hard case they do
not settle.** A question costs the owner's time and is not a sign of care: a
case the rules decide is decided, so decide it and say so in the report. Use
`"other"` only when no rule fits and the choice would change the result.

The spawn reply is short: the PR, the verdict with its lift numbers, and how
many questions `questions.json` holds. Don't repeat the report.
