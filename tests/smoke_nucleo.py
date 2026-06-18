"""Prueba el núcleo forense sin gastar API. Ejecutar: python tests\\smoke_nucleo.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum.tools.email_tools import parse_email, extract_iocs
from veredictum.tools.attachment_tools import analyze_attachment, vt_lookup

EML = Path(__file__).resolve().parent.parent / "veredictum" / "samples" / "demo.eml"

p = parse_email(str(EML))
print("ASUNTO:", p["asunto"])
print("AUTENTICACION:", p["autenticacion"])
print("ADJUNTOS:", [a["nombre"] for a in p["adjuntos"]])

iocs = extract_iocs(p["cuerpo"])
print("URLs:", iocs["urls_defanged"])
print("DOMINIOS:", iocs["dominios"])

a = analyze_attachment(p["adjuntos"][0]["ruta"])
print("ADJUNTO tipo:", a["tipo_real"], "| sha256:", a["hashes"]["sha256"][:16])
print("VT:", vt_lookup(a["hashes"]["sha256"]))
print("\nOK_NUCLEO")
