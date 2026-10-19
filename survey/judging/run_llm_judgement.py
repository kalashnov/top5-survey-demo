"""Stage 3 — classify papers for log-DV specifications. One script, two backends.

``--backend`` chooses who answers:

    --backend ollama  -> backend_ollama.OllamaBackend  (local GPU, free)
    --backend claude  -> backend_claude.ClaudeBackend  (Anthropic API, billed)

Everything else is shared with ``judge``: prompt, schema, body loader, verdict
envelope, sample rule and atomic write.

The sample rule, the same shape as Stages 1-2:

    sample = wids in --subset  ∩  papers with a {wid}.txt in --pdftxt-dir
             −  judging/prompts/blacklist_wids.json   (hardcoded, always subtracted)

``--subset`` is the census: it supplies the wid list and the per-paper header
fields (title, authors, journal_code, publication_year) the prompt carries,
since the ``.txt`` files hold body text alone. A paper Stage 2 has not produced,
or produced empty, is reported ``miss``, so passing the whole census is safe.

``--out-dir`` has no default: a mistyped run must not be able to land in
``judging/prompts/groundtruth/`` and rewrite the few-shot exemplars.

Usage::

    # corpus, local GPU (run detached — see CLAUDE.md)
    python -m survey.judging.run_llm_judgement --backend ollama --think \\
      --out-dir survey/data/output/llm_verdicts_qwen_corpus

    # corpus, Claude (what sonnet_loop.sh drives)
    python -m survey.judging.run_llm_judgement --backend claude --model claude-sonnet-4-6 \\
      --out-dir survey/data/output/llm_verdicts_sonnet_v4_qwen_corpus

    # regenerate the 6 few-shot exemplars the system prompt embeds
    python -m survey.judging.run_llm_judgement --backend claude --model claude-opus-4-7 \\
      --subset     survey/judging/prompts/few_shot_final_6.json \\
      --pdftxt-dir survey/data/archive/pdftxt_top10k_final6 \\
      --out-dir    survey/judging/prompts/groundtruth
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

from survey.judging.judge import (
    FatalBackendError,
    envelope,
    load_body,
    write_atomic,
)
from survey.utils import (
    BLACKLIST_PATH,
    _load_blacklist,
    _load_subset_records,
)

# survey/ — this script lives in survey/judging/, but every path it resolves
# (the census, the extracts, the display paths) is relative to the package root.
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "output"

# The full corpus census: 3,183 records carrying openalex_id + title + authors +
# journal_code + publication_year. The binding constraint on a run is --pdftxt-dir
# (only ~1,926 papers have an excerpt), so this default is safe to leave alone.
DEFAULT_SUBSET = DATA / "sample" / "top5_since_2020.json"
# Stage 2's top-K extracts: median ~9.9K chars, max exactly 10,000. NOT the raw
# `pdftxt/` dir (median ~129K, max ~454K) — see load_body on what that would cost.
DEFAULT_PDFTXT = OUTPUT / "pdftxt_top10k_v4_qwen_corpus"

# Per-backend defaults. Ollama: 2 workers matched to OLLAMA_NUM_PARALLEL=2, each
# with its own slot + prefix cache (~30-40% faster than sequential); num_ctx 16384
# is the combination that fits qwen3:32b on a 24 GB card with q4_0 KV. Claude:
# sequential — the constraint is API rate limits, not GPU slots.
BACKEND_DEFAULTS = {
    "ollama": {"model": "qwen3:32b",         "workers": 2},
    "claude": {"model": "claude-sonnet-4-6", "workers": 1},
}

# Flags that only mean something to Ollama; passing one to Claude is an error.
OLLAMA_ONLY = ("host", "num_ctx", "think", "temperature")


def _build_backend(args: argparse.Namespace):
    if args.backend == "ollama":
        try:
            import ollama
        except ImportError:
            print("Error: `ollama` package not installed. Run `pip install ollama`.",
                  file=sys.stderr)
            raise SystemExit(2)
        from survey.judging.backend.backend_ollama import OllamaBackend
        return OllamaBackend(
            ollama.Client(host=args.host), args.model,
            temperature=args.temperature, num_ctx=args.num_ctx, think=args.think,
        )
    from survey.judging.backend.backend_claude import ClaudeBackend
    return ClaudeBackend(args.model)


def _disp(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT.parent))
    except ValueError:
        return str(p)


def _header_coverage(records: dict[str, dict], fields=("title", "abstract")) -> dict[str, int]:
    """Count how many records are missing each header field. Printed at startup:
    a subset that carries no titles/abstracts silently produces degraded prompts,
    which is exactly the class of bug that made the few-shot block ship empty for
    a whole corpus run."""
    return {f: sum(1 for r in records.values() if not (r.get(f) or "").strip())
            for f in fields}


def _tokens_and_cost(env: dict) -> tuple[int, int, float]:
    """(input_tokens, output_tokens, usd) from either backend's usage shape.

    The two meters differ and are stored verbatim (see judge.JudgeResult), so the
    run summary reads whichever keys are present rather than pretending they are
    the same thing.
    """
    u = env.get("usage") or {}
    tok_in  = u.get("prompt_tokens")     or u.get("input_tokens")  or 0
    tok_out = u.get("completion_tokens") or u.get("output_tokens") or 0
    return tok_in, tok_out, env.get("cost_estimate_usd") or 0.0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stage 3: judge papers for log-DV specifications, "
                    "via a local Ollama model or via Claude.")
    ap.add_argument("--backend", required=True, choices=("ollama", "claude"),
                    help="Who answers. `ollama` = local GPU (free). `claude` = "
                         "Anthropic API (billed). Everything else about the run — "
                         "prompt, schema, sample, envelope — is identical.")
    ap.add_argument("--subset", type=Path, default=DEFAULT_SUBSET,
                    help="Census .json: supplies BOTH the wids to judge AND the prompt "
                         "header fields (title, authors, journal_code, publication_year). "
                         "The .txt files carry body text only, so this is the sole source "
                         "of the header. Papers with no excerpt in --pdftxt-dir are "
                         f"reported `miss`, so the whole census is safe to pass. "
                         f"Default: {_disp(DEFAULT_SUBSET)}")
    ap.add_argument("--pdftxt-dir", type=Path, default=DEFAULT_PDFTXT,
                    help=f"Directory of {{wid}}.txt bodies. Default: {_disp(DEFAULT_PDFTXT)} "
                         "(Stage 2's top-K extracts, ≤10,000 chars each). Point it at "
                         "data/output/pdftxt/ for raw full text — but note those run to "
                         "~454K chars and nothing truncates them.")
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="Where verdict_{wid}.json + run_log.jsonl go. REQUIRED — there is "
                         "deliberately no default, because judging/prompts/groundtruth/ (the few-shot "
                         "exemplars SYSTEM_PROMPT embeds) is a legitimate target and must "
                         "never be hit by accident.")
    ap.add_argument("--model", default=None,
                    help="Model tag. Default depends on --backend: "
                         f"ollama -> {BACKEND_DEFAULTS['ollama']['model']}, "
                         f"claude -> {BACKEND_DEFAULTS['claude']['model']}.")
    ap.add_argument("--workers", type=int, default=None,
                    help="Concurrent papers in flight. Default depends on --backend: "
                         f"ollama -> {BACKEND_DEFAULTS['ollama']['workers']} (match "
                         "OLLAMA_NUM_PARALLEL; each worker gets its own slot and prefix "
                         f"cache), claude -> {BACKEND_DEFAULTS['claude']['workers']} "
                         "(API rate limits).")
    ap.add_argument("--limit", type=int, default=0,
                    help="Judge at most N papers (debug).")
    ap.add_argument("--force", action="store_true",
                    help="Re-judge papers that already have a verdict on disk.")

    g = ap.add_argument_group("ollama-only", "Rejected with --backend claude.")
    g.add_argument("--host", default="http://localhost:11434",
                   help="Ollama server URL (default http://localhost:11434).")
    g.add_argument("--num-ctx", type=int, default=16_384,
                   help="Ollama context window in tokens (default 16384). Worst-case "
                        "prompt on top-K bodies is ~10K tokens; 16K leaves room for "
                        "thinking + answer, and at OLLAMA_NUM_PARALLEL=2 with q4_0 KV a "
                        "32B model still fits a 24 GB card. Ollama truncates anything "
                        "longer SILENTLY, so the backend warns when a prompt won't fit.")
    g.add_argument("--think", action="store_true",
                   help="Enable the reasoning channel (qwen3, deepseek-r1). Reasoning "
                        "streams in message.thinking; the schema constrains only "
                        "message.content, so the model reasons freely before committing.")
    g.add_argument("--temperature", type=float, default=0.0,
                   help="Sampling temperature (default 0.0 for reproducibility).")

    args = ap.parse_args()

    for k, v in BACKEND_DEFAULTS[args.backend].items():
        if getattr(args, k) is None:
            setattr(args, k, v)

    if args.backend == "claude":
        supplied = {f for f in OLLAMA_ONLY
                    if any(a == f"--{f.replace('_', '-')}"
                           or a.startswith(f"--{f.replace('_', '-')}=")
                           for a in sys.argv[1:])}
        if supplied:
            ap.error(f"--backend claude does not accept ollama-only flag(s): "
                     f"{', '.join('--' + f.replace('_', '-') for f in sorted(supplied))}")

    if not args.subset.exists():
        print(f"Error: subset file not found: {args.subset}", file=sys.stderr)
        return 1
    if not args.pdftxt_dir.exists():
        print(f"Error: --pdftxt-dir not found: {args.pdftxt_dir}", file=sys.stderr)
        return 1
    args.subset = args.subset.resolve()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    run_log = out_dir / "run_log.jsonl"

    # Force line-buffered stdout: under `nohup python -m ...` the default block
    # buffering hides per-paper progress until the whole run ends.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    # --- sample: subset ∩ pdftxt − blacklist -------------------------------
    # The blacklist is hardcoded and applies to every stage, so both backends
    # judge the same denominator.
    records = _load_subset_records(args.subset)
    n_subset = len(records)
    blacklist = _load_blacklist()
    records = {w: r for w, r in records.items() if w not in blacklist}
    n_blacklisted = n_subset - len(records)
    wids = list(records)
    if args.limit:
        wids = wids[: args.limit]

    print(f"backend:   {args.backend}   model: {args.model}   workers: {args.workers}")
    print(f"subset:    {_disp(args.subset)}  ({n_subset} wids"
          f"{f', -{n_blacklisted} blacklisted' if n_blacklisted else ''}"
          f" -> {len(wids)} to consider)")
    print(f"blacklist: {BLACKLIST_PATH.name}  ({len(blacklist)} wids)")
    print(f"bodies:    {_disp(args.pdftxt_dir)}")
    print(f"out:       {_disp(out_dir)}")
    if args.backend == "ollama":
        print(f"ollama:    host={args.host}  num_ctx={args.num_ctx:,}  "
              f"think={args.think}  temp={args.temperature}")

    gaps = _header_coverage(records, fields=("title", "authors"))
    if any(gaps.values()):
        print(f"WARNING: subset is missing header fields — {gaps['title']}/{len(records)} "
              f"wids have no title, {gaps['authors']}/{len(records)} no authors. Those "
              f"prompts carry an empty header line. Pass a census with full records.")
    print(flush=True)

    backend = _build_backend(args)

    n_done = n_skip = n_miss = n_fail = 0
    sums = {"in": 0, "out": 0, "cost": 0.0, "elapsed_s": 0.0}
    print_lock = Lock()
    t_run = time.time()

    def _log(msg: str) -> None:
        """Thread-safe progress sink for the backend, so two workers streaming at
        once don't interleave their per-chunk output."""
        with print_lock:
            print(msg, flush=True)

    # --- pre-filter: skip (already judged) and miss (no usable body) --------
    # skip is checked first: it's a stat() where miss is a file read.
    to_judge: list[tuple[int, str, dict, str, dict]] = []
    for i, wid in enumerate(wids, 1):
        if (out_dir / f"verdict_{wid}.json").exists() and not args.force:
            print(f"[{i:>4d}/{len(wids)}] skip  {wid}  (already judged)")
            n_skip += 1
            continue
        loaded = load_body(wid, args.pdftxt_dir)
        if loaded is None:
            why = "empty body" if (args.pdftxt_dir / f"{wid}.txt").exists() else "no body text"
            print(f"[{i:>4d}/{len(wids)}] miss  {wid}  ({why})")
            n_miss += 1
            continue
        body, provenance = loaded
        to_judge.append((i, wid, records[wid], body, provenance))

    def _process(item) -> tuple[str, dict | None]:
        i, wid, meta, body, provenance = item
        _log(f"[{i:>4d}/{len(wids)}] start {wid}  body={provenance['body_chars']:,} chars  "
             f"title=\"{(meta.get('title') or '')[:60]}\"")
        try:
            result = backend.judge_one(wid, meta, body, provenance, _log)
        except FatalBackendError:
            raise                                   # halts the whole run — see below
        except Exception as e:                      # noqa: BLE001
            _log(f"[{i:>4d}/{len(wids)}] fail  {wid}  ({type(e).__name__}: {str(e)[:140]})")
            return ("fail", None)

        env = envelope(wid, meta, provenance, backend, result)
        write_atomic(out_dir / f"verdict_{wid}.json", env)

        verdicts = env["structured_output"]["verdicts"]
        v = verdicts[0] if verdicts else {}
        tok_in, _, usd = _tokens_and_cost(env)
        _log(f"[{i:>4d}/{len(wids)}] {'done ' if verdicts else 'warn '}{wid}  "
             f"{env['elapsed_s']:>6.1f}s  tok_in={tok_in:>6d}  "
             f"{f'${usd:.3f}  ' if usd else ''}"
             f"emp={v.get('is_empirical','-'):<8s} log_dv={v.get('log_dv_likely','-'):<11s} "
             f"xform={v.get('transformation','-')}")
        return ("done", env)

    # --- dispatch ----------------------------------------------------------
    # A FatalBackendError dooms every remaining paper: stop dispatching and
    # exit rc=2, which sonnet_loop.sh depends on.
    fatal: FatalBackendError | None = None
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_process, item): item for item in to_judge}
        for fut in as_completed(futs):
            try:
                status, env = fut.result()
            except FatalBackendError as e:
                fatal = e
                for f in futs:
                    f.cancel()
                break
            if status == "fail":
                n_fail += 1
            elif env is not None:
                tok_in, tok_out, usd = _tokens_and_cost(env)
                sums["in"]        += tok_in
                sums["out"]       += tok_out
                sums["cost"]      += usd
                sums["elapsed_s"] += env["elapsed_s"]
                n_done += 1

    elapsed = time.time() - t_run
    print()
    if fatal:
        print(f"FATAL {fatal}")
        print("Exiting rc=2 so the outer loop halts instead of burning the backlog.")
    print(f"elapsed: {elapsed:.1f}s")
    print(f"done={n_done}  skip={n_skip}  miss={n_miss}  fail={n_fail}")
    print(f"tokens: in={sums['in']:,}  out={sums['out']:,}"
          + (f"   est. cost: ~${sums['cost']:.3f}" if sums["cost"] else "   (local GPU: $0)"))
    print(f"results in {_disp(out_dir)}")

    entry = {
        "ts":                 _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "backend":            args.backend,
        "model":              args.model,
        "subset":             _disp(args.subset),
        "pdftxt_dir":         _disp(args.pdftxt_dir),
        "workers":            args.workers,
        "papers_done":        n_done,
        "papers_skipped":     n_skip,
        "papers_missing":     n_miss,
        "papers_failed":      n_fail,
        "tokens":             {"input": sums["in"], "output": sums["out"]},
        "cost_usd_estimate":  round(sums["cost"], 4) if sums["cost"] else None,
        "elapsed_s_wall":     round(elapsed, 1),
        "elapsed_s_per_call": round(sums["elapsed_s"], 1),
        "fatal":              str(fatal) if fatal else None,
    }
    if args.backend == "ollama":
        entry.update({"host": args.host, "num_ctx": args.num_ctx, "think": args.think})
    with run_log.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"appended run summary to {_disp(run_log)}")

    return 2 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
