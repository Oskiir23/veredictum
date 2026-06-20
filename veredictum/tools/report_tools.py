"""Generación del borrador de dictamen pericial con la plantilla real de Óscar.

El agente aporta la NARRATIVA; los HECHOS se toman del store de evidencia
(context). Se vuelca todo a JSON y un renderer Node (docx-js) produce el .docx
con el estilo exacto de la plantilla maestra.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from .. import context
from ..config import SALIDA, asegurar_directorios

_RENDERER = Path(__file__).resolve().parent.parent / "render" / "gen_dictamen.js"
# node_modules del proyecto (tras `npm install`) y, como respaldo, el global del usuario.
_PROJECT_NM = Path(__file__).resolve().parent.parent.parent / "node_modules"
_HOME_NM = Path.home() / "node_modules"
_NODE_PATH = os.pathsep.join(str(p) for p in (_PROJECT_NM, _HOME_NM))
_MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _fecha_es() -> str:
    n = datetime.now()
    return f"{n.day} de {_MESES[n.month]} de {n.year}"


def write_report(
    caso_id: str,
    veredicto: str,
    nivel_confianza: str,
    resumen: str,
    resumen_bullets: list[str],
    hallazgos: list[str],
    linea_temporal: list[str],
    conclusiones: list[str],
    incertidumbres: list[str],
    recomendaciones: list[str],
) -> str:
    """Genera el borrador de dictamen pericial en .docx (plantilla real) y devuelve la ruta.

    Aporta SOLO el razonamiento; los hechos (hashes, autenticación, IOCs, adjuntos)
    se toman automáticamente del análisis previo. Es un BORRADOR para validar.

    Args:
        caso_id: Identificador del caso (p. ej. SOC-2026-0132).
        veredicto: Clasificación ("Malicioso", "Sospechoso", "No concluyente", "Legítimo").
        nivel_confianza: Alto / Medio / Bajo.
        resumen: Párrafo de resumen ejecutivo con la conclusión principal.
        resumen_bullets: Puntos clave del resumen, en lenguaje comprensible.
        hallazgos: Hechos técnicos observados (sección de desarrollo).
        linea_temporal: Eventos en orden cronológico.
        conclusiones: Conclusiones numeradas (se rotulan PRIMERA, SEGUNDA, ...).
        incertidumbres: Puntos NO concluyentes que requieren validación del perito.
        recomendaciones: Acciones propuestas.
    """
    asegurar_directorios()

    datos = {
        "caso_id": caso_id,
        "fecha_emision": _fecha_es(),
        "correo": context.EVIDENCIA.get("correo", {}),
        "adjuntos": context.EVIDENCIA.get("adjuntos", []),
        "vt": context.EVIDENCIA.get("vt", {}),
        "comportamiento": context.EVIDENCIA.get("comportamiento", {}),
        "detonacion": context.EVIDENCIA.get("detonacion", {}),
        "iocs": context.EVIDENCIA.get("iocs", {}),
        "narrativa": {
            "veredicto": veredicto,
            "nivel_confianza": nivel_confianza,
            "resumen": resumen,
            "resumen_bullets": resumen_bullets,
            "hallazgos": hallazgos,
            "linea_temporal": linea_temporal,
            "conclusiones": conclusiones,
            "incertidumbres": incertidumbres,
            "recomendaciones": recomendaciones,
        },
    }

    seguro = caso_id.replace("/", "-").replace("\\", "-")
    json_path = SALIDA / f"datos_{seguro}.json"
    docx_path = SALIDA / f"dictamen_{seguro}.docx"
    json_path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    env = dict(os.environ)
    env["NODE_PATH"] = _NODE_PATH
    try:
        proc = subprocess.run(
            ["node", str(_RENDERER), str(json_path), str(docx_path)],
            capture_output=True, text=True, env=env, timeout=120,
        )
    except FileNotFoundError:
        return "ERROR: no se encontró 'node'. Instala Node.js para renderizar el dictamen."
    if proc.returncode != 0:
        return f"ERROR al renderizar el dictamen: {proc.stderr[:500]}"
    return str(docx_path)
