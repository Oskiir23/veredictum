"""Store de evidencia compartido entre herramientas dentro de un análisis.

Los HECHOS (hashes, autenticación, IOCs, datos de adjuntos) los rellenan los
tools desde sus salidas reales y el dictamen los toma de aquí — NO del LLM —,
de modo que no pueden ser alucinados. El agente solo aporta el razonamiento.
"""

EVIDENCIA: dict = {}


def reset() -> None:
    EVIDENCIA.clear()
    EVIDENCIA.update({"correo": {}, "iocs": {}, "adjuntos": [], "vt": {}})


reset()
