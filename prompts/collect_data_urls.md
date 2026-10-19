Write a Python script, collect_data_urls.py, that finds the replication package of every
paper in papers.json (fields: wid, doi, title, authors, journal_code, publication_year)
and the paper's text in txt/<wid>.txt.

Sources, tried in this order until one gives a link that passes the checks below:
1. DataCite: deposits whose related identifiers cite the paper's DOI, then a search by title
2. Paper text: the data availability statement in txt/<wid>.txt, and links in it to
   openICPSR, Dataverse, Zenodo, OSF, figshare, Dryad, Mendeley Data or GitHub
3. ScholeXplorer (OpenAIRE): datasets linked to the paper's DOI
4. Crossref: relations recorded on the paper's DOI
5. Harvard Dataverse: search by title
6. Zenodo: search by title
7. World Bank Microdata Library: search by title
8. Econometric Society: the paper's supplementary material page (ECMA only)

Rules:
- Find links only; do not download any package.
- Identify the script with a plain User-Agent; do not send any email address.
- None of these sources needs an API key. Read ZENODO_TOKEN from the environment if it is
  set, to raise Zenodo's rate limit; work without it otherwise.
- A title search only counts as a match if the deposit's title is nearly the paper's title
  (deposits are often called "Replication data for: <title>") and at least one author's
  surname matches.

Check every candidate before accepting it:
- It must be this paper's own package. Reject preprints (arXiv, SSRN, NBER), datasets the
  paper only cites, and software packages it uses.
- In the paper text, accept a link only if it sits in the data availability statement or
  in a sentence that calls it the replication package, data or code for this paper.
- openICPSR mints a DOI per file and per version: keep the project's DOI
  (10.3886/E<number>V<version>), not a file's.
- The DOI must resolve (https://doi.org/api/handles/<doi> returns responseCode 1).
  openICPSR and Zenodo pages may refuse scripted requests; that is fine.
- Where the repository's API gives it (Dataverse, Zenodo), record the package's total size.

Output:
- Add a replication_url field to each paper in papers.json; null if nothing passed.
- Write data_url_log.jsonl: one line per paper, with every source and link tried, why it
  was rejected, the data availability statement if found, and the size if known.
- Print a summary: found / not found, by source and by journal.

Make it safe to rerun: skip papers that already have a replication_url.
Test it on 5 papers first and show me the log before running all of them.
