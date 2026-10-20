"""Stage 1: download each paper's PDF from its pdf_url in papers.json to pdfs/<wid>.pdf."""
import json
import urllib.request
from pathlib import Path

HEADERS = {"User-Agent": "Mozilla/5.0 (top5-survey-demo)"}  # some hosts refuse Python's default agent

Path("pdfs").mkdir(exist_ok=True)
for p in json.loads(Path("papers.json").read_text()):
    out = Path(f"pdfs/{p['wid']}.pdf")
    if out.exists():
        continue
    try:
        request = urllib.request.Request(p["pdf_url"], headers=HEADERS)
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
    except OSError as e:
        print(p["wid"], "failed:", e)
        continue
    if not data.startswith(b"%PDF"):
        print(p["wid"], "failed: not a PDF")
        continue
    out.write_bytes(data)
    print(p["wid"], "ok")
