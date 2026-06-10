"""
Genera PDF con estética Atalaya/Bound para reportes de inteligencia competitiva.
Paleta: fondo blanco, texto negro, acentos amarillo #FFFF00 y negro #0a0a0a
"""
import re
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak
)
from reportlab.pdfgen import canvas as rl_canvas

# ── Colores ────────────────────────────────────────────────────────────────────
BLACK   = colors.HexColor("#0a0a0a")
YELLOW  = colors.HexColor("#FFFF00")
WHITE   = colors.HexColor("#FFFFFF")
GRAY    = colors.HexColor("#888888")
LGRAY   = colors.HexColor("#cccccc")
DGRAY   = colors.HexColor("#444444")
OFFWHITE= colors.HexColor("#f5f5f5")

W, H = A4


# ── Canvas con header/footer ───────────────────────────────────────────────────
class AtalayaCanvas(rl_canvas.Canvas):
    def __init__(self, *args, client_name="", scan_date="", **kwargs):
        super().__init__(*args, **kwargs)
        self.client_name = client_name
        self.scan_date   = scan_date
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for i, state in enumerate(self._saved_page_states):
            self.__dict__.update(state)
            self._draw_page(i + 1, total)
            super().showPage()
        super().save()

    def _draw_page(self, page_num, total):
        self.saveState()

        # Fondo blanco
        self.setFillColor(WHITE)
        self.rect(0, 0, W, H, fill=1, stroke=0)

        # Banda negra superior
        self.setFillColor(BLACK)
        self.rect(0, H - 14*mm, W, 14*mm, fill=1, stroke=0)

        # Texto header izquierda — amarillo sobre negro
        self.setFillColor(YELLOW)
        self.setFont("Helvetica-Bold", 6)
        self.drawString(15*mm, H - 8.5*mm, "ATALAYA · MONITOR DE COMPETENCIA")

        # Texto header derecha — gris sobre negro
        self.setFillColor(LGRAY)
        self.setFont("Helvetica", 6)
        self.drawRightString(W - 15*mm, H - 8.5*mm, self.client_name.upper())

        # Línea amarilla debajo del header
        self.setStrokeColor(YELLOW)
        self.setLineWidth(2)
        self.line(0, H - 14*mm, W, H - 14*mm)

        # Footer — línea gris clara
        self.setStrokeColor(LGRAY)
        self.setLineWidth(0.5)
        self.line(15*mm, 12*mm, W - 15*mm, 12*mm)

        self.setFillColor(GRAY)
        self.setFont("Helvetica", 6)
        self.drawString(15*mm, 8*mm, f"AENIMA · BOUND · {self.scan_date}")
        self.drawRightString(W - 15*mm, 8*mm, f"{page_num:02d} / {total:02d}")

        self.restoreState()


def _make_styles():
    cover_eyebrow = ParagraphStyle("cover_eyebrow",
        fontName="Helvetica-Bold", fontSize=7, textColor=GRAY,
        spaceAfter=4, leading=10, letterSpacing=2)

    cover_title = ParagraphStyle("cover_title",
        fontName="Helvetica-Bold", fontSize=40, textColor=BLACK,
        spaceAfter=4, leading=44)

    cover_sub = ParagraphStyle("cover_sub",
        fontName="Helvetica", fontSize=10, textColor=GRAY,
        spaceAfter=4, leading=14)

    section_label = ParagraphStyle("section_label",
        fontName="Helvetica-Bold", fontSize=6, textColor=GRAY,
        spaceAfter=2, leading=9, letterSpacing=2)

    h1 = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=18, textColor=BLACK,
        spaceBefore=12, spaceAfter=6, leading=22)

    h2 = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=12, textColor=BLACK,
        spaceBefore=12, spaceAfter=4, leading=16)

    h3 = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=10, textColor=BLACK,
        spaceBefore=8, spaceAfter=3, leading=14)

    body = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9, textColor=DGRAY,
        spaceAfter=5, leading=14)

    bullet = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=9, textColor=DGRAY,
        spaceAfter=3, leading=14, leftIndent=14)

    bold_label = ParagraphStyle("bold_label",
        fontName="Helvetica-Bold", fontSize=9, textColor=BLACK,
        spaceAfter=3, leading=14)

    meta = ParagraphStyle("meta",
        fontName="Helvetica", fontSize=7, textColor=GRAY,
        spaceAfter=2, leading=10)

    return dict(
        cover_eyebrow=cover_eyebrow, cover_title=cover_title,
        cover_sub=cover_sub, section_label=section_label,
        h1=h1, h2=h2, h3=h3, body=body, bullet=bullet,
        bold_label=bold_label, meta=meta
    )


def _hr(color=LGRAY, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=6, spaceBefore=4)


def _hr_yellow():
    return HRFlowable(width="100%", thickness=2, color=YELLOW,
                      spaceAfter=8, spaceBefore=4)


def _parse_markdown(md_text: str, styles: dict) -> list:
    story = []
    lines = md_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            story.append(Spacer(1, 3))
            i += 1
            continue

        if line.startswith("# "):
            text = line[2:].strip()
            story.append(Spacer(1, 4))
            story.append(_hr_yellow())
            story.append(Paragraph(text.upper(), styles["h1"]))
            story.append(_hr())
            i += 1
            continue

        if line.startswith("## "):
            text = line[3:].strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(text.upper(), styles["h2"]))
            story.append(_hr())
            i += 1
            continue

        if line.startswith("### "):
            text = line[4:].strip()
            story.append(Spacer(1, 4))
            # Caja negra con texto blanco para nombre del competidor
            comp_data = [[Paragraph(f"  {text.upper()}", ParagraphStyle(
                "comp_header",
                fontName="Helvetica-Bold", fontSize=9,
                textColor=WHITE, leading=14
            ))]]
            comp_table = Table(comp_data, colWidths=[170*mm])
            comp_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), BLACK),
                ("TOPPADDING",    (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ]))
            story.append(comp_table)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Bullet con bold label
        if line.startswith("- **") and ":**" in line:
            match = re.match(r"- \*\*(.+?):\*\*\s*(.*)", line)
            if match:
                label = match.group(1)
                rest  = match.group(2)
                text  = f"<b>{label}:</b> {rest}"
                story.append(Paragraph(f"· {text}", styles["bullet"]))
                i += 1
                continue

        # Bullet normal
        if line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            story.append(Paragraph(f"· {text}", styles["bullet"]))
            i += 1
            continue

        # Línea normal
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        story.append(Paragraph(text, styles["body"]))
        i += 1

    return story


def generate_pdf(
    client_name: str,
    report_markdown: str,
    scan_date: str = None,
    competitors: list = None
) -> bytes:
    if not scan_date:
        scan_date = datetime.now().strftime("%d.%m.%Y")
    if competitors is None:
        competitors = []

    buffer = io.BytesIO()
    styles = _make_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=22*mm,
        bottomMargin=20*mm,
        title=f"Atalaya · {client_name}",
        author="Aenima Agency",
    )

    story = []

    # ── PORTADA ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20*mm))

    # Banda amarilla decorativa
    banda = Table([[""]], colWidths=[170*mm], rowHeights=[3])
    banda.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), YELLOW)]))
    story.append(banda)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("AENIMA · INTELIGENCIA COMPETITIVA", styles["cover_eyebrow"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph("ATALAYA", styles["cover_title"]))
    story.append(Paragraph("MONITOR DE COMPETENCIA", styles["cover_sub"]))
    story.append(Spacer(1, 8*mm))

    story.append(_hr(LGRAY))
    story.append(Spacer(1, 4))

    # Tabla de info
    info_data = [
        [Paragraph("CLIENTE",       styles["section_label"]),
         Paragraph(client_name.upper(), styles["bold_label"])],
        [Paragraph("FECHA",         styles["section_label"]),
         Paragraph(scan_date,           styles["body"])],
        [Paragraph("COMPETIDORES",  styles["section_label"]),
         Paragraph(str(len(competitors)), styles["body"])],
        [Paragraph("MODELO",        styles["section_label"]),
         Paragraph("LLAMA 3.3 · 70B · GROQ", styles["body"])],
    ]
    info_table = Table(info_data, colWidths=[35*mm, 135*mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), WHITE),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [WHITE, OFFWHITE]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, LGRAY),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    # Lista de competidores
    if competitors:
        story.append(Paragraph("COMPETIDORES ANALIZADOS", styles["section_label"]))
        story.append(Spacer(1, 3))
        for idx, comp in enumerate(competitors):
            name    = comp.get("name", "").upper()
            url     = comp.get("url", "")
            fb      = comp.get("facebook_page", "")
            details = []
            if url: details.append(url)
            if fb:  details.append(f"FB: {fb}")
            detail_str = "  ·  ".join(details)
            story.append(Paragraph(
                f"<b>{idx+1:02d}  {name}</b>  <font color='#888888'>{detail_str}</font>",
                styles["body"]
            ))

    story.append(PageBreak())

    # ── CONTENIDO ──────────────────────────────────────────────────────────────
    story.extend(_parse_markdown(report_markdown, styles))

    # ── PÁGINA FINAL ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Spacer(1, 60*mm))

    banda2 = Table([[""]], colWidths=[170*mm], rowHeights=[3])
    banda2.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), YELLOW)]))
    story.append(banda2)
    story.append(Spacer(1, 6))
    story.append(Paragraph("ATALAYA · MONITOR DE COMPETENCIA", styles["cover_eyebrow"]))
    story.append(Paragraph("AENIMA AGENCY · BOUND", styles["cover_sub"]))
    story.append(Paragraph(f"Generado el {scan_date}", styles["meta"]))

    def make_canvas(filename, doc=None, **kwargs):
        return AtalayaCanvas(
            filename,
            pagesize=A4,
            client_name=client_name,
            scan_date=scan_date,
        )

    doc.build(story, canvasmaker=make_canvas)
    return buffer.getvalue()