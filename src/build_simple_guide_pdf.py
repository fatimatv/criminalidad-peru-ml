from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "defense" / "guia_simple_para_entender_el_proyecto.md"
OUTPUT = ROOT / "defense" / "guia_simple_para_entender_el_proyecto.pdf"


def clean_inline(text: str) -> str:
    return text.replace("**", "")


def parse_table(lines):
    rows = []
    for line in lines:
        rows.append([clean_inline(cell.strip()) for cell in line.strip().strip("|").split("|")])
    return rows


def build_pdf() -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "BodySimple",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=8,
        textColor=colors.HexColor("#111111"),
    )
    h1 = ParagraphStyle(
        "HeadingSimple1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.black,
    )
    h2 = ParagraphStyle(
        "HeadingSimple2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.black,
    )
    title = ParagraphStyle(
        "TitleSimple",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        alignment=0,
        textColor=colors.black,
        spaceAfter=10,
    )
    quote = ParagraphStyle(
        "QuoteSimple",
        parent=body,
        leftIndent=18,
        rightIndent=18,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1F4E79"),
    )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    story = [
        Paragraph("Guia simple para entender el proyecto", title),
        Paragraph(
            "Material de estudio para explicar el proyecto de criminalidad, seguridad ciudadana y Machine Learning sin necesidad de tener formacion en ingenieria.",
            body,
        ),
        Spacer(1, 8),
    ]

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx].rstrip()
        if not line:
            idx += 1
            continue
        if line.startswith("# "):
            idx += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(clean_inline(line[3:].strip()), h1))
        elif line.startswith("### "):
            story.append(Paragraph(clean_inline(line[4:].strip()), h2))
        elif line.startswith("| "):
            table_lines = []
            while idx < len(lines) and lines[idx].startswith("| "):
                table_lines.append(lines[idx])
                idx += 1
            idx -= 1
            rows = parse_table([table_lines[0], *table_lines[2:]])
            table = Table(rows, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
                        ("LEADING", (0, 0), (-1, -1), 11),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 8))
        elif line.startswith("- "):
            story.append(Paragraph("• " + clean_inline(line[2:].strip()), body))
        elif len(line) > 2 and line[0].isdigit() and ". " in line[:4]:
            story.append(Paragraph(clean_inline(line.strip()), body))
        elif line.startswith('"') and line.endswith('"'):
            story.append(Paragraph(clean_inline(line), quote))
        else:
            story.append(Paragraph(clean_inline(line), body))
        idx += 1

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
    print(OUTPUT)
