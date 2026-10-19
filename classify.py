"""Stage 3: classify each paper in papers.json with Haiku; writes verdicts/<wid>.json.

Usage: python classify.py [N]   (N = stop after N papers; finished papers are skipped)
"""
import asyncio
import json
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

MODEL = "claude-haiku-5-5"
PROMPTS = Path("prompts")
SCHEMA = json.loads((PROMPTS / "json_schema.json").read_text())

# No tools, settings or plugins: Claude Code's own context would otherwise ride along.
OPTIONS = ClaudeAgentOptions(
    model=MODEL, system_prompt=(PROMPTS / "system_prompt.md").read_text(),
    tools=[], allowed_tools=[], setting_sources=[], mcp_servers={}, strict_mcp_config=True,
    skills=[], agents={}, plugins=[],
    output_format={"type": "json_schema", "schema": SCHEMA},
)


async def classify(prompt: str) -> ResultMessage:
    # Drain the stream: returning mid-iteration leaves the SDK's generator open.
    async for m in query(prompt=prompt, options=OPTIONS):
        if isinstance(m, ResultMessage):
            result = m
    return result


limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
Path("verdicts").mkdir(exist_ok=True)
done = 0
for p in json.loads(Path("papers.json").read_text()):
    out, txt = Path(f"verdicts/{p['wid']}.json"), Path(f"txt/{p['wid']}.txt")
    if out.exists() or not txt.exists():
        continue
    prompt = (f"## {p['wid']}\n"
              f"- **Title**: {p['title'].strip()}\n"
              f"- **Authors**: {p['authors'].strip()}\n"
              f"- **Journal**: {p['journal_code']} {p['publication_year']}\n"
              "- **Full extracted text (top-10K-token excerpt from condenser)**:\n\n"
              f"--- BEGIN PAPER ---\n{txt.read_text(errors='replace')}\n--- END PAPER ---\n")
    r = asyncio.run(classify(prompt))
    if r.structured_output is None:
        sys.exit(f"{p['wid']}: no verdict ({r.subtype})")
    out.write_text(json.dumps({"wid": p["wid"], "model": MODEL, "usage": r.usage, **r.structured_output},
                              indent=1, ensure_ascii=False))
    print(p["wid"], [v["log_dv_likely"] for v in r.structured_output["verdicts"]], flush=True)
    done += 1
    if done == limit:
        break
