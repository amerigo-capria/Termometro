"""Genera Manuale_utente.pdf dal markdown del manuale."""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent
MD_PATH = ROOT / "Manuale_utente.md"
PDF_PATH = ROOT / "Manuale_utente.pdf"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")


class ManualPdf(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Manual", size=8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"Pagina {self.page_no()}/{{nb}}", align="C")


def strip_md(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("`", "")
    text = text.replace("\u2011", "-")  # non-breaking hyphen
    text = text.replace("\u2014", "-")  # em dash
    text = text.replace("\u2013", "-")  # en dash
    text = text.replace("\u2605", "*")  # star
    return text


def main() -> None:
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    pdf = ManualPdf(format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("Manual", "", str(FONT))
    pdf.add_font("Manual", "B", str(FONT_BOLD))
    pdf.set_margins(18, 16, 18)
    usable = pdf.epw

    in_table = False

    for raw in lines:
        line = raw.rstrip()
        pdf.set_x(pdf.l_margin)

        if not line.strip():
            in_table = False
            pdf.ln(3)
            continue

        if line.strip() == "---":
            pdf.ln(2)
            y = pdf.get_y()
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.l_margin, y, pdf.l_margin + usable, y)
            pdf.ln(4)
            continue

        if line.startswith("# "):
            pdf.set_font("Manual", "B", 18)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(usable, 10, strip_md(line[2:]))
            pdf.ln(2)
            continue

        if line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Manual", "B", 13)
            pdf.set_text_color(40, 70, 50)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(usable, 8, strip_md(line[3:]))
            pdf.ln(1)
            continue

        if line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Manual", "B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(usable, 7, strip_md(line[4:]))
            continue

        if line.startswith("|") and re.search(r"\|\s*-+", line):
            continue

        if line.startswith("|"):
            cells = [strip_md(c.strip()) for c in line.strip("|").split("|")]
            pdf.set_font("Manual", "B" if not in_table else "", 9)
            in_table = True
            pdf.set_text_color(30, 30, 30)
            if len(cells) >= 2:
                w0, w1 = usable * 0.28, usable * 0.72
                x = pdf.l_margin
                y = pdf.get_y()
                pdf.set_xy(x, y)
                pdf.multi_cell(w0, 6, cells[0], border=0)
                h0 = pdf.get_y() - y
                pdf.set_xy(x + w0, y)
                pdf.multi_cell(w1, 6, cells[1], border=0)
                h1 = pdf.get_y() - y
                pdf.set_y(y + max(h0, h1, 6))
            else:
                pdf.multi_cell(usable, 6, " | ".join(cells))
            continue

        if re.match(r"^\d+\.\s", line.strip()):
            pdf.set_font("Manual", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(usable, 6, strip_md(line.strip()))
            continue

        if line.lstrip().startswith("- "):
            pdf.set_font("Manual", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(usable, 6, "- " + strip_md(line.lstrip()[2:]))
            continue

        pdf.set_font("Manual", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(usable, 6, strip_md(line))

    pdf.output(str(PDF_PATH))
    print(PDF_PATH)


if __name__ == "__main__":
    main()
