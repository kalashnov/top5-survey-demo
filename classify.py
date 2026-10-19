"""Stage 3: classify each paper in papers.json with Claude; writes verdicts/<wid>.json."""
import argparse
import asyncio
import json
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

PROMPTS = Path(__file__).parent / "prompts"
SCHEMA = json.loads((PROMPTS / "json_schema.json").read_text())


def system_prompt() -> str:
    """The base prompt plus six worked examples: paragraphs.json paired with groundtruth/."""
    fields = SCHEMA["properties"]["verdicts"]["items"]["properties"]
    parts = [
        "", "", "## EXAMPLES", "",
        "The following 6 papers have been carefully audited. Each paragraph "
        "summarizes the paper's relevant methodology, including details that "
        "could mislead a careless reader (logs on the RHS, multi-arm RCT "
        "design, theoretical log-linearization, descriptive stratification). "
        "The JSON shows the correct classification. Study how each paragraph "
        "maps to the verdict.",
        "",
    ]
    for p in json.loads((PROMPTS / "paragraphs.json").read_text())["papers"]:
        gt = json.loads((PROMPTS / "groundtruth" / f"verdict_{p['wid']}.json").read_text())
        v = gt["structured_output"]["verdicts"][0]
        parts += [f"### Example {p['slot']} — {p['role']}", "", "Paper:", p["paragraph"], "",
                  "Correct verdict:",
                  json.dumps({k: v[k] for k in fields if k in v}, indent=2, ensure_ascii=False), ""]
    return (PROMPTS / "system_prompt.md").read_text() + "\n".join(parts)


def user_message(p: dict, body: str) -> str:
    return (f"## {p['wid']}\n"
            f"- **Title**: {p['title'].strip()}\n"
            f"- **Authors**: {p['authors'].strip()}\n"
            f"- **Journal**: {p['journal_code']} {p['publication_year']}\n"
            "- **Full extracted text (top-10K-token excerpt from condenser)**:\n\n"
            f"--- BEGIN PAPER ---\n{body}\n--- END PAPER ---\n")


async def classify(prompt: str, options: ClaudeAgentOptions) -> ResultMessage:
    # Drain the stream: returning mid-iteration leaves the SDK's generator open.
    async for m in query(prompt=prompt, options=options):
        if isinstance(m, ResultMessage):
            result = m
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--txt-dir", type=Path, default=Path("txt"))
    ap.add_argument("--out-dir", type=Path, default=Path("verdicts"))
    ap.add_argument("--limit", type=int, default=0, help="stop after this many papers (0 = all)")
    args = ap.parse_args()

    # No tools, settings or plugins: Claude Code's own context would otherwise ride along.
    options = ClaudeAgentOptions(
        model=args.model, system_prompt=system_prompt(),
        tools=[], allowed_tools=[], setting_sources=[], mcp_servers={}, strict_mcp_config=True,
        skills=[], agents={}, plugins=[],
        output_format={"type": "json_schema", "schema": SCHEMA},
    )
    args.out_dir.mkdir(exist_ok=True)
    done = 0
    for p in json.loads(Path("papers.json").read_text()):
        out, txt = args.out_dir / f"{p['wid']}.json", args.txt_dir / f"{p['wid']}.txt"
        if out.exists() or not txt.exists():
            continue
        r = asyncio.run(classify(user_message(p, txt.read_text(errors="replace")), options))
        if r.structured_output is None:
            raise SystemExit(f"{p['wid']}: no verdict ({r.subtype})")
        out.write_text(json.dumps({"wid": p["wid"], "model": args.model, "usage": r.usage,
                                   **r.structured_output}, indent=1, ensure_ascii=False))
        print(p["wid"], [v["log_dv_likely"] for v in r.structured_output["verdicts"]], flush=True)
        done += 1
        if done == args.limit:
            break


if __name__ == "__main__":
    main()
