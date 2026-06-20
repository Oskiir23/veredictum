"""Configuración central: claves, modelo y rutas de trabajo."""

from __future__ import annotations

import os
from pathlib import Path

try:  # dotenv es opcional: la VM aislada corre sin él (solo stdlib).
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
VT_API_KEY = os.getenv("VT_API_KEY", "").strip()
MODEL = os.getenv("VEREDICTUM_MODEL", "gemini-2.5-flash").strip()

# Carpeta de trabajo aislada. Aquí se escribe el dictamen.
# Regla forense: el malware nunca se ejecuta; solo análisis estático sobre copia.
SALIDA = Path(os.getenv("VEREDICTUM_SALIDA", "salida")).resolve()

# Cuarentena de muestras. Los adjuntos se escriben aquí con sufijo .quarantine
# (no ejecutable, no doble-clicable) para evitar ejecución accidental.
CUARENTENA = SALIDA / "cuarentena"
SUFIJO_CUARENTENA = ".quarantine"

# Carpeta de reglas YARA (.yar/.yara). Override con VEREDICTUM_YARA_RULES.
RULES_DIR = Path(
    os.getenv("VEREDICTUM_YARA_RULES", str(Path(__file__).resolve().parent / "rules"))
)


def asegurar_directorios() -> None:
    CUARENTENA.mkdir(parents=True, exist_ok=True)


def comprobar_clave() -> None:
    if not GEMINI_API_KEY:
        raise SystemExit(
            "Falta GEMINI_API_KEY. Copia .env.example a .env y pega tu clave "
            "gratuita de https://aistudio.google.com/app/apikey"
        )
