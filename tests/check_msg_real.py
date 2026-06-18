"""Valida _parse_msg con un .msg real (benigno)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum import context
from veredictum.tools.email_tools import parse_email

EJEMPLO = Path(__file__).resolve().parent.parent / "veredictum" / "samples" / "ejemplo.msg"
if not EJEMPLO.exists():
    print("Coloca un .msg benigno en veredictum/samples/ejemplo.msg para probar.")
    raise SystemExit(0)

context.reset()
r = parse_email(str(EJEMPLO))

if "error" in r:
    print("ERROR:", r["error"])
else:
    print("remitente:", (r["remitente"] or "(vacio)")[:60])
    print("asunto:", (r["asunto"] or "(vacio)")[:60])
    print("fecha:", r["fecha"])
    print("auth:", r["autenticacion"])
    print("cuerpo (50):", (r["cuerpo"] or "")[:50].replace("\n", " "))
    print("adjuntos:", [(a["nombre"], a["tamano_bytes"]) for a in r["adjuntos"]])
    print("store sha256:", context.EVIDENCIA["correo"]["sha256"][:16])
    print("OK_MSG")
