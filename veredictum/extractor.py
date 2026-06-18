"""Extracción forense OFFLINE — pensada para correr dentro de la VM aislada.

NO usa el LLM ni internet. Procesa el .eml con las herramientas estáticas y
exporta SOLO hechos en texto (cabeceras, autenticación, hashes, salida de
olevba, IOCs). El binario malicioso queda en cuarentena DENTRO de la VM y
nunca se incluye en la exportación: lo único que cruza al host es texto saneado.
"""

import json
from pathlib import Path

from . import context
from .tools.attachment_tools import analyze_attachment
from .tools.email_tools import extract_iocs, parse_email


def extraer(ruta_eml: str) -> dict:
    """Analiza el correo en estático y devuelve el diccionario de HECHOS.

    No consulta VirusTotal (requeriría red): eso se hace en el host con el hash.
    """
    context.reset()
    correo = parse_email(ruta_eml)
    if "error" in correo:
        raise SystemExit(f"No se pudo parsear el correo: {correo['error']}")

    # IOCs del cuerpo (y del campo Received, que delata la infraestructura).
    extract_iocs(correo.get("cuerpo", ""))
    extract_iocs(" ".join(correo.get("received", [])))

    # Análisis estático de cada adjunto desde la cuarentena local.
    for adj in correo.get("adjuntos", []):
        analyze_attachment(adj["ruta"])

    facts = json.loads(json.dumps(context.EVIDENCIA))  # copia profunda
    # El binario NO cruza: se eliminan las rutas locales de cuarentena.
    for adj in facts.get("adjuntos", []):
        adj.pop("ruta", None)
    return facts


def exportar(ruta_eml: str, salida_json: str) -> str:
    """Extrae y vuelca los hechos a un JSON listo para transferir al host."""
    facts = extraer(ruta_eml)
    destino = Path(salida_json).resolve()
    destino.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(destino)
