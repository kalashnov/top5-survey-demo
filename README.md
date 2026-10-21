# Demo: classify and replicate Economics papers with an agent

A short version of the tutorial in [`full_demo/`](full_demo/). It takes five papers, listed in [`papers.json`](papers.json):

| Paper | Journal |
|---|---|
| Koessler & Skreta, "Informed Information Design" | JPE 2023 |
| Englmaier, Grimm, Grothe, Schindler & Schudy, "The Effect of Incentives in Nonroutine Analytical Team Tasks" | JPE 2024 |
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
Clone or download https://github.com/kalashnov/top5-survey-demo,
create a Python environment and install full_demo/requirements.txt in it.
```

Claude will ask for permission before it runs commands. Read what it wants to do, then allow it.

## Step 1: Get the papers

```
Download the 5 papers PDFs in `papers.json` listed in json and extract their text. Use the scripts in `full_demo/stage1_collect_papers`. 

Report the paper titles, please
```


## Step 2: Classify

The questions are in [`classify.md`](classify.md): is the paper empirical, is it an experiment, does it study heterogeneity, is the intervention costly, does it use a lot of controls. The full demo asks many more, calls the model from a script and uses *structured output*, so the API guarantees valid JSON. Here we just ask subagents for JSON and then check what they return:

```
For each paper in papers.json, spawn one Haiku subagent, all in parallel. Give each the
instructions in classify.md and the paper text.
Save each reply to verdicts/<wid>.json, check that it correctly as json.

Print back a table, showing the results
```

## Step 3: Download the replication data

```
For each paper classified as empirical and download the replication file using replication_url in papers.json,
download its replication package into datasets/<wid>/. Use the API of Harvard Dataverse
and Zenodo to download.
```


## Step 4: Replicate

```
For each paper with a folder in datasets/, spawn one Sonnet subagent, two at a time.
Give each the instructions in replicate.md and the paper's wid.
When they are done, show me one table: paper, how many numbers match, how many miss, why.
```

Check a few numbers yourself against the PDF.

## What you should see

| Paper | Classify | Replicate |
|---|---|---|
| Koessler & Skreta | not empirical | — |
| Englmaier et al. | empirical | Table 8 replicates |
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
