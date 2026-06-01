from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from ..config import PDF_OUTPUT_DIR


def _build_table(data: Sequence[Sequence[object]]) -> Table:
    table = Table([[str(cell) for cell in row] for row in data], repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    table.setStyle(style)
    return table


def generate_pdf(filename: str, title: str, subtitle: str, table_headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    PDF_OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = PDF_OUTPUT_DIR / filename
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 8), Paragraph(subtitle, styles["Normal"]), Spacer(1, 12)]
    data = [list(table_headers)] + [list(row) for row in rows]
    story.append(_build_table(data))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated at: {datetime.utcnow().isoformat(sep=' ', timespec='seconds')} UTC", styles["Italic"]))
    doc.build(story)
    return str(output_path)
