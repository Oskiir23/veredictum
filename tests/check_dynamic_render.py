"""Valida la sección de comportamiento dinámico en el .docx, sin usar el LLM."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum import context
from veredictum.tools.attachment_tools import vt_behaviour
from veredictum.tools.report_tools import write_report

facts = json.loads(
    (Path(__file__).resolve().parent.parent / "transfer_vm" / "salida" / "evidencia.json").read_text(encoding="utf-8")
)
context.reset()
context.EVIDENCIA.update(facts)

for adj in context.EVIDENCIA.get("adjuntos", []):
    r = vt_behaviour(adj["sha256"])
    print(f"vt_behaviour({adj['nombre']}): {r['estado']}",
          f"| procesos={len(r.get('procesos', []))} mitre={len(r.get('mitre', []))}" if r["estado"] == "consultado" else "")

ruta = write_report(
    caso_id="TEST-DYN",
    veredicto="Malicioso",
    nivel_confianza="Alto",
    resumen="Prueba de render dinámico.",
    resumen_bullets=["Adjunto ejecutable con comportamiento malicioso."],
    hallazgos=["PE disfrazado de .zip."],
    linea_temporal=["Recepción del correo."],
    conclusiones=["El correo es malicioso."],
    incertidumbres=["Pendiente validación pericial."],
    recomendaciones=["Bloquear IOCs."],
)
print("DOCX:", ruta)
