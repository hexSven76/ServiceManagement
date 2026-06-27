from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def simple_pdf(path: str | Path, title: str, lines: list[str]) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 32
    c.setFont("Helvetica", 10)
    for line in lines:
        if y < 72:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 10)
        c.drawString(72, y, str(line)[:110])
        y -= 18
    c.save()
    return str(path)
