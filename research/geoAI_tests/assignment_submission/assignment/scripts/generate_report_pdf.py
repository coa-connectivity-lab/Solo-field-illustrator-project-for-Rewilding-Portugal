"""
Phase 7: render the written report (output/report_source.md) to a PDF at
output/coa_valley_livability_report.pdf. Simple, direct markdown-to-PDF
rendering (title, ## headers, (i)/(ii) paragraphs) -- no external converter
needed given the report's plain structure.
"""

import re

from fpdf import FPDF

from config import OUTPUT_DIR

SOURCE_PATH = OUTPUT_DIR / "report_source.md"
PDF_PATH = OUTPUT_DIR / "coa_valley_livability_report.pdf"


def clean_text(s: str) -> str:
    # fpdf2's default core fonts are Latin-1; keep special characters
    # readable if a non-Latin-1 glyph slips in.
    replacements = {
        "–": "-", "—": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"',
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


if __name__ == "__main__":
    text = SOURCE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(18, 15, 18)

    for raw_line in lines:
        line = clean_text(raw_line.strip())
        if not line:
            pdf.ln(2)
            continue
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 15)
            pdf.multi_cell(0, 8, line[2:])
            pdf.ln(1)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 11.5)
            pdf.ln(1)
            pdf.multi_cell(0, 6, line[3:])
            pdf.ln(0.5)
        else:
            # Bold markers **text** rendered as plain text (kept simple);
            # strip markdown bold/backtick syntax for clean PDF prose.
            clean = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            clean = re.sub(r"`(.*?)`", r"\1", clean)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.multi_cell(0, 4.6, clean)

    pdf.output(str(PDF_PATH))
    print(f"Saved {PDF_PATH}")
    print(f"Page count: {pdf.page_no()}")
