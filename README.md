# Top-5 survey demo

50 articles from AER, QJE, JPE, ECMA and REStud, 2 per journal per year, 2021–2025, listed in `papers.json`.

`dvc pull -r r2ro` fetches `pdfs/`, `txt/` and the 6 replication packages in `datasets/`.

## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Condense.** Score each chunk of a paper and keep the best ~10K characters (Haiku).
3. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
4. **Download replication data.** 6 of the 50 so far.
5. **Replicate the published regressions.** 4 of the 50 so far.

## Run stage 3

Uses your Claude Code login; `ANTHROPIC_API_KEY` must be unset.

```bash
pip install -r requirements.txt
dvc pull -r r2ro txt.dvc
python classify.py          # writes verdicts/<wid>.json
```

## Run stage 5

```bash
dvc pull -r r2ro datasets/W4401126511.dvc
pytest test_replications.py            # one test per published column
```

`prompts/replicate.md` asks an agent to add a paper: `replications/<wid>.py` with its data loader and `SPECS`.
