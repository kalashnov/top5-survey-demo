"""Stage 1: extract the text of each pdfs/<wid>.pdf to txt/<wid>.txt with PyMuPDF."""
from pathlib import Path

import pymupdf

Path("txt").mkdir(exist_ok=True)
for pdf in sorted(Path("pdfs").glob("*.pdf")):
    out = Path(f"txt/{pdf.stem}.txt")
    if out.exists():
        continue
    with pymupdf.open(pdf) as doc:
        text = "\n\n".join(page.get_text("text") for page in doc)
    out.write_text(text)
    print(pdf.stem, len(text), "characters")
