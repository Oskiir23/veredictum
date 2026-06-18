"""Simula la VM: bloquea dotenv, docx y oletools y comprueba que extraer funciona
con Python pelado (stdlib). Ejecutar: python tests\\smoke_vm.py"""

import sys
from pathlib import Path

# Simula ausencia de dependencias (como en una Parrot live sin pip).
for mod in ("dotenv", "docx", "oletools", "oletools.olevba", "vt", "extract_msg"):
    sys.modules[mod] = None  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum.extractor import extraer  # noqa: E402

EML = Path(__file__).resolve().parent.parent / "veredictum" / "samples" / "demo.eml"
facts = extraer(str(EML))
print("correo.sha256:", facts["correo"]["sha256"][:16])
print("auth:", facts["correo"]["autenticacion"])
print("adjuntos:", [(a["nombre"], a.get("tipo_real"), a.get("macros")) for a in facts["adjuntos"]])
print("iocs.dominios:", facts["iocs"]["dominios"])
print("\nOK_VM (extractor corre sin dependencias)")
