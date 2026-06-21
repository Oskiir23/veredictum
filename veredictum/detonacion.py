"""Ingesta de artefactos de detonación propia (laboratorio aislado).

Convierte la salida de herramientas de monitorización en hechos para el dictamen.
A diferencia del comportamiento de VirusTotal (sección 8.6), esto es la detonación
realizada por el perito en su propio entorno aislado.

v1: Process Monitor (Procmon) exportado a CSV — cubre procesos, ficheros,
registro y red en un único fichero. Si se indica `proceso`, filtra al árbol de
procesos de la muestra (la muestra y los procesos que crea), descartando el ruido
del sistema.
"""

import csv as _csv
import re
from pathlib import Path

# Operaciones de Procmon agrupadas por eje.
_OP_PROCESO = {"Process Create"}
_OP_FICHERO = {"WriteFile"}
_OP_REGISTRO = {"RegSetValue", "RegCreateKey"}
_OP_RED = {"TCP Connect", "TCP Send", "UDP Send", "TCP Receive", "UDP Receive"}

# Rutas de registro típicas de persistencia.
_PERSISTENCIA = ("\\run", "\\runonce", "currentversion\\run", "\\winlogon", "\\services\\")

_RE_CHILD_PID = re.compile(r"PID:\s*(\d+)")


def _unicos(seq, n=40):
    vistos, out = [], []
    for x in seq:
        if x and x not in vistos:
            vistos.append(x)
            out.append(x)
        if len(out) >= n:
            break
    return out


def _arbol_pids(ruta: Path, objetivo: str) -> set:
    """Primera pasada: PIDs de la muestra y de los procesos que crea (recursivo)."""
    objetivo_pids, creaciones = set(), []
    with ruta.open("r", encoding="utf-8-sig", newline="") as f:
        for fila in _csv.DictReader(f):
            proc = (fila.get("Process Name") or "").strip().lower()
            pid = (fila.get("PID") or "").strip()
            if pid and proc == objetivo:
                objetivo_pids.add(pid)
            if (fila.get("Operation") or "").strip() == "Process Create":
                m = _RE_CHILD_PID.search(fila.get("Detail") or "")
                if m and pid:
                    creaciones.append((pid, m.group(1)))
    arbol = set(objetivo_pids)
    cambio = True
    while cambio:
        cambio = False
        for padre, hijo in creaciones:
            if padre in arbol and hijo not in arbol:
                arbol.add(hijo)
                cambio = True
    return arbol


def parse_procmon(csv_path: str, proceso: str | None = None) -> dict:
    """Parsea un CSV de Process Monitor y resume el comportamiento observado.

    Args:
        csv_path: Ruta al CSV exportado desde Procmon.
        proceso: Nombre de la muestra (p. ej. "muestra.exe"). Si se indica, filtra
            al árbol de procesos de la muestra; si no, procesa todos los eventos.
    """
    ruta = Path(csv_path)
    if not ruta.exists():
        return {"estado": "sin_datos", "detalle": f"No existe: {csv_path}"}

    objetivo = (proceso or "").strip().lower()
    pids = None
    try:
        if objetivo:
            pids = _arbol_pids(ruta, objetivo)
            if not pids:
                return {"estado": "sin_actividad",
                        "detalle": f"No se observó el proceso '{proceso}' en el CSV."}

        procesos, ficheros, registro, persistencia, red = [], [], [], [], []
        with ruta.open("r", encoding="utf-8-sig", newline="") as f:
            for fila in _csv.DictReader(f):
                pid = (fila.get("PID") or "").strip()
                if pids is not None and pid not in pids:
                    continue
                op = (fila.get("Operation") or "").strip()
                path = (fila.get("Path") or "").strip()
                detail = (fila.get("Detail") or "").strip()
                proc = (fila.get("Process Name") or "").strip()
                res = (fila.get("Result") or "").strip().upper()

                if op in _OP_PROCESO:
                    procesos.append(f"{proc} -> {path}".strip(" ->"))
                elif op in _OP_FICHERO and res == "SUCCESS":
                    ficheros.append(path)
                elif op in _OP_REGISTRO and res == "SUCCESS":
                    registro.append(path)
                    if any(p in path.lower() for p in _PERSISTENCIA):
                        persistencia.append(f"{path}{('  = ' + detail) if detail else ''}")
                elif op in _OP_RED:
                    # Se incluye aunque falle: un intento de C2 con la red cortada es evidencia.
                    red.append(path)
    except Exception as e:  # noqa: BLE001
        return {"estado": "error", "detalle": str(e)[:200]}

    return {
        "estado": "analizado",
        "fuente": "Detonación propia en laboratorio aislado (Process Monitor)",
        "proceso": proceso or "(todos)",
        "procesos": _unicos(procesos),
        "ficheros_escritos": _unicos(ficheros),
        "registro": _unicos(registro),
        "persistencia": _unicos(persistencia, 15),
        "red": _unicos(red),
    }
