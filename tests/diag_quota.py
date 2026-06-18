"""Muestra el detalle del error 429 para saber si es límite por minuto o por día."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai.errors import ClientError

from veredictum.config import GEMINI_API_KEY

cliente = genai.Client(api_key=GEMINI_API_KEY)
for modelo in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]:
    try:
        r = cliente.models.generate_content(model=modelo, contents="di OK")
        print(f"{modelo}: OK -> {(r.text or '').strip()[:20]}")
    except ClientError as e:
        msg = str(e)
        # Busca pistas de tipo de límite
        tipo = "POR DÍA (RPD)" if "PerDay" in msg or "per day" in msg.lower() else "POR MINUTO (RPM)" if "PerMinute" in msg or "per minute" in msg.lower() else "?"
        print(f"{modelo}: 429 [{tipo}] {msg[:160]}")
    except Exception as e:  # noqa: BLE001
        print(f"{modelo}: {type(e).__name__} {str(e)[:120]}")
