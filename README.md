# Top-5 survey demo

100 articles from AER, QJE, JPE, ECMA and REStud, 4 per journal per year, 2021–2025, listed in `papers.json`.

`dvc pull -r r2ro` fetches `pdfs/`, `txt/` and the 12 replication packages in `datasets/`.

## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Condense.** Score each chunk of a paper and keep the best ~10K characters (Haiku).
3. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
4. **Download replication data.** 12 of the 100 so far.
5. **Replicate the published regressions.** 7 of the 100 so far.
