from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

FONT_REGISTERED = False


def _register_fonts():
    global FONT_REGISTERED
    if FONT_REGISTERED:
        return
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont("MainFont", path))
                FONT_REGISTERED = True
                return
    except Exception:
        pass


def generate_analysis_pdf(document_name: str, analysis: dict) -> BytesIO:
    _register_fonts()
    font_name = "MainFont" if FONT_REGISTERED else "Helvetica"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleTR", parent=styles["Title"], fontName=font_name, fontSize=18, textColor=HexColor("#4f46e5"))
    heading_style = ParagraphStyle("HeadingTR", parent=styles["Heading2"], fontName=font_name, fontSize=13, textColor=HexColor("#1f2937"), spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("BodyTR", parent=styles["Normal"], fontName=font_name, fontSize=10, leading=15, textColor=HexColor("#374151"))
    meta_style = ParagraphStyle("MetaTR", parent=styles["Normal"], fontName=font_name, fontSize=9, textColor=HexColor("#9ca3af"))

    elements = []

    elements.append(Paragraph("PDF Reader AI - Analiz Raporu", title_style))
    elements.append(Paragraph(document_name, meta_style))
    elements.append(Spacer(1, 16))

    if analysis.get("summary"):
        elements.append(Paragraph("Özet", heading_style))
        elements.append(Paragraph(analysis["summary"], body_style))

    if analysis.get("importantPoints"):
        elements.append(Paragraph("Önemli Noktalar", heading_style))
        items = [ListItem(Paragraph(p, body_style)) for p in analysis["importantPoints"]]
        elements.append(ListFlowable(items, bulletType="bullet"))

    if analysis.get("keywords"):
        elements.append(Paragraph("Anahtar Kelimeler", heading_style))
        elements.append(Paragraph(", ".join(analysis["keywords"]), body_style))

    sensitive = analysis.get("sensitiveFindings", [])
    elements.append(Paragraph("Hassas Veri Tespiti", heading_style))
    if not sensitive:
        elements.append(Paragraph("Hassas veri tespit edilmedi.", body_style))
    else:
        for f in sensitive:
            elements.append(Paragraph(f"{f.get('type', '')}: {f.get('count', 0)} adet", body_style))

    specific = analysis.get("documentSpecificAnalysis", {})
    doc_type = analysis.get("documentType", "general")

    if doc_type == "cv" and specific:
        if specific.get("strongSides"):
            elements.append(Paragraph("Güçlü Yönler", heading_style))
            items = [ListItem(Paragraph(p, body_style)) for p in specific["strongSides"]]
            elements.append(ListFlowable(items, bulletType="bullet"))
        if specific.get("technicalSkills"):
            elements.append(Paragraph("Teknik Beceriler", heading_style))
            elements.append(Paragraph(", ".join(specific["technicalSkills"]), body_style))
        if specific.get("improvementSuggestions"):
            elements.append(Paragraph("Öneriler", heading_style))
            items = [ListItem(Paragraph(p, body_style)) for p in specific["improvementSuggestions"]]
            elements.append(ListFlowable(items, bulletType="bullet"))
        if specific.get("careerAdvice"):
            elements.append(Paragraph("Kariyer Tavsiyesi", heading_style))
            elements.append(Paragraph(specific["careerAdvice"], body_style))

    elif doc_type == "lecture_note" and specific:
        if specific.get("examFocusedNotes"):
            elements.append(Paragraph("Sınav Notları", heading_style))
            items = [ListItem(Paragraph(p, body_style)) for p in specific["examFocusedNotes"]]
            elements.append(ListFlowable(items, bulletType="bullet"))
        if specific.get("studySuggestions"):
            elements.append(Paragraph("Çalışma Önerileri", heading_style))
            items = [ListItem(Paragraph(p, body_style)) for p in specific["studySuggestions"]]
            elements.append(ListFlowable(items, bulletType="bullet"))

    doc.build(elements)
    buffer.seek(0)
    return buffer
