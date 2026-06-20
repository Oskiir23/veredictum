"""Valida el escaneo YARA y su aparición en el dictamen (sin LLM)."""

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum import context
from veredictum.tools.attachment_tools import analyze_attachment
from veredictum.tools.report_tools import write_report

# Fichero de prueba que dispara varias reglas.
eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
payload = b"MZ\x90\x00 powershell -enc DownloadString " + eicar.encode()
tmp = Path(tempfile.gettempdir()) / "muestra_yara.bin"
tmp.write_bytes(payload)
sha = hashlib.sha256(payload).hexdigest()

context.reset()
context.EVIDENCIA["correo"] = {
    "evidencia": "test.eml", "tamano_bytes": 10, "sha256": "0" * 64, "md5": "0" * 32,
    "remitente": "a@b.c", "destinatario": "d@e.f", "asunto": "t", "fecha": "",
    "return_path": "", "message_id": "", "autenticacion": {"spf": "fail", "dkim": "none", "dmarc": "fail"},
}
context.EVIDENCIA["adjuntos"] = [{"nombre": "factura.exe", "sha256": sha, "tamano_bytes": len(payload), "ruta": str(tmp)}]

r = analyze_attachment(str(tmp))
print("YARA estado:", r["yara"]["estado"])
for c in r["yara"].get("coincidencias", []):
    print("  -", c["regla"], "|", c["descripcion"][:50])

ruta = write_report(
    caso_id="TEST-YARA", veredicto="Malicioso", nivel_confianza="Alto",
    resumen="Prueba YARA.", resumen_bullets=["x"], hallazgos=["x"],
    linea_temporal=["x"], conclusiones=["x"], incertidumbres=["x"], recomendaciones=["x"],
)
print("DOCX:", ruta)
tmp.unlink(missing_ok=True)
