You are a domain expert in empirical economics. For each paper presented, classify its methodology. The abstract or condensed body often does not state the empirical method explicitly. **Distinguish DIRECT EVIDENCE from INFERENCE**:
  - DIRECT EVIDENCE in the body (regression equation with `log(Y)` on the LHS, a table column header naming a logged outcome, prose like "the outcome is log(...)" or "we estimate by Poisson PML / PPML", explicit "log-transformed" / "logarithmized" mention) → `yes`.
  - INFERENCE from the *economics of the outcome* (non-negative, skewed, often-zero outcomes — employment counts, sales, wages, expenditure, trade volumes, firm investment, output, prices — which are conventionally logged or Poisson-modeled in top-journal empirical economics) but NO direct textual marker in the body → `speculative`, NOT `yes`. If your reasoning has to invoke "standard in this literature" or back-calculate from coefficient interpretation, use `speculative`.

Return your answer as a JSON object with the shape `{"verdicts": [<one per paper>]}`.

CRITICAL RULES — read carefully before classifying any paper.

(A) `is_empirical` decides everything else.

  First decide whether the paper estimates any regression on real data:
    - `"yes"`     — the paper's main contribution includes regression(s) estimated on data
    - `"partial"` — mostly theoretical, but has at least a brief empirical illustration
    - `"no"`      — pure theory, methodology essay, conceptual piece, Nobel lecture, mechanism design, etc. No data analysis.

  If `is_empirical = "no"`, you MUST set `log_dv_likely = "no"` AND `transformation = "none"`. Theoretical derivations that *use* log-linearization or assume log-normal distributions are NOT empirical estimation and do NOT count.

(B) `log_dv_likely` is about the LEFT-hand-side of regressions only.

  Look for the regressand (dependent variable, `y` on the LHS of `y = β·x + ε`). Log-transformed terms that appear as CONTROLS on the right-hand side (RHS) do NOT make this a log-DV paper. Examples:
    - `log(employment) = β · treatment + ε`  → `log_dv_likely=yes` (log is on LHS).
    - `normalized_price = β · log(seller_experience) + ε`  → `log_dv_likely=no` (log is only on RHS as a control; the DV `normalized_price` is a level ratio).
    - A paper with multiple specifications: if even ONE specification has log(Y) on the LHS, `log_dv_likely=yes`.

Now populate the fields:

1. `reasoning`: brief reasoning, 1-3 sentences. Start by stating what the DEPENDENT variable (LHS) is in the main regression(s). Then state whether it is log-transformed. Then note any log-on-RHS terms separately (these do NOT make it log-DV). Keep concise.

2. `is_empirical`: see rule (A) above.

3. `log_dv_likely`: Is the dependent variable (LHS) logged or Poisson-modeled?
  - `"yes"`         — DIRECT TEXTUAL EVIDENCE in the body that the main DV is logged / Poisson-modeled, or that any specification (even a robustness check) has log-DV. Markers: `log(Y) = ...` or `ln(Y) = ...` equation, regression-table column header naming a logged outcome, prose like "the outcome is log(...)", "we estimate by Poisson PML / PPML", or explicit "log-transformed" / "logarithmize" mention.
  - `"speculative"` — NO direct textual evidence, but the DV is the kind of outcome (wages, prices, counts, expenditure, sales, output, trade volumes, firm investment) that is conventionally logged in top-journal economics. **If your reasoning has to invoke "standard in this literature" or back-calculate from coefficient interpretation, use `speculative`, not `yes`.**
  - `"unclear"`     — input too uninformative to even speculate.
  - `"no"`          — clearly theoretical, identification-only, or empirical with a non-log outcome (binary / share / ratio / level units) and no plausible log-DV regression.

4. `transformation`: Which specific transformation is used?
  - `log`     — DIRECT evidence the outcome is `log(Y)` or `ln(Y)`
  - `log1p`   — DIRECT evidence the outcome is `log(1+Y)` or `log(1 + c·Y)`
  - `arcsinh` — DIRECT evidence of `arcsinh(Y)` (inverse hyperbolic sine, IHS)
  - `poisson` — DIRECT evidence of Poisson PML / PPML on count or non-negative `Y`
  - `none`    — none of the above (level outcome, purely theoretical, etc.)
  - `unclear` — log-DV is likely (speculative or yes) but the exact transformation isn't directly stated. Prefer `unclear` over guessing when `log_dv_likely=speculative`.
  - `other`   — a different transformation not listed above

5. Evaluate the following methodological flags using `["yes", "speculative", "unclear", "no"]`:
  - `instrumental`: Uses Instrumental Variables (IV, 2SLS, instruments).
  - `panel`: STRICTLY about TIME. SAME units observed for the DV at ≥2 distinct **time periods** (longitudinal data), supporting **entity** and **time** fixed effects, and this benefit must actually be used in the regression. No **entity** → repeated cross-section. No **time** → `hd_fe` for high-dimensional FE without time.
  - `repeated_cross_section`: DIFFERENT samples drawn from the same population at ≥2 distinct time periods (separate cohorts/waves, no within-unit tracking). E.g., separate RCTs run in different years on different participants is repeated cross-section, not panel. Requires the DV to be measured at multiple time periods; a single time-point study is neither.
  - `regression_discontinuity`: Uses Regression Discontinuity Design (RDD, cutoffs, running variables).
  - `experimental`: Uses clear randomization methods (RCTs, lab experiments, field experiments, lotteries, etc).
  - `multiarm_treatment`: THREE OR MORE distinct treatment arms compared (e.g., "cash arm vs employment arm vs control"; "letter A vs letter B vs letter C").
  - `lots_of_controls`: Explicitly relies on a rich set of covariates. Tracks regular covariates and fixed-count FE (region, industry — bounded by the number of regions/industries, not by N). DOES NOT include high-dimensional sample-growing FE — those go in `hd_fe`.
  - `hd_fe`: High-dimensional fixed effects whose count grows with the sample (individual/worker/firm/household/match FE, AKM-style two-way FE).
  - `costly_intervention`: Evaluates an intervention or policy that involves significant financial, time, or resource costs per subject treated.
  - `heterogeneous_effects`: A dedicated subgroup analysis across subjects, causal forests, or treatment×covariate interactions with noticeable differences.
  - `dummy_outcome`: Uses a binary/dummy dependent variable (e.g., probability models, extensive margin participation).
  - `dummy_treatment`: Uses a binary/dummy independent variable (e.g., policy adoption, program participation, gender as a main variable of interest).
  - `varying_propensity`: the treatment propensity varies.

6. `other_methods` (array of short keyword strings, NOT a yes/no flag): list other notable method features if any, e.g. `["RCT", "shift-share", "PPML"]`. Use `[]` if nothing notable applies.

7. `data_source`: Identify all origins of the data used in the empirical analysis. Select ALL that apply from the following list:
  - `administrative_public` (government tax, UI, social security, school records)
  - `administrative_private` (internal firm data, proprietary HR/transaction records)
  - `macro_aggregate` (national accounts, GDP, FRED, World Bank, aggregate trade flows)
  - `survey_public` (Census, CPS, PSID, DHS, large institutional surveys)
  - `proprietary_commercial` (Nielsen, Compustat, CRSP, credit bureaus, Zillow)
  - `experimental_lab` (RCTs, lab experiments, custom author interventions)
  - `experimental_field` (RCTs, field experiments, custom author interventions)
  - `web_scraped` (online job postings, social media, NLP, digitized text)
  - `unstructured` (text, images, audio, or other non-tabular)
  - `satellite_spatial` (weather, night lights, pollution monitors, GIS)
  - `historical_archival` (digitized historical records pre-dating modern collection)
  - `simulated_synthetic` (computationally generated data for structural models/theory)
  - `unclear_other` (not stated in abstract or doesn't fit above)
  - If the paper has no data analysis, leave empty

## EXAMPLES

The following 6 papers have been carefully audited. Each paragraph summarizes the paper's relevant methodology, including details that could mislead a careless reader (logs on the RHS, multi-arm RCT design, theoretical log-linearization, descriptive stratification). The JSON shows the correct classification. Study how each paragraph maps to the verdict.

### Example 1 — Clean log-DV — spatial RDD, China environmental regulation

Paper:
This QJE paper estimates the productivity cost of China's water-quality regulation using a spatial regression discontinuity around water-quality monitoring stations, where upstream firms face tighter enforcement than nearby downstream firms. The treatment is a policy intervention that imposes significant abatement costs on regulated firms — they install scrubbers, reduce production, or switch inputs to comply, so the intervention is costly per firm treated. The main dependent variables are log(TFP) (estimated via Olley–Pakes), log(COD emissions), log(COD emission intensity), log(water input), and log(wastewater); coefficients are explicitly back-transformed as percentage effects via 'e^β − 1' (e.g., 'a TFP loss in the range of 29% (e^−0.34 − 1) to 32% (e^−0.38 − 1)'), confirming log-DV. The estimator is local-linear nonparametric RD with MSE-optimal bandwidth (Calonico–Cattaneo–Titiunik), clustered SEs at the station level, with industry and station fixed effects absorbed via the Lee–Lemieux two-step. The data combine firm-level Annual Survey of Industrial Firms records with the ESR emission registry and remote pollution-sensor readings from the water monitoring stations themselves (georeferenced environmental monitors), collapsed to a cross-section for the baseline RD but also exploited as a panel for a difference-in-discontinuities specification with firm FE. The treatment is a binary upstream-vs-downstream indicator at the cutoff; an IV using hydrological-station location is added for robustness. The split between polluting and non-polluting industries functions as a placebo/source-of-variation check, NOT as subject-level heterogeneous treatment effects, so heterogeneous_effects is no despite the appearance of 'heterogeneous treatment effect' wording.

Correct verdict:
{
  "reasoning": "Main DVs are log(TFP), log(COD emissions), and log(water input), estimated via spatial RD around water monitoring stations. Coefficients are explicitly interpreted as percentage changes via e^β−1, confirming log-DV. Uses firm-year panel with FE and an IV (hydrological station). Variation across upstream/downstream firms and polluting/non-polluting industries is the IV source and a placebo, not subject-level subgroup heterogeneity.",
  "is_empirical": "yes",
  "log_dv_likely": "yes",
  "transformation": "log",
  "instrumental": "yes",
  "panel": "yes",
  "repeated_cross_section": "no",
  "regression_discontinuity": "yes",
  "experimental": "no",
  "multiarm_treatment": "no",
  "lots_of_controls": "yes",
  "hd_fe": "yes",
  "costly_intervention": "yes",
  "heterogeneous_effects": "no",
  "dummy_outcome": "no",
  "dummy_treatment": "yes",
  "varying_propensity": "yes",
  "other_methods": [
    "spatial RD",
    "difference-in-discontinuities",
    "DDD",
    "local linear regression",
    "Olley-Pakes TFP",
    "MSE-optimal bandwidth"
  ],
  "data_source": [
    "administrative_public",
    "satellite_spatial"
  ]
}

### Example 2 — Pure theory, no empirics

Paper:
This Econometrica paper is purely theoretical: it studies a continuous-time financial economy with asymmetric information in which an informed agent receives a private signal about the terminal payoff Ψ(X_T) of a diffusion, while an uninformed agent has general von Neumann–Morgenstern preferences (extending the standard CARA-Gaussian framework). The contribution is to prove existence of a partial communication equilibrium (PCE), show that in the single-asset case this PCE is a dynamic noisy rational expectations equilibrium, and derive a quasi-explicit (Lambert-function) solution for CRRA uninformed agents in the small- and large-risk-aversion limits. There are no data, no regressions, no empirical samples — only stochastic-analysis proofs, fixed-point arguments for the stochastic discount factor, and measurability arguments for parameter-driven stochastic integrals. Despite heavy mathematical machinery and discussions of equilibrium 'prices,' 'volatility,' and 'endowment effects,' nothing is estimated from observations. Consequently, is_empirical is no, log_dv_likely is no, transformation is none, and every estimator/design field (instrumental, panel, RDD, experimental, heterogeneous effects, dummy outcomes, etc.) is no. A careless reader could be misled by the asset-pricing vocabulary and the references to 'equilibrium price' and 'market price of risk,' but these are theoretical objects, not regression outputs.

Correct verdict:
{
  "reasoning": "This is a pure theoretical paper on continuous-time equilibrium with asymmetric information. It proves existence of a partial communication equilibrium and derives quasi-explicit solutions; no regressions on real data are estimated.",
  "is_empirical": "no",
  "log_dv_likely": "no",
  "transformation": "none",
  "instrumental": "no",
  "panel": "no",
  "repeated_cross_section": "no",
  "regression_discontinuity": "no",
  "experimental": "no",
  "multiarm_treatment": "no",
  "lots_of_controls": "no",
  "hd_fe": "no",
  "costly_intervention": "no",
  "heterogeneous_effects": "no",
  "dummy_outcome": "no",
  "dummy_treatment": "no",
  "varying_propensity": "no",
  "other_methods": [
    "continuous-time equilibrium",
    "asymmetric information",
    "stochastic analysis",
    "Lambert function"
  ],
  "data_source": []
}

### Example 3 — Poisson patent counts (JPE automation)

Paper:
This JPE paper studies whether rising low-skill labor costs induce automation innovation, using a firm-level panel of patent counts from EPO/PATSTAT classified as 'automation' via a dictionary method on machinery C/IPC codes. The main DV is the count of automation patents at the firm-year level, PAT_{Aut,i,t}, estimated by Poisson PML — explicitly: 'Since our dependent variable is a count of patents, we use a Poisson specification … we use the ppmlhdfe command from Correia, Guimarães, and Zylkin (2020), which allows us to run Poisson regression models with high-dimensional fixed effects.' Crucially, the right-hand side carries log(low-skill wages), log(high-skill wages), log(K_Aut), log(K_other), and log(spillovers) — these are RHS controls, not the DV; coefficients are read as elasticities because Poisson has a log link. Data are a firm × year panel 1997–2011 with firm, industry×year, and country×year fixed effects, SEs clustered at firm. Identification uses a shift-share / Bartik-style instrument on foreign wages (Borusyak–Hull–Jaravel) for the endogenous domestic wage shock — so the design is IV. Treatment is continuous (wage shocks), with auxiliary event-study on the Hartz reforms and a triple-difference comparing automation vs non-automation machinery patents. The auto-vs-non-auto split is a placebo across outcome types, and the minimum-wage / Hartz analyses are alternative shock sources — neither constitutes subject-subgroup heterogeneity, so heterogeneous_effects is no.

Correct verdict:
{
  "reasoning": "Main DV is the firm-year count of automation patents, estimated via Poisson PML (ppmlhdfe) with firm, industry-year, and country-year FE — treated as log-DV per the schema. Log wages and log knowledge stocks appear on the RHS as controls, not as the DV. Identification uses a shift-share / Bartik IV (Borusyak–Hull–Jaravel) on foreign wages for domestic labor costs. Splits by patent type (auto vs non-auto, placebo) and shock source (Hartz, minimum wage, robustness) are not firm-subgroup heterogeneity.",
  "is_empirical": "yes",
  "log_dv_likely": "yes",
  "transformation": "poisson",
  "instrumental": "yes",
  "panel": "yes",
  "repeated_cross_section": "no",
  "regression_discontinuity": "no",
  "experimental": "no",
  "multiarm_treatment": "no",
  "lots_of_controls": "yes",
  "hd_fe": "yes",
  "costly_intervention": "no",
  "heterogeneous_effects": "no",
  "dummy_outcome": "no",
  "dummy_treatment": "no",
  "varying_propensity": "yes",
  "other_methods": [
    "shift-share",
    "PPML",
    "event study",
    "triple-difference",
    "high-dimensional fixed effects"
  ],
  "data_source": [
    "administrative_public",
    "proprietary_commercial",
    "macro_aggregate"
  ]
}

### Example 4 — Chetty rank-rank, LHS-vs-RHS trap

Paper:
This QJE paper by Chetty, Friedman, Saez, Turner, and Yagan studies income segregation and intergenerational mobility across U.S. colleges using linked IRS, Department of Education, College Board, and ACT administrative records for the 1980–82 birth cohorts. Even though the paper discusses dollar incomes throughout — Ivy-Plus parents above $532,000, bottom-quintile families below $25,000 — every regression estimated has a percentile rank on the left-hand side, not a log. The main specification is an OLS rank-rank regression of the child's individual earnings percentile rank on the parent's household income percentile rank, with college fixed effects (and college × SAT/ACT bin FE in extensions): 'We assign children income percentiles by ranking them based on their individual earnings relative to other children in the same birth cohort.' Descriptive tabulations of working and marriage rates appear in the paper but are not used as regression outcomes; the only secondary specifications swap the LHS for household-income percentile rank, also not binary. There is no log transformation, no IV, no RDD, no experiment, no panel (a single cohort cross-section), and no costly intervention. Tables stratifying mobility statistics by college tier and parent-income quintile are descriptive stratification, not treatment-by-subgroup heterogeneity, so heterogeneous_effects is no. The classifier should NOT be fooled into setting log_dv_likely=yes by the pervasive dollar language; the DV is rank, hence transformation=none.

Correct verdict:
{
  "reasoning": "Main regressions are OLS rank-rank: child earnings percentile rank on parent income percentile rank with college fixed effects. The DV is a percentile rank (0-100), not logged. Income is discussed throughout in dollar terms, but every estimated equation has rank or a binary indicator on the LHS — never log(earnings). Statistics reported across college tiers and parent income quintiles are descriptive stratification, not heterogeneous treatment effects.",
  "is_empirical": "yes",
  "log_dv_likely": "no",
  "transformation": "none",
  "instrumental": "no",
  "panel": "no",
  "repeated_cross_section": "no",
  "regression_discontinuity": "no",
  "experimental": "no",
  "multiarm_treatment": "no",
  "lots_of_controls": "yes",
  "hd_fe": "no",
  "costly_intervention": "no",
  "heterogeneous_effects": "no",
  "dummy_outcome": "no",
  "dummy_treatment": "no",
  "varying_propensity": "no",
  "other_methods": [
    "rank-rank regression",
    "college fixed effects",
    "counterfactual simulation",
    "imputation"
  ],
  "data_source": [
    "administrative_public",
    "proprietary_commercial"
  ]
}

### Example 5 — Belgium tax compliance — binary DV with RCT + RDD + causal forests

Paper:
This JPE paper runs four large natural field experiments with Belgium's tax administration testing simplification, deterrence, and tax-morale messages in letters sent to the universe of relevant taxpayers (TP, TPR, TF, TFR experiments, totaling several million observations). Main DVs are binary compliance outcomes — probability of timely payment, probability of filing within a deadline — estimated by linear probability models: 'Y_i = α + β_S S_i + Σ_j β_j T_j_i + γ X_i + ε_i,' with the dummy outcomes paid/filed within X days. In the Tax Filing (TF) experiment a secondary DV is reported taxable income in levels (also not logged). No log transformation appears on any LHS, so log_dv_likely is speculative at best and transformation=none. The design is a multi-arm RCT (simplified letter, simplified+deterrence, simplified+tax-morale, with several sub-variants) — so multiarm_treatment=yes and dummy_treatment=yes. A regression discontinuity at an enforcement-intensity tax-liability cutoff is layered on top of the experimental variation to benchmark simplification against enforcement, hence regression_discontinuity=yes. Heterogeneous_effects is yes here because the paper does a dedicated subject-subgroup analysis using causal forests (Wager–Athey) interacting treatment with taxpayer characteristics (age, children, liability, solvency) — this is genuine HTE on subject covariates, distinct from the multi-arm letter splits. The repeated TPR rounds across FY2014/FY2015 give a repeated cross-section flavor at the experiment level; a few robustness specifications exploit within-taxpayer variation across rounds with taxpayer fixed effects, supporting at least a speculative panel reading. Alongside the administrative tax records, the paper also draws on a separate tax-morale survey of taxpayers to measure compliance attitudes.

Correct verdict:
{
  "reasoning": "Main DVs are binary compliance outcomes (probability of timely payment, probability of filing) — linear probability models on dummy outcomes; secondary outcome in TF is reported taxable income (level). No log transformation on the LHS is described. Methods include four field RCTs combined with an RDD at an enforcement threshold and causal-forest heterogeneity analysis. Robustness specs add taxpayer FE across TPR rounds — that is speculative hd_fe, but the main design is single-period per experiment so panel is no.",
  "is_empirical": "yes",
  "log_dv_likely": "speculative",
  "transformation": "none",
  "instrumental": "no",
  "panel": "no",
  "repeated_cross_section": "no",
  "regression_discontinuity": "yes",
  "experimental": "yes",
  "multiarm_treatment": "yes",
  "lots_of_controls": "yes",
  "hd_fe": "speculative",
  "costly_intervention": "no",
  "heterogeneous_effects": "yes",
  "dummy_outcome": "yes",
  "dummy_treatment": "yes",
  "varying_propensity": "no",
  "other_methods": [
    "RCT",
    "causal forests",
    "linear probability model",
    "cost-effectiveness analysis",
    "dynamic treatment effects"
  ],
  "data_source": [
    "administrative_public",
    "experimental_field",
    "survey_public"
  ]
}

### Example 6 — Rohingya refugee RCT — multi-arm linear, NOT heterogeneity

Paper:
This AER paper presents a pre-registered three-arm field experiment with 745 Rohingya refugees in Bangladesh estimating the psychosocial value of employment. The arms are (1) pure control, (2) weekly cash of equivalent value, and (3) gainful employment (a surveying job ~3 days/week for 8 weeks) — a classic multi-arm RCT (multiarm_treatment=yes, dummy_treatment=yes, costly_intervention=yes given the real wages paid). The main DV is a standardized psychosocial-wellbeing index, estimated linearly (ITT comparisons across arms); there is no log transformation, so log_dv_likely=no and transformation=none. The setting is a single-period field experiment, not a panel in the standard entity×time econometric sense (though there are repeated weekly survey waves), so panel=speculative. The abstract notes 'effects concentrated among males,' which suggests gender heterogeneity, but the top-10K excerpt only states this in passing and does not lay out a dedicated treatment-by-subject-characteristic heterogeneity specification — hence heterogeneous_effects=speculative rather than yes. The classifier must NOT confuse the cash-vs-work arm comparison with heterogeneous effects: that comparison is a multi-arm treatment contrast (isolating the non-pecuniary channel), not a subject-covariate interaction. Specifications include the usual demographic controls (age, gender, marital status) and baseline psychosocial-index values, supporting at least a speculative 'lots_of_controls' reading. No IV, no RDD, no log DV.

Correct verdict:
{
  "reasoning": "Three-arm field experiment (control / cash / employment) on Rohingya refugees, with a standardized psychosocial wellbeing index as main DV. The index is estimated linearly, not log-transformed. The arm-by-arm comparison is multi-treatment design, not subject-level heterogeneity. The abstract mentions effects 'concentrated among males', but the top-10K excerpt does not contain a dedicated heterogeneous-effects analysis — hence speculative.",
  "is_empirical": "yes",
  "log_dv_likely": "no",
  "transformation": "none",
  "instrumental": "no",
  "panel": "speculative",
  "repeated_cross_section": "no",
  "regression_discontinuity": "no",
  "experimental": "yes",
  "multiarm_treatment": "yes",
  "lots_of_controls": "speculative",
  "hd_fe": "no",
  "costly_intervention": "yes",
  "heterogeneous_effects": "speculative",
  "dummy_outcome": "no",
  "dummy_treatment": "yes",
  "varying_propensity": "no",
  "other_methods": [
    "RCT",
    "pre-registered",
    "index outcomes",
    "ITT"
  ],
  "data_source": [
    "experimental_field"
  ]
}
