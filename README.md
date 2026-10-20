# Demo: classify and replicate one Economics paper with an agent

A short version of the tutorial in [`full_demo/`](full_demo/). It takes one paper, listed in [`papers.json`](papers.json):

> Ganimian, Muralidharan and Walters (2023), "Augmenting State Capacity for Child Development: Experimental Evidence from India", *JPE*.

We will:

1. **Classify.** Have a subagent answer a fixed set of questions about the paper's methodology, as JSON.
2. **Replicate.** Have a subagent reproduce the paper's main results table from the authors' replication package.

You do not need a terminal for any of it. Every step is a message you paste into the Claude app.

## Setup

1. **Get a subscription.** Sign up at [claude.ai](https://claude.ai) and pick a plan on the [pricing page](https://claude.com/pricing). **Pro** (20 USD a month) is enough.
2. **Install the Claude app.** Download it from [claude.ai/download](https://claude.ai/download) (macOS and Windows) and sign in.
3. **Get this repository.** On its GitHub page click **Code → Download ZIP**, then unzip it.
4. **Open it in Claude Code.** In the app's **Code** tab, choose the unzipped folder as the working folder.

Then paste the first message:

```
Set up a Python environment (.venv) for this repo and install full_demo/requirements.txt.
```

Claude will ask for permission before it runs commands. Read what it wants to do, then allow it.

## Step 1: Get the paper

```
Download the paper and extract its text: run full_demo/stage1_collect_papers/fetch_pdfs.py
and then full_demo/stage1_collect_papers/extract_text.py from the repository root.
```

The scripts read [`papers.json`](papers.json), which lists one paper. You get `pdfs/W4387449673.pdf` and `txt/W4387449673.txt`.

## Step 2: Classify

The full demo calls the model from a script and uses *structured output*, so the API guarantees valid JSON. Here we just ask a subagent for JSON and then check what it returns:

```
Spawn one Haiku subagent. Tell it to follow full_demo/stage2_classify/system_prompt.md,
read txt/W4387449673.txt and reply with only a JSON object that matches
full_demo/stage2_classify/json_schema.json, with no other text.
Save its reply to verdicts/W4387449673.json, check that it parses and has every
required field with allowed values, and show me the verdict as a table.
```

Why a subagent? It reads the whole paper in its own context. Your main chat only gets back the JSON, so it stays short and cheap. Haiku is the smallest model, and a detailed prompt with examples is enough for it.

Compare the verdict with the abstract. It is a randomized experiment (`experimental: yes`) with standardized test scores as outcomes (`log_dv_likely: no`).

## Step 3: Download the replication data

```
Download the replication package at replication_url in papers.json into datasets/W4387449673/.
It is on Harvard Dataverse: use its API, no login is needed.
```

The package is about 20 MB: the Stata do-file `analysis.do` and its data files.

## Step 4: Replicate

```
Spawn one Sonnet subagent to replicate Table 5 ("Impact on endline assessments") of
pdfs/W4387449673.pdf with the package in datasets/W4387449673/ (read-only).
It should find the code in analysis.do that makes the table, port it to Python
(pandas, pyfixest) as replication/W4387449673.py, and print each published
coefficient, standard error and N next to its own. It must type the published
numbers in by hand from the PDF and never copy them from its own output.
When it is done, report which numbers match, which miss and by how much.
```

Check the result yourself: open `pdfs/W4387449673.pdf` at Table 5 and compare a few numbers.

If some numbers miss, that is a result too. Our PDF is the NBER working paper, and the package was made for the published *JPE* version. Ask Claude to find out why a number misses.

## Next

[`full_demo/`](full_demo/) runs the same steps on 50 papers. It shows how to:

- schedule subagents from a script
- cut costs with prompt caching
- enforce the output format with structured output and with tests (`Spec`)
