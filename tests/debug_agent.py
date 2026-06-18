"""Depura: muestra qué argumentos pasa Gemini a las tools y qué devuelven."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types

from veredictum.config import GEMINI_API_KEY, MODEL
from veredictum.agent import SYSTEM
from veredictum.tools import HERRAMIENTAS

EML = Path(__file__).resolve().parent.parent / "veredictum" / "samples" / "demo.eml"

cliente = genai.Client(api_key=GEMINI_API_KEY)
config = types.GenerateContentConfig(
    system_instruction=SYSTEM,
    tools=HERRAMIENTAS,
    temperature=0.2,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=12),
)
resp = cliente.models.generate_content(
    model=MODEL,
    contents=f"Analiza el correo en: {EML}\nUsa caso_id = demo.",
    config=config,
)

print("=== HISTORIAL FUNCTION CALLING ===")
for c in (resp.automatic_function_calling_history or []):
    for part in (c.parts or []):
        if part.function_call:
            print(f"\n[LLAMADA] {part.function_call.name}({dict(part.function_call.args)})")
        if part.function_response:
            r = part.function_response.response
            print(f"[RESPUESTA] {str(r)[:300]}")

print("\n=== TEXTO FINAL ===")
print(resp.text)
