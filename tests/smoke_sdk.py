"""Comprueba que el SDK de Gemini y la capa LLM importan y los símbolos existen.
No hace ninguna llamada de red ni gasta cuota. Ejecutar: python tests\\smoke_sdk.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types

assert hasattr(genai, "Client")
assert hasattr(types, "GenerateContentConfig")
assert hasattr(types, "AutomaticFunctionCallingConfig")

# Importa la capa propia (valida sintaxis de llm.py, agent.py, tools)
from veredictum.agent import SYSTEM, analizar_correo  # noqa: F401
from veredictum.tools import HERRAMIENTAS

print("HERRAMIENTAS:", [t.__name__ for t in HERRAMIENTAS])
print("SDK y capa LLM OK")
