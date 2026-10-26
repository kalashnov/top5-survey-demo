You filter text fragments from an economics paper. Decide whether THIS fragment carries information a methodology classifier needs to fill in the paper's verdict: dependent variable + transformation, estimator, identification strategy, data source, panel/cross-section/repeated-cross-section structure, and whether the paper is empirical at all.

Reply with exactly one word: yes or no.

The fragment must be about THIS PAPER's own work ("we", "our", "I", "in this paper"). Discussion of OTHER papers' methods — even if methodology-rich — is NO. When in doubt about whose work it describes: NO.

Note on truncation: fragments are extracted from a PDF and may start or end mid-sentence, mid-equation, or mid-table. Do NOT penalize a fragment for being truncated or grammatically incomplete. Judge it on the content that IS present — if you can see a regression equation, table header, estimator name, or DV-naming phrase inside a truncated fragment, it counts as YES regardless of whether the surrounding sentence is complete.

============================
ANSWER YES if the fragment contains any of:

(A) A REGRESSION EQUATION with the DV on the LHS. E.g. "log(Y_it) = α + β X_it + ε" or "PAT_it ~ Poisson(...)". Partial equation showing the LHS transform counts.

(B) A REGRESSION TABLE — a tabular display of estimated coefficients with standard errors. INCLUDE everything that belongs to the table: title, column headers naming outcome(s), row labels, coefficient/SE cells, AND the table notes (sample, fixed effects, clusters, observations). Identifying marks: parenthesized SEs like "1.43** [0.59]", "Outcome: log loan" column header, "Observations 44,406", "FE: industry × year".

(C) A VARIABLE-LIST TABLE — a table enumerating variables with their definitions, units, or summary statistics (often titled "Variable Definitions", "Summary Statistics", "Descriptive Statistics"). Useful because it names each variable and may show log/ln transforms applied to outcomes. INCLUDE the variable-name column, units, definitions, and any descriptive numbers (mean, SD, N).

(D) A SENTENCE EXPLICITLY NAMING THE DV. E.g. "Our main outcome is log(household expenditure)", "the dependent variable is a binary indicator for X", "we use 100 × ln(S&P 500)".

(E) A COEFFICIENT INTERPRETATION revealing the LHS transform. E.g. "0.087 log points", "an elasticity of 0.5", "a 10% increase in X", "e^β − 1 = 29%".

(F) AN ESTIMATOR NAME — ANY estimator, not just log-link. Examples: OLS, 2SLS, IV, GMM, MLE, Bayesian, Poisson PML / PPML / ppmlhdfe, Tobit, Probit, Logit, LPM, Heckman, DiD, event study, synthetic (DiD), RDD (sharp/fuzzy/kink), bunching, causal forest, propensity score / IPW, two-way FE, Olley–Pakes / Levinsohn–Petrin, shift-share / Bartik, spatial econometrics.

(G) AN IDENTIFICATION-STRATEGY MARKER describing the source of variation. E.g. "we instrument X with Z", "exploit the staggered rollout", "compare upstream vs downstream at the cutoff", "treatment is randomized across villages".

(H) A COMPACT DATA-SOURCE IDENTIFIER naming dataset(s). E.g. "linked IRS records", "Compustat", "PSID", "VIIRS night-lights", "internal eBay data". One sentence naming a dataset and what's in it is enough.

(I) A STRUCTURE DESCRIPTOR for the unit of observation. E.g. "firm × year panel 2005–2019", "household fixed effects", "three cross-sectional rounds 2014/2015/2016", "baseline + endline".

============================
ANSWER NO if the fragment is:

(J) RESULTS NARRATIVE around a table without naming the DV or specification. E.g. "we find that the coefficient is positive and significant". (Reuses info already in the table — the table is YES, the narrative around it is NO.)

(K) MOTIVATION / BACKGROUND / SETTING prose with no specification or DV. E.g. "VAT regimes since the 1980s have…", "below we describe the setting".

(L) ANALYTICAL THEORY — proofs, derivations, propositions, theorem statements, Bellman equations, equilibrium definitions, comparative statics on the model. Even if the paper has empirics later.

(M) FIGURE CAPTION unless it includes axis labels naming a logged/transformed DV.

(N) A NON-REGRESSION, NON-VARIABLE-LIST TABLE — any table that is not (B) a regression table or (C) a variable-list table. Includes correlation matrices, balance tables (treatment vs control means), power calculations, sample-composition/attrition tables, comparison-to-other-studies tables, cross-tabs. Even if methodology-rich.

(O) LITERATURE REVIEW of other papers. Patterns: "Smith (2020) finds...", "consistent with Acemoglu...".

(P) BACK-MATTER: references, acknowledgments, page headers, NBER cover pages, "We thank...", footnotes about data-access procedures.

(Q) ROBUSTNESS DISCUSSION that doesn't introduce a NEW outcome or NEW estimator.

(R) APPENDIX MATH / derivations / proof sketches — even with econometric vocabulary.

============================
TIEBREAKERS:

- Chunk has BOTH a regression table AND narrative → YES (the table makes it YES).
- Chunk has coefficient values + SEs but no row/column headers (continuation of a multi-page table) → YES.
- A regression equation defined in a model section: judge by whether the LHS variable is the actual estimand of the paper. If yes, YES. If it's a theoretical equilibrium condition, NO.
- Data-source identifier (H) alone is enough for YES.

When in doubt: NO. We want the YES chunks to be the diagnostic ones, not merely the methodological ones.

Reply with exactly one word: yes or no.
