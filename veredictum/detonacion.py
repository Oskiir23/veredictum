"""Ingesta de artefactos de detonación propia (laboratorio aislado).

Convierte la salida de herramientas de monitorización en hechos para el dictamen.
A diferencia del comportamiento de VirusTotal (sección 8.6), esto es la detonación
realizada por el perito en su propio entorno aislado.

v1: Process Monitor (Procmon) exportado a CSV — cubre procesos, ficheros,
registro y red en un único fichero.
"""

import csv as _csv
from pathlib import Path

# Operaciones de Procmon agrupadas por eje.
_OP_PROCESO = {"Process Create"}
_OP_FICHERO = {"WriteFile", "CreateFile", "SetRenameInformationFile"}
_OP_REGISTRO = {"RegSetValue", "RegCreateKey"}
_OP_RED = {"TCP Connect", "TCP Send", "UDP Send", "TCP Receive", "UDP Receive"}

# Rutas de registro típicas de persistencia.
_PERSISTENCIA = ("\\run", "\\runonce", "currentversion\\run", "\\winlogon", "\\services\\")


def _únicos(seq, n=30):
    vistos, out = set(), []
    for x in seq:
        if x and x not in vistos:
            vistos.add(x)
            out.append(x)
        if len(out) >= n:
            break
    return out


def parse_procmon(csv_path: str) -> dict:
    """Parsea un CSV de Process Monitor y resume el comportamiento observado.

    Args:
        csv_path: Ruta al CSV exportado desde Procmon.
    """
    ruta = Path(csv_path)
    if not ruta.exists():
        return {"estado": "sin_datos", "detalle": f"No existe: {csv_path}"}

    procesos, ficheros, registro, persistencia, red = [], [], [], [], []
    try:
        with ruta.open("r", encoding="utf-8-sig", newline="") as f:
            lector = _csv.DictReader(f)
            for fila in lector:
                op = (fila.get("Operation") or "").strip()
                path = (fila.get("Path") or "").strip()
                detail = (fila.get("Detail") or "").strip()
                proc = (fila.get("Process Name") or "").strip()
                res = (fila.get("Result") or "").strip().upper()
                if res and res != "SUCCESS":
                    continue
                if op in _OP_PROCESO:
                    procesos.append(f"{proc} -> {path}".strip(" ->"))
                elif op in _OP_FICHERO and op == "WriteFile":
                    ficheros.append(path)
                elif op in _OP_REGISTRO:
                    registro.append(path)
                    if any(p in path.lower() for p in _PERSISTENCIA):
                        persistencia.append(f"{path}  {('= ' + detail) if detail else ''}".strip())
                elif op in _OP_RED:
                    red.append(path)
    except Exception as e:  # noqa: BLE001
        return {"estado": "error", "detalle": str(e)[:200]}

    return {
        "estado": "analizado",
        "fuente": "Detonación propia en laboratorio aislado (Process Monitor)",
        "procesos": _únicos(procesos),
        "ficheros_escritos": _únicos(ficheros),
        "registro": _únicos(registro),
        "persistencia": _únicos(persistencia, 15),
        "red": _únicos(red),
    }
