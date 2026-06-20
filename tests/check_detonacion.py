"""Valida el parser de detonación (Procmon) y su sección en el dictamen, sin LLM."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum import context
from veredictum.detonacion import parse_procmon
from veredictum.tools.report_tools import write_report

det = parse_procmon(str(Path(__file__).resolve().parent / "procmon_ejemplo.csv"))
print("estado:", det["estado"])
print("procesos:", det["procesos"])
print("ficheros:", det["ficheros_escritos"])
print("persistencia:", det["persistencia"])
print("red:", det["red"])

context.reset()
context.EVIDENCIA["correo"] = {
    "evidencia": "x.eml", "tamano_bytes": 1, "sha256": "0" * 64, "md5": "0" * 32,
    "remitente": "", "destinatario": "", "asunto": "", "fecha": "",
    "return_path": "", "message_id": "", "autenticacion": {"spf": "fail", "dkim": "none", "dmarc": "fail"},
}
context.EVIDENCIA["detonacion"] = det

ruta = write_report(
    caso_id="TEST-DET", veredicto="Malicioso", nivel_confianza="Alto",
    resumen="x", resumen_bullets=["x"], hallazgos=["x"], linea_temporal=["x"],
    conclusiones=["x"], incertidumbres=["x"], recomendaciones=["x"],
)
print("DOCX:", ruta)
