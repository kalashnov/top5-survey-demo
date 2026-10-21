# Demo: classify and replicate Economics papers with an agent

This is a tutorial on surveying and replicating papers with an LLM. This is the short version; the full version is in [`full_demo/`](full_demo/).

On a sample of 5 papers, listed in [`papers.json`](papers.json), we will:

1. **Classify.** Have subagents answer a fixed set of questions about each paper's methodology.
2. **Replicate.** Have subagents reproduce one table of each remaining paper from the authors' replication package.
3. **Extend.** Ask a subagent to run an interaction table on top of the analysis.


## Setup

1. **Get a subscription.** Sign up at [claude.ai](https://claude.ai) and pick a plan on the [pricing page](https://claude.com/pricing). **Pro** (20 USD a month) is enough.
2. **Install the Claude app.** Download it from [claude.ai/download](https://claude.ai/download) (macOS and Windows) and sign in.
3. Select the **Code** tab in the app:

<img width="284" height="242" alt="Screenshot 2026-10-20 at 20 21 35" src="https://github.com/user-attachments/assets/3d452e5b-c9e5-4371-91ce-0151a5b999cf" />

Then paste the first message:

```
Clone or download https://github.com/kalashnov/top5-survey-demo,
create a Python environment and install full_demo/requirements.txt in it.
```

Claude will ask for permission before it runs commands or writes to the folder.

## Step 1: Get the papers

Ask the agent to download the papers' PDFs with the scripts in [`full_demo/stage1_collect_papers/`](full_demo/stage1_collect_papers/):

```
Download the PDFs of the 5 papers listed in papers.json and extract their text.
Use the scripts in full_demo/stage1_collect_papers.

Please report the paper titles.
```


## Step 2: Classify

Now we ask Claude a few questions about each paper: is it empirical, is it an experiment, does it study heterogeneity, is the intervention costly, does it use a lot of controls. You can read the full prompt for this task in [`classify.md`](classify.md).

```
For each paper in papers.json, spawn one Haiku subagent, all in parallel. Give each the
instructions in classify.md and the paper's text.
Save each reply to verdicts/<wid>.json and check that it is valid JSON.

Print a table with the results.
```

## Step 3: Download the replication data

Now we take the empirical papers and download their datasets.

```
For each paper classified as empirical, download its replication package from
replication_url in papers.json into datasets/<wid>/. Use the APIs of Harvard Dataverse
and Zenodo to download.
```


## Step 4: Replicate

Finally, we ask subagents to replicate a table from each paper and to report the reason if it does not replicate. You can read the full prompt in [`replicate.md`](replicate.md).

```
For each paper with a folder in datasets/, spawn one Sonnet subagent, two at a time.
Give each the instructions in replicate.md and the paper's wid.
When they are done, show me one table: paper, how many numbers match, how many miss, why.
```

If you are interested, ask a few follow-up questions.

## Step 5: Your own interaction table

Now write a prompt yourself. Pick a paper and ask a subagent for a new table: the paper's main regression, with the treatment interacted with characteristics of the subjects.
