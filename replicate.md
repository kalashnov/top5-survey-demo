You are given one paper ID, `<wid>`. Replicate the table named in its `table` field in `papers.json`.

- The paper is `pdfs/<wid>.pdf` and its replication package is `datasets/<wid>/` (read-only).
  Use this PDF only; do not look for other versions of the paper.
- Find the code in the package that makes the table, and port it to Python
  (pandas, pyfixest) as `replications/<wid>.py`. Port the authors' code as written, quirks included.
- If the package has code but no data, stop and say so.
- Print each published coefficient, standard error and N next to your own.
  Type the published numbers in by hand: from the package's own table output if it
  has one, otherwise from the PDF. Never copy them from your own output.
- A number matches if it differs by at most half a unit of the last printed digit.
- A number that misses is a result: say by how much, and what you ruled out.

Reply with: how many numbers match, how many miss, and why.
