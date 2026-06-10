"""
Atalaya · PDF Report Generator
Paleta: fondo blanco, texto negro/gris, acento amarillo #FFFF00
Header: línea fina amarilla + texto negro sobre blanco, elegante
"""
import re
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak
)
from reportlab.pdfgen import canvas as rl_canvas

# ── Colores ────────────────────────────────────────────────────────────────────
BLACK    = colors.HexColor("#111111")
YELLOW   = colors.HexColor("#FFFF00")
WHITE    = colors.HexColor("#FFFFFF")
GRAY     = colors.HexColor("#888888")
LGRAY    = colors.HexColor("#cccccc")
DGRAY    = colors.HexColor("#333333")
OFFWHITE = colors.HexColor("#f7f7f7")
YELLOW_BG= colors.HexColor("#FFFDE6")  # amarillo muy suave para filas alternas

W, H = A4  # 595 x 842 pts


# ── Canvas: header y footer refinados ─────────────────────────────────────────
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

        # Fondo blanco total
        self.setFillColor(WHITE)
        self.rect(0, 0, W, H, fill=1, stroke=0)

        # ── HEADER ──
        # Línea amarilla gruesa en el tope
        self.setFillColor(YELLOW)
        self.rect(0, H - 3*mm, W, 3*mm, fill=1, stroke=0)

        # Línea gris muy fina debajo del área de header
        self.setStrokeColor(LGRAY)
        self.setLineWidth(0.4)
        self.line(15*mm, H - 14*mm, W - 15*mm, H - 14*mm)

        # ATALAYA — texto negro, bold
        self.setFillColor(BLACK)
        self.setFont("Helvetica-Bold", 7)
        self.drawString(15*mm, H - 10*mm, "ATALAYA")

        # Separador puntito
        self.setFillColor(GRAY)
        self.setFont("Helvetica", 7)
        self.drawString(15*mm + 28, H - 10*mm, "·  MONITOR DE COMPETENCIA")

        # Cliente — derecha, gris
        self.setFillColor(GRAY)
        self.setFont("Helvetica", 6.5)
        self.drawRightString(W - 15*mm, H - 10*mm, self.client_name.upper())

        # ── FOOTER ──
        self.setStrokeColor(LGRAY)
        self.setLineWidth(0.4)
        self.line(15*mm, 13*mm, W - 15*mm, 13*mm)

        # Línea amarilla mini en el fondo
        self.setFillColor(YELLOW)
        self.rect(0, 0, W, 2*mm, fill=1, stroke=0)

        self.setFillColor(GRAY)
        self.setFont("Helvetica", 6)
        self.drawString(15*mm, 9*mm, f"AENIMA · BOUND  ·  {self.scan_date}")
        self.drawRightString(W - 15*mm, 9*mm, f"{page_num:02d} / {total:02d}")

        self.restoreState()


# ── Estilos de texto ───────────────────────────────────────────────────────────
def _make_styles():
    cover_eyebrow = ParagraphStyle("cover_eyebrow",
        fontName="Helvetica", fontSize=7.5, textColor=GRAY,
        spaceAfter=3, leading=11, letterSpacing=1.5)

    cover_title = ParagraphStyle("cover_title",
        fontName="Helvetica-Bold", fontSize=42, textColor=BLACK,
        spaceAfter=2, leading=46)

    cover_sub = ParagraphStyle("cover_sub",
        fontName="Helvetica", fontSize=10, textColor=GRAY,
        spaceAfter=4, leading=14)

    section_label = ParagraphStyle("section_label",
        fontName="Helvetica-Bold", fontSize=6.5, textColor=GRAY,
        spaceAfter=2, leading=9, letterSpacing=1.5)

    h1 = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=17, textColor=BLACK,
        spaceBefore=10, spaceAfter=5, leading=21)

    h2 = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=11, textColor=DGRAY,
        spaceBefore=12, spaceAfter=3, leading=15)

    h3 = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=9.5, textColor=BLACK,
        spaceBefore=6, spaceAfter=3, leading=13)

    body = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9, textColor=DGRAY,
        spaceAfter=4, leading=14)

    bullet = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=9, textColor=DGRAY,
        spaceAfter=3, leading=14, leftIndent=12)

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


def _hr(color=LGRAY, thickness=0.4):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=5, spaceBefore=3)

def _hr_accent():
    """Línea amarilla de 30mm — acento decorativo bajo secciones"""
    return HRFlowable(width=30*mm, thickness=2.5, color=YELLOW,
                      spaceAfter=6, spaceBefore=2)


# ── Parser de Markdown → flowables ────────────────────────────────────────────
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

        # H1 — título del reporte
        if line.startswith("# "):
            text = line[2:].strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(text.upper(), styles["h1"]))
            story.append(_hr_accent())
            i += 1
            continue

        # H2 — secciones principales
        if line.startswith("## "):
            text = line[3:].strip()
            story.append(Spacer(1, 6))
            story.append(Paragraph(text.upper(), styles["h2"]))
            story.append(_hr())
            i += 1
            continue

        # H3 — nombre de competidor: caja con borde izquierdo amarillo
        if line.startswith("### "):
            text = line[4:].strip()
            story.append(Spacer(1, 5))
            comp_data = [[Paragraph(text.upper(), ParagraphStyle(
                "comp_h",
                fontName="Helvetica-Bold", fontSize=9,
                textColor=BLACK, leading=13
            ))]]
            comp_table = Table(comp_data, colWidths=[170*mm])
            comp_table.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), OFFWHITE),
                ("TOPPADDING",    (0,0), (-1,-1), 7),
                ("BOTTOMPADDING", (0,0), (-1,-1), 7),
                ("LEFTPADDING",   (0,0), (-1,-1), 10),
                ("RIGHTPADDING",  (0,0), (-1,-1), 8),
                ("LINEBEFORE",    (0,0), (0,-1),  3, YELLOW),
                ("LINEBELOW",     (0,0), (-1,-1), 0.3, LGRAY),
            ]))
            story.append(comp_table)
            story.append(Spacer(1, 3))
            i += 1
            continue

        # Bullet con bold label — "- **Label:** texto"
        if line.startswith("- **") and ":**" in line:
            match = re.match(r"- \*\*(.+?):\*\*\s*(.*)", line)
            if match:
                label = match.group(1)
                rest  = match.group(2)
                rest_clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", rest)
                story.append(Paragraph(
                    f"<b>{label}:</b> <font color='#555555'>{rest_clean}</font>",
                    styles["bullet"]
                ))
                i += 1
                continue

        # Bullet normal
        if line.startswith("- ") or line.startswith("* "):
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line[2:].strip())
            story.append(Paragraph(f"· {text}", styles["bullet"]))
            i += 1
            continue

        # Bold standalone
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            story.append(Paragraph(line[2:-2], styles["bold_label"]))
            i += 1
            continue

        # Línea normal con bold inline
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        story.append(Paragraph(text, styles["body"]))
        i += 1

    return story


# ── Función principal ──────────────────────────────────────────────────────────
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

    buffer  = io.BytesIO()
    styles  = _make_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,    # el header ocupa ~14mm, dejamos 20 de margen
        bottomMargin=20*mm,
        title=f"Atalaya · {client_name}",
        author="Aenima Agency",
    )

    story = []

    # ── PORTADA ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 28*mm))

    # Acento amarillo
    banda = Table([[""]], colWidths=[170*mm], rowHeights=[4])
    banda.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), YELLOW)]))
    story.append(banda)
    story.append(Spacer(1, 10*mm))

    story.append(Paragraph("AENIMA · INTELIGENCIA COMPETITIVA", styles["cover_eyebrow"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph("ATALAYA", styles["cover_title"]))
    story.append(Paragraph("MONITOR DE COMPETENCIA", styles["cover_sub"]))
    story.append(Spacer(1, 10*mm))
    story.append(_hr())
    story.append(Spacer(1, 5))

    # Tabla de metadata
    info_rows = [
        [Paragraph("CLIENTE",      styles["section_label"]),
         Paragraph(client_name.upper(), styles["bold_label"])],
        [Paragraph("FECHA",        styles["section_label"]),
         Paragraph(scan_date,          styles["body"])],
        [Paragraph("COMPETIDORES", styles["section_label"]),
         Paragraph(str(len(competitors)), styles["body"])],
        [Paragraph("MODELO",       styles["section_label"]),
         Paragraph("LLAMA 3.3 · 70B · GROQ", styles["body"])],
    ]
    info_table = Table(info_rows, colWidths=[38*mm, 132*mm])
    info_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, OFFWHITE]),
        ("TOPPADDING",     (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 6),
        ("LEFTPADDING",    (0,0), (-1,-1), 4),
        ("RIGHTPADDING",   (0,0), (-1,-1), 4),
        ("LINEBELOW",      (0,0), (-1,-1), 0.3, LGRAY),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    # Competidores en portada
    if competitors:
        story.append(Paragraph("COMPETIDORES ANALIZADOS", styles["section_label"]))
        story.append(Spacer(1, 4))
        for idx, comp in enumerate(competitors):
            name = comp.get("name", "").upper()
            url  = comp.get("url", "")
            fb   = comp.get("facebook_page", "")
            parts = []
            if url: parts.append(url)
            if fb:  parts.append(f"FB: {fb}")
            detail = "  ·  ".join(parts)
            story.append(Paragraph(
                f"<b><font color='#111111'>{idx+1:02d}  {name}</font></b>"
                + (f"  <font color='#aaaaaa'>{detail}</font>" if detail else ""),
                styles["body"]
            ))

    story.append(PageBreak())

    # ── CONTENIDO ──────────────────────────────────────────────────────────────
    story.extend(_parse_markdown(report_markdown, styles))

    # ── PÁGINA FINAL ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Spacer(1, 65*mm))

    banda2 = Table([[""]], colWidths=[170*mm], rowHeights=[4])
    banda2.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), YELLOW)]))
    story.append(banda2)
    story.append(Spacer(1, 8))
    story.append(Paragraph("ATALAYA · MONITOR DE COMPETENCIA", styles["cover_eyebrow"]))
    story.append(Paragraph("AENIMA AGENCY · BOUND", styles["cover_sub"]))
    story.append(Paragraph(f"Generado el {scan_date}", styles["meta"]))

    def make_canvas(filename, doc=None, **kwargs):
        return AtalayaCanvas(
            filename, pagesize=A4,
            client_name=client_name,
            scan_date=scan_date,
        )

    doc.build(story, canvasmaker=make_canvas)
    return buffer.getvalue()