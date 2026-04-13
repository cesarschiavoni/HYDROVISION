"""Genera PDF de datos-constitucion-sas.md con fpdf2."""

import re
from pathlib import Path
from fpdf import FPDF

SRC = Path(__file__).parent / "datos-constitucion-sas.md"
DST = Path(__file__).parent / "datos-constitucion-sas.pdf"

# Use a Windows TTF font that supports Unicode (DejaVu or fallback to Arial)
_FONT_DIR = Path("C:/Windows/Fonts")


def _sanitize(text):
    """Replace Unicode chars that may cause issues with safe alternatives."""
    text = text.replace("\u2014", "-")   # em dash
    text = text.replace("\u2013", "-")   # en dash
    text = text.replace("\u2018", "'")   # left single quote
    text = text.replace("\u2019", "'")   # right single quote
    text = text.replace("\u201c", '"')   # left double quote
    text = text.replace("\u201d", '"')   # right double quote
    text = text.replace("\u2026", "...")  # ellipsis
    text = text.replace("\u2713", "v")   # checkmark -> v
    text = text.replace("\u2610", "[ ]") # ballot box
    text = text.replace("\u2022", "-")   # bullet
    # Remove emojis (checkmarks etc)
    text = re.sub(r'[\U0001f000-\U0001ffff]', '', text)
    text = text.replace("\u2705", "[OK]")  # green checkmark emoji
    return text


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, "HydroVision AG - Constitucion SAS - Confidencial", align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")


def render_table(pdf, header_line, rows):
    """Render a markdown table."""
    def parse_row(line):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        return cells

    headers = parse_row(header_line)
    col_count = len(headers)
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    col_w = page_w / col_count

    # Header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(52, 73, 94)
    pdf.set_text_color(255, 255, 255)
    for h in headers:
        pdf.cell(col_w, 7, _sanitize(h), border=1, fill=True, align="C")
    pdf.ln()

    # Rows
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    even = False
    for row_line in rows:
        cells = parse_row(row_line)
        if even:
            pdf.set_fill_color(235, 240, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        for i, c in enumerate(cells):
            c = c.replace("**", "")
            pdf.cell(col_w, 7, _sanitize(c), border=1, fill=True)
        pdf.ln()
        even = not even
    pdf.ln(3)


def main():
    text = SRC.read_text(encoding="utf-8")
    lines = text.split("\n")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(18, 15, 18)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Reset x to left margin at start of each line
        pdf.set_x(pdf.l_margin)

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            pdf.set_draw_color(200, 200, 200)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(4)
            i += 1
            continue

        # Title H1
        if stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(20, 60, 100)
            pdf.multi_cell(0, 8, _sanitize(stripped[2:].strip()))
            pdf.ln(2)
            i += 1
            continue

        # H2
        if stripped.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 80, 130)
            pdf.multi_cell(0, 7, _sanitize(stripped[3:].strip()))
            pdf.ln(2)
            i += 1
            continue

        # H3
        if stripped.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 7, _sanitize(stripped[4:].strip()))
            pdf.ln(1)
            i += 1
            continue

        # Table detection
        if "|" in stripped and i + 1 < len(lines) and "---" in lines[i + 1]:
            header_line = stripped
            i += 2  # skip separator
            table_rows = []
            while i < len(lines) and "|" in lines[i].strip():
                table_rows.append(lines[i])
                i += 1
            render_table(pdf, header_line, table_rows)
            continue

        # Bold line (like **text**)
        if stripped.startswith("**") and stripped.endswith("**"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            clean = _sanitize(stripped.replace("**", ""))
            pdf.multi_cell(0, 6, clean)
            pdf.ln(1)
            i += 1
            continue

        # Checklist / bullet
        if stripped.startswith("- ["):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            checked = "[x]" in stripped
            marker = "[v] " if checked else "[ ] "
            clean = re.sub(r"- \[.\]\s*", "", stripped)
            clean = _sanitize(clean.replace("**", ""))
            pdf.multi_cell(0, 6, marker + clean)
            i += 1
            continue

        # Bullet list
        if stripped.startswith("- "):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            clean = _sanitize(stripped[2:].replace("**", ""))
            pdf.multi_cell(0, 6, "- " + clean)
            i += 1
            continue

        # Italic (standalone)
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 6, _sanitize(stripped.strip("*")))
            pdf.ln(1)
            i += 1
            continue

        # Regular paragraph (with inline bold handling)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        clean = _sanitize(stripped.replace("**", ""))
        pdf.multi_cell(0, 6, clean)
        pdf.ln(1)
        i += 1

    pdf.output(str(DST))
    print(f"PDF generado: {DST}")


if __name__ == "__main__":
    main()
