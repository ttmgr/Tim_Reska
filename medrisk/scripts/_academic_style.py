"""Shared academic/scientific PDF styling for all MedRisk reports.

Provides:
- AcademicPDF: portrait or landscape FPDF subclass with clean typography
- SlidePDF: landscape variant for presentation decks
- Colour constants and chart styling
- Unicode safety helper
"""

from __future__ import annotations

from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF

# ============================================================================
# Colour palette -- muted, print-safe, ColorBrewer-inspired
# ============================================================================

# PDF RGB tuples
C_TEXT = (26, 26, 26)
C_HEADING = (26, 26, 26)
C_BODY = (51, 51, 51)
C_CAPTION = (85, 85, 85)
C_FOOTNOTE = (136, 136, 136)
C_ACCENT = (68, 114, 196)      # steel blue
C_TABLE_HDR = (232, 232, 232)
C_TABLE_ALT = (250, 250, 250)
C_BOX_BG = (245, 245, 245)
C_RULE = (200, 200, 200)
C_WHITE = (255, 255, 255)
C_GREEN_BG = (240, 248, 240)   # very light green for highlight
C_RED_BG = (252, 240, 240)     # very light red for highlight

# Matplotlib hex
M_BLUE = "#4472C4"
M_AMBER = "#ED7D31"
M_GREEN = "#70AD47"
M_RED = "#E15759"
M_TEAL = "#59A14F"
M_GREY = "#888888"
M_DARK = "#333333"
M_PURPLE = "#9467BD"
M_LIGHT = "#B0C4DE"


def safe(text: str) -> str:
    """Replace Unicode chars that Helvetica can't render."""
    return (text
            .replace("\u2014", "--")
            .replace("\u2013", "-")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2022", "-")
            .replace("\u00d7", "x")
            .replace("\u2265", ">=")
            .replace("\u2264", "<=")
            .replace("\u2212", "-")
            .replace("\u2192", "->")
            .replace("\u03a3", "Sum")
            .replace("\u03b1", "alpha")
            .replace("\u03b2", "beta")
            .replace("\u03b3", "gamma")
            .replace("\u00b1", "+/-")
            .replace("\u20ac", "EUR")
            .replace("\u00a3", "GBP")
            .replace("\u00fc", "ue")
            .replace("\u00e4", "ae")
            .replace("\u00f6", "oe")
            .replace("\u00dc", "Ue")
            .replace("\u00c4", "Ae")
            .replace("\u00d6", "Oe")
            .replace("\u00df", "ss")
            )


def chart_style():
    """Apply clean academic chart style."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 8.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "axes.grid": True,
        "grid.alpha": 0.15,
        "grid.linewidth": 0.4,
        "figure.facecolor": "white",
        "figure.dpi": 180,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "#cccccc",
    })


# ============================================================================
# Academic PDF -- portrait documents (reports, guides, manuals)
# ============================================================================

class AcademicPDF(FPDF):
    """Portrait A4 document with academic/scientific styling."""

    def __init__(self, header_left: str = "MedRisk v2.0",
                 header_right: str = "", footer_left: str = "the author | Helmholtz Munich | March 2026"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(18, 18, 18)
        self._pw = 210
        self._cw = 210 - 36
        self._fig_n = 0
        self._tbl_n = 0
        self._header_left = header_left
        self._header_right = header_right
        self._footer_left = footer_left
        self._skip_header_pages = 2

    def header(self):
        if self.page_no() <= self._skip_header_pages:
            return
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_FOOTNOTE)
        self.set_y(10)
        self.cell(self._cw / 2, 4, safe(self._header_left))
        self.cell(self._cw / 2, 4, safe(self._header_right), align="R",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.3)
        self.line(18, self.get_y(), self._pw - 18, self.get_y())
        self.set_y(19)

    def footer(self):
        self.set_y(-11)
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.3)
        self.line(18, self.get_y(), self._pw - 18, self.get_y())
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_FOOTNOTE)
        self.cell(self._cw / 2, 5, safe(self._footer_left))
        self.cell(self._cw / 2, 5, str(self.page_no()), align="R")

    # --- Cover ---

    def cover(self, title: str, subtitle: str, byline: str = "",
              extra: str = ""):
        self.add_page()
        self.ln(50)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(*C_FOOTNOTE)
        self.cell(0, 6, safe(self._header_left), align="C",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*C_HEADING)
        self.multi_cell(0, 10, safe(title), align="C")
        self.ln(3)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(*C_BODY)
        self.multi_cell(0, 6, safe(subtitle), align="C")
        self.ln(8)
        self.set_draw_color(*C_ACCENT)
        self.set_line_width(0.6)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(8)
        if byline:
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*C_BODY)
            self.cell(0, 5, safe(byline), align="C",
                      new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*C_CAPTION)
        self.cell(0, 5, "Helmholtz Munich  |  March 2026", align="C",
                  new_x="LMARGIN", new_y="NEXT")
        if extra:
            self.ln(10)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*C_FOOTNOTE)
            self.multi_cell(0, 4.5, safe(extra), align="C")

    # --- Typography ---

    def chapter_head(self, number, title: str):
        if self.get_y() > 40:
            self.add_page()
        self.ln(4)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*C_HEADING)
        label = f"{number}   {title}" if number else title
        self.cell(0, 8, safe(label), new_x="LMARGIN", new_y="NEXT")
        y = self.get_y() + 1
        self.set_draw_color(*C_ACCENT)
        self.set_line_width(0.6)
        self.line(18, y, 70, y)
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.2)
        self.line(70, y, self._pw - 18, y)
        self.ln(5)

    def h2(self, text: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*C_HEADING)
        self.cell(0, 6, safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def h3(self, text: str):
        self.ln(2)
        self.set_font("Helvetica", "BI", 9.5)
        self.set_text_color(*C_HEADING)
        self.cell(0, 5, safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def p(self, text: str):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*C_BODY)
        self.multi_cell(self._cw, 4.8, safe(text))
        self.ln(2)

    def li(self, text: str):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*C_BODY)
        self.cell(5, 4.8, "-")
        self.multi_cell(self._cw - 5, 4.8, safe(text))

    def key_concept(self, text: str):
        y0 = self.get_y()
        self.set_fill_color(*C_BOX_BG)
        self.rect(18, y0, self._cw, 18, "F")
        self.set_fill_color(*C_ACCENT)
        self.rect(18, y0, 2, 18, "F")
        self.set_xy(24, y0 + 2)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_ACCENT)
        self.cell(30, 4, "KEY CONCEPT", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(24, self.get_y())
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_BODY)
        self.multi_cell(self._cw - 10, 4.5, safe(text))
        self.set_y(max(self.get_y(), y0 + 20))
        self.ln(2)

    def source_line(self, text: str):
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_FOOTNOTE)
        self.cell(self._cw, 4, safe(text), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*C_BODY)
        self.ln(1)

    # --- Figures ---

    def figure(self, buf: BytesIO, caption: str, w: float = 145):
        self._fig_n += 1
        buf.seek(0)
        x = (self._pw - w) / 2
        self.image(buf, x=x, w=w)
        self.ln(1)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*C_CAPTION)
        self.multi_cell(self._cw, 4, safe(f"Figure {self._fig_n}. {caption}"))
        self.set_text_color(*C_BODY)
        self.ln(3)

    def embed_chart(self, buf: BytesIO, w: float = 145):
        buf.seek(0)
        self.image(buf, x=(self._pw - w) / 2, w=w)
        self.ln(2)

    # --- Tables ---

    def table_caption(self, caption: str):
        self._tbl_n += 1
        self.set_font("Helvetica", "BI", 8)
        self.set_text_color(*C_CAPTION)
        self.multi_cell(self._cw, 4, safe(f"Table {self._tbl_n}. {caption}"))
        self.set_text_color(*C_BODY)
        self.ln(1)

    def table(self, headers: list[str], rows: list[list[str]],
              col_widths: list[float] | None = None,
              num_cols: list[int] | None = None):
        avail = self._cw
        if col_widths is None:
            w = avail / len(headers)
            col_widths = [w] * len(headers)
        else:
            total = sum(col_widths)
            if abs(total - avail) > 1:
                scale = avail / total
                col_widths = [x * scale for x in col_widths]
        if num_cols is None:
            num_cols = []

        self.set_font("Helvetica", "B", 7.5)
        self.set_fill_color(*C_TABLE_HDR)
        self.set_text_color(*C_HEADING)
        self.set_draw_color(*C_RULE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, safe(h), border="TB", fill=True,
                      align="R" if i in num_cols else "L")
        self.ln()

        self.set_font("Helvetica", "", 7.5)
        for ri, row in enumerate(rows):
            if ri % 2 == 0:
                self.set_fill_color(*C_TABLE_ALT)
            else:
                self.set_fill_color(*C_WHITE)
            for i, val in enumerate(row):
                self.set_text_color(*C_BODY)
                self.cell(col_widths[i], 5, safe(str(val)), border="B",
                          fill=True,
                          align="R" if i in num_cols else "L")
            self.ln()
        self.ln(3)


# ============================================================================
# Slide PDF -- landscape decks (presentations)
# ============================================================================

class SlidePDF(FPDF):
    """Landscape A4 slide deck with academic styling."""

    def __init__(self, n_slides: int = 10,
                 header_right: str = "MedRisk v2.0"):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.set_margins(15, 15, 15)
        self._pw = 297
        self._ph = 210
        self._cw = 297 - 30
        self._n_slides = n_slides
        self._header_right = header_right
        self._fig_n = 0
        self._tbl_n = 0

    def header(self):
        if self.page_no() == 1:
            return
        # Thin top line with project label
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.4)
        self.line(15, 12, self._pw - 15, 12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_FOOTNOTE)
        self.set_xy(self._pw - 60, 6)
        self.cell(45, 4, safe(self._header_right), align="R")
        self.set_text_color(*C_BODY)
        self.set_y(15)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_FOOTNOTE)
        self.cell(0, 5, f"{self.page_no()} / {self._n_slides}", align="R")
        self.set_text_color(*C_BODY)

    # --- Slide elements ---

    def slide_title(self, title: str, subtitle: str = ""):
        self.set_xy(15, 15)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*C_HEADING)
        self.multi_cell(self._cw - 50, 8, safe(title),
                        new_x="LMARGIN", new_y="NEXT")
        y = self.get_y() + 1
        self.set_draw_color(*C_ACCENT)
        self.set_line_width(0.5)
        self.line(15, y, 65, y)
        self.set_draw_color(*C_RULE)
        self.set_line_width(0.2)
        self.line(65, y, 120, y)
        self.ln(5)
        if subtitle:
            self.set_font("Helvetica", "I", 11)
            self.set_text_color(*C_CAPTION)
            self.cell(self._cw, 6, safe(subtitle),
                      new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*C_BODY)
        self.ln(2)

    def body_text(self, text: str, size: float = 11):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*C_BODY)
        self.multi_cell(self._cw, 6, safe(text))
        self.ln(2)

    def bullet(self, text: str, size: float = 11):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*C_BODY)
        self.cell(6, 6, "-")
        self.multi_cell(self._cw - 6, 6, safe(text))

    def source_line(self, text: str):
        self.set_xy(15, self._ph - 14)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*C_FOOTNOTE)
        self.cell(self._cw, 4, safe(text))
        self.set_text_color(*C_BODY)

    def key_metric(self, label: str, value: str, x: float, y: float,
                   w: float = 55):
        self.set_xy(x, y)
        self.set_fill_color(*C_BOX_BG)
        self.rect(x, y, w, 22, "F")
        # Left accent
        self.set_fill_color(*C_ACCENT)
        self.rect(x, y, 2, 22, "F")
        self.set_xy(x + 5, y + 2)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*C_ACCENT)
        self.cell(w - 8, 10, safe(value))
        self.set_xy(x + 5, y + 13)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*C_CAPTION)
        self.cell(w - 8, 5, safe(label))
        self.set_text_color(*C_BODY)

    def figure(self, buf: BytesIO, caption: str, w: float = 200):
        self._fig_n += 1
        buf.seek(0)
        x = (self._pw - w) / 2
        self.image(buf, x=x, w=w)
        self.ln(1)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*C_CAPTION)
        self.set_x(15)
        self.multi_cell(self._cw, 4, safe(f"Figure {self._fig_n}. {caption}"))
        self.set_text_color(*C_BODY)
        self.ln(2)

    def embed_chart(self, buf: BytesIO, w: float = 200):
        buf.seek(0)
        x = (self._pw - w) / 2
        self.image(buf, x=x, w=w)
        self.ln(2)

    def table_caption(self, caption: str):
        self._tbl_n += 1
        self.set_font("Helvetica", "BI", 8)
        self.set_text_color(*C_CAPTION)
        self.multi_cell(self._cw, 4, safe(f"Table {self._tbl_n}. {caption}"))
        self.set_text_color(*C_BODY)
        self.ln(1)

    def table(self, headers: list[str], rows: list[list[str]],
              col_widths: list[float] | None = None,
              num_cols: list[int] | None = None):
        avail = self._cw
        if col_widths is None:
            w = avail / len(headers)
            col_widths = [w] * len(headers)
        else:
            total = sum(col_widths)
            if abs(total - avail) > 1:
                scale = avail / total
                col_widths = [x * scale for x in col_widths]
        if num_cols is None:
            num_cols = []

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*C_TABLE_HDR)
        self.set_text_color(*C_HEADING)
        self.set_draw_color(*C_RULE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, safe(h), border="TB", fill=True,
                      align="R" if i in num_cols else "L")
        self.ln()
        self.set_font("Helvetica", "", 8)
        for ri, row in enumerate(rows):
            if ri % 2 == 0:
                self.set_fill_color(*C_TABLE_ALT)
            else:
                self.set_fill_color(*C_WHITE)
            for i, val in enumerate(row):
                self.set_text_color(*C_BODY)
                self.cell(col_widths[i], 5.5, safe(str(val)), border="B",
                          fill=True,
                          align="R" if i in num_cols else "L")
            self.ln()
        self.ln(3)
