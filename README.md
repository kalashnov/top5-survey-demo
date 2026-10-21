# Demo: classify and replicate Economics papers with an agent

A short version of the tutorial in [`full_demo/`](full_demo/). It takes five papers, listed in [`papers.json`](papers.json):

| Paper | Journal |
|---|---|
| Koessler & Skreta, "Informed Information Design" | JPE 2023 |
| Greenstone, Pande, Ryan & Sudarshan, "Can Pollution Markets Work in Developing Countries?" | QJE 2025 |
| Do & Jacoby, "Optimal Pricing of a New Utility Service: The Case of Piped Water in Vietnam" | REStud 2024 |
| Ganimian, Muralidharan & Walters, "Augmenting State Capacity for Child Development" | JPE 2023 |
| Cederlöf, Fredriksson, Nekoei & Seim, "Mandatory Notice of Layoff, Job Search, and Efficiency" | QJE 2024 |

We will:

1. **Classify.** Have subagents answer a fixed set of questions about each paper's methodology, as JSON. Papers with no empirical work drop out here.
2. **Replicate.** Have subagents reproduce one table of each remaining paper from the authors' replication package.

You do not need a terminal for any of it. Every step is a message you paste into the Claude app.

## Setup

1. **Get a subscription.** Sign up at [claude.ai](https://claude.ai) and pick a plan on the [pricing page](https://claude.com/pricing). **Pro** (20 USD a month) is enough.
2. **Install the Claude app.** Download it from [claude.ai/download](https://claude.ai/download) (macOS and Windows) and sign in.
3. **Open a folder in Claude Code.** Make a new, empty folder, e.g. `survey-demo` in your Documents. In the app's **Code** tab, choose it as the working folder.

Then paste the first message:

```
Set up the repository https://github.com/kalashnov/top5-survey-demo in this folder:
1. Clone it here, into the current folder itself, not a subfolder. If git is not
   installed, download the ZIP from GitHub and unpack it here instead.
2. Make sure Python 3.11 or newer is available. If it is not, tell me how to install
   it on my system and stop.
3. Create a virtual environment .venv in this folder and install full_demo/requirements.txt into it.
4. Check that it works: import pymupdf, pandas and pyfixest with the .venv Python.
From now on, run all Python in this folder with the .venv Python.
Tell me what you did and whether anything failed.
```

Claude will ask for permission before it runs commands. Read what it wants to do, then allow it.

## Step 1: Get the papers

```
Download the papers and extract their text: run full_demo/stage1_collect_papers/fetch_pdfs.py
and then full_demo/stage1_collect_papers/extract_text.py from the repository root.
```

The scripts read [`papers.json`](papers.json). You get one PDF in `pdfs/` and one text file in `txt/` per paper.

## Step 2: Classify

The questions are in [`classify.md`](classify.md): is the paper empirical, is it an experiment, does it study heterogeneity, is the intervention costly, does it use a lot of controls. The full demo asks many more, calls the model from a script and uses *structured output*, so the API guarantees valid JSON. Here we just ask subagents for JSON and then check what they return:

```
For each paper in papers.json, spawn one Haiku subagent, all in parallel. Give each the
instructions in classify.md and the paper txt/<wid>.txt.
Save each reply to verdicts/<wid>.json, check that it parses and has every field
with an allowed value, and show me all verdicts as one table, one row per paper.
```

Why one subagent per paper? Each one reads a whole paper in its own context. Your main chat only gets back the JSON, so it stays short and cheap. Haiku is the smallest model, and a clear prompt is enough for it.

Koessler & Skreta is pure theory, so it should come back `empirical: no`. It drops out here.

## Step 3: Download the replication data

```
For each paper with empirical other than "no" and a replication_url in papers.json,
download its replication package into datasets/<wid>/. They are on Harvard Dataverse
and Zenodo: use their APIs, no login is needed.
```

The Greenstone et al. package is the largest, about 300 MB.

## Step 4: Replicate

```
For each paper with a folder in datasets/, spawn one Sonnet subagent, two at a time.
Ask each to replicate the table named in the paper's `table` field in papers.json:
- The paper is pdfs/<wid>.pdf and the package is datasets/<wid>/ (read-only).
  Use this PDF only; do not look for other versions of the paper.
- Find the code in the package that makes the table, and port it to Python
  (pandas, pyfixest) as replications/<wid>.py. If the package has code but no data,
  stop and say so.
- Print each published coefficient, standard error and N next to its own.
  Type the published numbers in by hand: from the package's own table output if it
  has one, otherwise from the PDF. Never copy them from your own output.
- A number that misses is a result: say by how much, and what you ruled out.
When they are done, show me one table: paper, how many numbers match, how many miss, why.
```

Check a few numbers yourself against the PDF.

## What you should see

| Paper | Classify | Replicate |
|---|---|---|
| Koessler & Skreta | not empirical | — |
| Greenstone et al. | empirical | Table 3 replicates |
| Do & Jacoby | empirical | Table 1 replicates |
| Ganimian et al. | empirical | Table A.4 replicates only in part |
| Cederlöf et al. | empirical | no data: the package has only code |

Two reasons a paper does not replicate:

- **Ganimian et al.** We have the 2021 NBER working paper. The package was made for the 2023 version, and some columns of Table A.4 changed in between.
- **Cederlöf et al.** The paper uses Swedish administrative data, which cannot be shared. The package has only the code.

Ask Claude to explain any miss. Whether your run matches this table is a test of the prompts.

## Next

[`full_demo/`](full_demo/) runs the same steps on 50 papers. It shows how to:

- schedule subagents from a script
- cut costs with prompt caching
- enforce the output format with structured output and with tests (`Spec`)
