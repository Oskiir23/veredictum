"""Llamada mínima a Gemini para validar la clave. Ejecutar: python tests\\smoke_api.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai

from veredictum.config import GEMINI_API_KEY, MODEL, comprobar_clave

comprobar_clave()
cliente = genai.Client(api_key=GEMINI_API_KEY)
resp = cliente.models.generate_content(
    model=MODEL, contents="Responde solo con la palabra: OK"
)
print("MODELO:", MODEL)
print("RESPUESTA:", (resp.text or "").strip())
