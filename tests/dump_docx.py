"""Vuelca el texto del dictamen generado para revisarlo."""

import sys
from pathlib import Path

from docx import Document

ruta = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\seosc\Desktop\Claude\salida\dictamen_demo.eml.docx"
doc = Document(ruta)
for p in doc.paragraphs:
    if p.text.strip():
        estilo = p.style.name if p.style else ""
        marca = "•" if "List" in estilo else ("#" if "Heading" in estilo else " ")
        print(f"{marca} {p.text}")
