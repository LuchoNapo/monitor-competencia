"""
Genera PDF con estética Atalaya/Bound para reportes de inteligencia competitiva.
Paleta: negro #0a0a0a, amarillo #FFFF00, blanco #FFFFFF, gris #555555
"""
import re
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

# ── Colores ────────────────────────────────────────────────────────────────────
BLACK   = colors.HexColor("#0a0a0a")
YELLOW  = colors.HexColor("#FFFF00")
WHITE   = colors.HexColor("#FFFFFF")
GRAY    = colors.HexColor("#555555")
DGRAY   = colors.HexColor("#222222")
LGRAY   = colors.HexColor("#aaaaaa")

W, H = A4  # 210 x 297 mm

# ── Canvas con header/footer en cada página ────────────────────────────────────
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

        # Fondo negro total
        self.setFillColor(BLACK)
        self.rect(0, 0, W, H, fill=1, stroke=0)

        # Línea amarilla superior
        self.setStrokeColor(YELLOW)
        self.setLineWidth(1.5)
        self.line(15*mm, H - 12*mm, W - 15*mm, H - 12*mm)

        # Header izquierda
        self.setFillColor(YELLOW)
        self.setFont("Helvetica-Bold", 6)
        self.drawString(15*mm, H - 9*mm, "ATALAYA · MONITOR DE COMPETENCIA")

        # Header derecha — cliente
        self.setFillColor(LGRAY)
        self.setFont("Helvetica", 6)
        txt = self.client_name.upper()
        self.drawRightString(W - 15*mm, H - 9*mm, txt)

        # Línea footer
        self.setStrokeColor(DGRAY)
        self.setLineWidth(0.5)
        self.line(15*mm, 12*mm, W - 15*mm, 12*mm)

        # Footer izquierda
        self.setFillColor(GRAY)
        self.setFont("Helvetica", 6)
        self.drawString(15*mm, 8*mm, f"AENIMA · BOUND · {self.scan_date}")

        # Footer derecha — paginado
        self.drawRightString(W - 15*mm, 8*mm, f"{page_num:02d} / {total:02d}")

        self.restoreState()


def _make_styles():
    base = dict(fontName="Helvetica", textColor=WHITE, backColor=BLACK)

    cover_eyebrow = ParagraphStyle("cover_eyebrow",
        fontName="Helvetica-Bold", fontSize=7, textColor=YELLOW,
        spaceAfter=4, leading=10, letterSpacing=3)

    cover_title = ParagraphStyle("cover_title",
        fontName="Helvetica-Bold", fontSize=36, textColor=WHITE,
        spaceAfter=6, leading=40)

    cover_sub = ParagraphStyle("cover_sub",
        fontName="Helvetica", fontSize=9, textColor=GRAY,
        spaceAfter=4, leading=14)

    section_label = ParagraphStyle("section_label",
        fontName="Helvetica-Bold", fontSize=6, textColor=YELLOW,
        spaceAfter=3, leading=9, letterSpacing=2)

    h1 = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=16, textColor=WHITE,
        spaceBefore=14, spaceAfter=6, leading=20)

    h2 = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=11, textColor=YELLOW,
        spaceBefore=12, spaceAfter=4, leading=15)

    h3 = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=9, textColor=WHITE,
        spaceBefore=8, spaceAfter=3, leading=13)

    body = ParagraphStyle("body",
        fontName="Helvetica", fontSize=8.5, textColor=LGRAY,
        spaceAfter=5, leading=13)

    bullet = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=8.5, textColor=LGRAY,
        spaceAfter=3, leading=13, leftIndent=12, bulletIndent=0)

    bold_label = ParagraphStyle("bold_label",
        fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE,
        spaceAfter=3, leading=13)

    meta = ParagraphStyle("meta",
        fontName="Helvetica", fontSize=7, textColor=GRAY,
        spaceAfter=2, leading=10)

    return dict(
        cover_eyebrow=cover_eyebrow, cover_title=cover_title,
        cover_sub=cover_sub, section_label=section_label,
        h1=h1, h2=h2, h3=h3, body=body, bullet=bullet,
        bold_label=bold_label, meta=meta
    )


def _hr(color=DGRAY, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=6)


def _parse_markdown(md_text: str, styles: dict) -> list:
    """Convierte markdown básico a flowables de ReportLab."""
    story = []
    lines = md_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            story.append(Spacer(1, 3))
            i += 1
            continue

        # H1
        if line.startswith("# "):
            text = line[2:].strip()
            story.append(Spacer(1, 6))
            story.append(_hr(YELLOW, 1))
            story.append(Paragraph(text.upper(), styles["h1"]))
            story.append(_hr(DGRAY))
            i += 1
            continue

        # H2
        if line.startswith("## "):
            text = line[3:].strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"// {text.upper()}", styles["h2"]))
            story.append(_hr())
            i += 1
            continue

        # H3
        if line.startswith("### "):
            text = line[4:].strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"[ {text.upper()} ]", styles["h3"]))
            i += 1
            continue

        # Bullet con bold label (- **Label:** texto)
        if line.startswith("- **") and ":**" in line:
            match = re.match(r"- \*\*(.+?):\*\*\s*(.*)", line)
            if match:
                label = match.group(1)
                rest  = match.group(2)
                text  = f"<b><font color='#FFFFFF'>· {label}:</font></b> {rest}"
                story.append(Paragraph(text, styles["bullet"]))
                i += 1
                continue

        # Bullet normal
        if line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            story.append(Paragraph(f"· {text}", styles["bullet"]))
            i += 1
            continue

        # Bold standalone **texto**
        if line.startswith("**") and line.endswith("**"):
            text = line[2:-2]
            story.append(Paragraph(text, styles["bold_label"]))
            i += 1
            continue

        # Línea normal — procesar bold inline
        text = re.sub(r"\*\*(.+?)\*\*", r"<b><font color='#FFFFFF'>\1</font></b>", line)
        story.append(Paragraph(text, styles["body"]))
        i += 1

    return story


def generate_pdf(
    client_name: str,
    report_markdown: str,
    scan_date: str = None,
    competitors: list = None
) -> bytes:
    """
    Genera el PDF y devuelve bytes para st.download_button.
    """
    if not scan_date:
        scan_date = datetime.now().strftime("%d.%m.%Y")

    buffer = io.BytesIO()
    styles = _make_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title=f"Atalaya · {client_name}",
        author="Aenima Agency",
    )

    story = []

    # ── PORTADA ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 30*mm))

    story.append(Paragraph("AENIMA · INTELIGENCIA COMPETITIVA", styles["cover_eyebrow"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("ATALAYA", styles["cover_title"]))
    story.append(Spacer(1, 2))

    story.append(Paragraph("MONITOR DE COMPETENCIA", styles["cover_sub"]))
    story.append(Spacer(1, 8*mm))

    story.append(_hr(YELLOW, 1))
    story.append(Spacer(1, 4*mm))

    # Info del reporte en tabla
    info_data = [
        [Paragraph("CLIENTE", styles["section_label"]),
         Paragraph(client_name.upper(), styles["h3"])],
        [Paragraph("FECHA", styles["section_label"]),
         Paragraph(scan_date, styles["body"])],
        [Paragraph("COMPETIDORES", styles["section_label"]),
         Paragraph(str(len(competitors)) if competitors else "—", styles["body"])],
        [Paragraph("MODELO", styles["section_label"]),
         Paragraph("LLAMA 3.3 · 70B · GROQ", styles["body"])],
    ]
    info_table = Table(info_data, colWidths=[35*mm, 120*mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), BLACK),
        ("TEXTCOLOR",   (0,0), (-1,-1), WHITE),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [BLACK, DGRAY]),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW",   (0,0), (-1,-1), 0.3, DGRAY),
    ]))
    story.append(info_table)

    story.append(Spacer(1, 8*mm))
    story.append(_hr(DGRAY))

    # Lista de competidores en portada
    if competitors:
        story.append(Spacer(1, 4))
        story.append(Paragraph("COMPETIDORES ANALIZADOS", styles["section_label"]))
        story.append(Spacer(1, 2))
        for idx, comp in enumerate(competitors):
            name = comp.get("name", "").upper()
            url  = comp.get("url", "")
            fb   = comp.get("facebook_page", "")
            meta_str = f" · FB: {fb}" if fb else ""
            url_str  = f" · {url}"    if url  else ""
            story.append(Paragraph(
                f"<b><font color='#FFFF00'>{idx+1:02d}</font></b>  {name}{url_str}{meta_str}",
                styles["body"]
            ))

    story.append(PageBreak())

    # ── CONTENIDO DEL REPORTE ──────────────────────────────────────────────────
    content_story = _parse_markdown(report_markdown, styles)
    story.extend(content_story)

    # ── PÁGINA FINAL ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Spacer(1, 60*mm))
    story.append(_hr(YELLOW, 1))
    story.append(Spacer(1, 6))
    story.append(Paragraph("ATALAYA · MONITOR DE COMPETENCIA", styles["cover_eyebrow"]))
    story.append(Paragraph("AENIMA AGENCY · BOUND", styles["cover_sub"]))
    story.append(Paragraph(f"Generado el {scan_date}", styles["meta"]))

    # Build
    def make_canvas(filename, doc=None, **kwargs):
        return AtalayaCanvas(
            filename,
            pagesize=A4,
            client_name=client_name,
            scan_date=scan_date,
        )

    doc.build(story, canvasmaker=make_canvas)
    return buffer.getvalue()
