"""Valida el enrutado .eml/.msg de parse_email (sin necesitar un .msg real válido)."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum import context
from veredictum.tools.email_tools import parse_email

RAIZ = Path(__file__).resolve().parent.parent

# 1) .eml real sigue funcionando
context.reset()
r = parse_email(str(RAIZ / "veredictum" / "samples" / "demo.eml"))
print(".eml ->", "OK" if r.get("asunto") else f"FALLO: {r}")

# 2) un .msg corrupto (no OLE) debe devolver error limpio, no reventar
tmp = Path(tempfile.gettempdir()) / "fake.msg"
tmp.write_bytes(b"esto no es un .msg valido")
context.reset()
r = parse_email(str(tmp))
print(".msg corrupto ->", "error limpio OK" if "error" in r else f"INESPERADO: {r}")
print("   detalle:", r.get("error", "")[:60])
tmp.unlink(missing_ok=True)
