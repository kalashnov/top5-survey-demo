# Demo: survey and replication of papers in Economics

This is a tutorial on a mass survey and replication of papers using an LLM. It shows how to:

| | |
|---|---|
| **Run, manage and schedule dozens of subagents** | with the API · simply in chat |
| **Save on costs** | local models · tight prompts · context control · prompt caching · batch processing |

In this toy example, we will:

1. **Survey.** Survey the methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`.
2. **Replicate.** Ask the agents to replicate the empirical papers in the sample in an organized way.
3. **Extend.** The next step is bounded only by imagination.

> [!NOTE]
> **ChatGPT and other providers.** The whole tutorial is written with Claude in mind, but a large part of it is not specific to Claude. Some of the steps can run with any agent; others may require rewriting some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

The repo is small enough not to eat any sensible part of your quota on a 20 USD subscription.


## Stages

The tutorial is organized in stages. If you just want to skip it and execute the code, skip to the **What to do** paragraph. Also, if you are not interested in some stages, you may ask your agent to do that stage for you.

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
3. **Download replication data.** 6 of the 50 so far.
4. **Replicate the published regressions.** 5 of the 50 so far.

## Stage 1: Collect papers

*Covers: code exctraction first, then subagents*

The first thing is to collect any public URLs for each paper. To save time, the repo already contains URLs for each paper, but generally a good approach is to ask your agent to write a script that systematically reviews the following sources:

1. OpenAlex
2. Semantic Scholar
3. NBER
4. arXiv

Here is a suggested prompt: [`stage1_collect_papers/collect_urls.md`](stage1_collect_papers/collect_urls.md).

The result will contain mistakes: some links will lead to other papers, and some will lead to supplementary material instead. Some papers will have no link, even though the paper is public on the author's website. A good approach is to run a number of **Haiku subagents** tasked each with a couple of papers to check for the mistakes and/or search the web for the correct versions. This is more expensive than scraping the APIs of the sources above with code, but also, we have already narrowed down the task before handing it to LLMs.

> [!NOTE]
> For this exercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here and will learn about subagents on a more exciting example.

**What to do.** To download the PDFs from my list, run (this will take a few minutes):

```bash
python stage1_collect_papers/fetch_pdfs.py
```

Then extract the plain text from the PDFs:

```bash
python stage1_collect_papers/extract_text.py
```


## Stage 2: Classifying the methodology of papers

*Covers: subagents at scale, verose prompts, few-shot examples, prompt caching, structured output, batch processing*

Now we arrive at the fun part: running an army of subagents. The idea of this stage is as follows. Let the agents read the paper and answer a few questions: Do they run an experiment? Do they run difference-in-differences? What is the source of the data?

Our virtues and our vices:

- **Virtue:** We ask a set of simple questions about a given input. No exploration or problem solving is needed.
- **Vice:** We need to classify thousands of papers.
- **Vice:** We need structured output, so that it is ready to load into Stata and explore.

Therefore, we will heavily optimize the cost per paper. Here are a few ways to do it:

1. **Pre-screen with a local model.** We can run a local model to pre-screen paper texts and throw away anything not related to methodology. UCSD's Slurm cluster can run a local model large enough for this task. I do not cover this in detail, because it requires more involvement. Less input text means lower costs.
2. **A long prompt with examples.** We use a very verbose, clear prompt with a bunch of examples, and we validate this prompt with a few experiments/iterations. The prompt for this task is in [`stage2_classify/system_prompt.md`](stage2_classify/system_prompt.md). A really good prompt lets us use smaller models.
3. **Prompt caching.** One may worry that a larger prompt means more input, and therefore higher costs. But the prompt doesn't change from request to request, and if everything is designed correctly, it is cached and billed at a 10% rate. The larger part of the input is the paper anyway.
4. **Structured output.** Finally, we use a feature called "structured output". It constrains the model to output valid JSON, which we can then use to construct our final dataset. The schema for this application is in [`stage2_classify/json_schema.json`](stage2_classify/json_schema.json).
5. **Batch processing.** The other way to save is batch processing, which we do not use here. Most providers let you submit a job as a "batch" instead of "on demand". They guarantee a response within 24 hours, but are not obliged to answer right away, and they give significant discounts. However, it also involves tradeoffs, e.g. it might be harder to manage the prompt cache (which expires). For Claude, it also doesn't work with a subscription. At my scale I found that a 100 USD subscription, though it adds some inconvenience, is the most cost-effective option, so I do not rely on batch processing.

**What to do.**

For this stage you need to make sure that you are authenticated in the Claude Code command line interface:

```bash
claude -p "Reply with OK"
```

> [!NOTE]
> **ChatGPT and other providers.** If you use ChatGPT, you will need to ask your agent to adapt the code to your provider.

To run the classification, just execute (this already implements all of the recommendations above):

```bash
python stage2_classify/classify.py          # writes verdicts/<wid>.json
```

This will output one JSON file per paper with the answers to the questions we asked.

## Stage 3: Download replication data

*Covers: browser agents*

For downloading datasets we follow the same approach as for PDFs. We first need to collect a list of URLs (already collected for this example). Ask the agent to write code that systematically scrapes the following sources:

1. DataCite
2. Harvard Dataverse
3. Zenodo
4. ScholeXplorer (OpenAIRE)
5. Crossref
6. World Bank Microdata Library
7. Econometric Society
8. The paper's own text for direct links

Here is a suggested prompt: [`stage3_replication_data/collect_data_urls.md`](stage3_replication_data/collect_data_urls.md).

Once you have the links, downloading is more of a problem than for PDFs, because it usually requires you to consent to something and/or leave your contact details. Some repositories (e.g. Harvard Dataverse and Zenodo) have an API. You can ask your agent to figure out the API and run code to download the datasets. Either way, you need to babysit it.

For some repositories, downloading cannot be efficiently automated. Here are the options:

1. **Open the links, download by hand.** Ask Claude for Chrome to open each of the links in a new tab, and go over them manually.
2. **Let Claude download.** Ask Claude for Chrome to download them itself: this spends a lot of tokens, is very slow and quite unreliable, but might save your own time.

Sometimes a package doesn't contain the data itself, but provides instructions on how to fetch the data from another source. Agents are quite good at this most of the time; just ask them to follow the authors' instructions.

**What to do.** For this tutorial I suggest manually downloading a few replication packages, e.g. these. After they are downloaded, just ask Claude to go into your downloads folder and copy them into the project.

| Paper | Size | Repository | Package |
|---|---|---|---|
| W4401126511, AER 2024 | 4 MB | openICPSR | https://doi.org/10.3886/E197302V1 |
| W4405354213, REStud 2024 | 16 MB | Zenodo | https://doi.org/10.5281/zenodo.10783446 |
| W4387449673, JPE 2023 | 20 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/NYSNOT |
| W3174918233, AER 2021 | 33 MB | openICPSR | https://doi.org/10.3886/E121941V1 |
| W4407240810, QJE 2025 | 214 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/PDFDKR |
| W3186531035, AER 2024 | 1.2 GB | openICPSR | https://doi.org/10.3886/E198004V1 |

## Stage 4: Replication

*Covers: context management, orchestrating subagents from chat, testing*

This is another stage where we will heavily use subagents. However, this time the task requires the agents to explore and use whatever tools they need. Still, we need to add some structure to their search.

A good way to add structure is to recognize that our unit of analysis is a regression. A regression is more or less determined by its right-hand side and left-hand side. So we need the subagent to provide us with

1. a prepared dataset,
2. the right-hand side, the left-hand side and other details of the specification (e.g. the standard errors variant),
3. the published coefficients.

This is where we fix the `Spec` interface. It registers the model specification the agent wants to fit and its reference values. After that, the code that we fixed in advance runs the regression, checks the published coefficients against the result and reports back whether the paper replicates or not.

This way we

1. have a guardrail that the agent did indeed check the coefficients against the published ones,
2. have the replication results in a structured format as well (a set of `Spec`s), which can later be collected into a dataset of their own.

You will find that papers fail to replicate for various reasons: the package doesn't contain the required data, the version of the PDF we have is not the published version, or the authors indeed made a mistake. But in most cases they replicate well.

> [!NOTE]
> Why do we use *sub*agent, and why do we ask to process one paper at a time? For both quality and cost. We do not want each our main chat to carry context from processing of other papers, for two reasons: 1) longer contexts are expensive, and 2) longer contexts may deteriorate quality.


**What to do.**

The prompt for this stage is in [`stage4_replicate/replicate.md`](stage4_replicate/replicate.md). The prompt asks a subagent to take a specific paper and replicate tables from it. You can either write scheduling code in the spirit of Stage 2, or just ask in chat something like this:

```
Run 1 sonnet subagent for each paper with a dataset (2 in parallel),
prompt them with replicate.md and ask them to replicate the paper. Report back with the results.
```

The chat will spawn subagents and talk to them on your behalf.

The output of the agents should be data preparation scripts and registered regressions, which they either could or could not replicate.

Check that the registered tables replicate:

```bash
pytest stage4_replicate            # one test per published column
```

## Stage 5: new analysis

Suppose, instead of just replicating the analysis of the authors we want to extend it. Here there are two useful approaches. 

First example will require decision for each seperate paper from scratch: Just as an example, we want them to systematically run interaction tables. Then, we can write `ISpec`, that will formalize interaction tables and write a prompt that will ask an agent to 

Then, we can register another version of `Spec`, e.g. `ISpec` (`I` for interaction) and ask the subagents to come up with sensible interaction regressions. Of course, we should also come up with some automated way to validate/aggregate the agent's output.

Another example, we can try to test, what if we replace all left hand sides with `exp` -- we can do it from the shared code we wrote in advance. There is no need to spawn a new subagent for each paper from scratch

## Take home lessons:

1. **Narrow the task with code first.** Scripts collect links, download files and extract text for free. LLMs only get what code cannot do, such as fixing wrong links.
3. **Keep the prompt fixed.** A prompt that does not change is cached and billed at a fraction of the price; the paper is the bulk of the input. Anything that changes from agent to agent should go after the initial prompt
4. **Fix the format of output with any means** It can be strictly enforced structured output, or it could be the same testing procedure on the agent's output.
5. **One subagent per paper for a long task.** A short context is cheaper and gives better answers.

## More tips

- **Worktrees.** When you start a chat (or a subagent), ask it to `work in a worktree`. This gives the agent their own folder, where they can do whatever they want.
- **Pull requests.** Having dozens of subagent each working on their paper makes it hard to review their results in detail. Ask them to submit a pull request to the github repo after they are done in their worktree. This way you can see what they done, before it reaches the main project folder. Generally, using git is a requirement here, to always be able to rollback their changes
- **Questions document.** Subagents may want you to make some decisions they hesitate to do on their own. Make a document, and ask them to collect questions in a document. You can answer in the document and then just instruct them to read the answer from there. There are numerous ways to improve: require to structure the document in a certain way, provide tags to filter/classify questions, and even have small subagents, whom you can ask follow up questions on the decisions to make

## Related work

- **Chen and Roth (2024), "Logs with Zeros? Some Problems and Solutions", QJE.** Their replication code, [jiafengkevinchen/logs-public](https://github.com/jiafengkevinchen/logs-public), re-estimates the log specifications of published papers. The classification question in Stage 2, whether a paper logs its outcome, comes from the same problem.
- **Peter Hull** ([@instrumenthull](https://x.com/instrumenthull)) used an AI agent to read more than 5,000 top-five papers from the last ten years and find two-way fixed effects regressions with staggered adoption, to measure how much "negative weights" matter in practice. The writeup is ["Two-Way Fixed Effects and Modern Difference-in-Differences: An Empirical Comparison"](https://www.dropbox.com/scl/fi/ago5vsi89l2ns388rwhgz/did_reanalysis.pdf?rlkey=zxv893g3j5j8dpqkwxsy48o6q), and the repository [peterdhull/twfe-replication](https://github.com/peterdhull/twfe-replication) reproduces its figures.
- **Paul Goldsmith-Pinkham** teaches [Claude Code for applied economists](https://markusacademy.substack.com/p/claude-code-for-applied-economists) and has proposed [LLM-friendly academic papers](https://paulgp.substack.com/p/llm-friendly-academic-papers-a-proposal), whose replication packages an agent can run and verify.
