"""Capa LLM aislada. Hoy: Gemini (free). Mañana: cambia aquí a Ollama local.

Todo el resto del proyecto llama a `run_agent(...)` sin saber qué motor hay
debajo. Para pasar a un modelo local y privado (la evidencia no sale del equipo),
solo hay que reimplementar esta función con el cliente de Ollama — el agente y
las herramientas no cambian.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from .config import GEMINI_API_KEY, MODEL

# Si el modelo principal está saturado, se prueba el siguiente.
_FALLBACKS = ["gemini-2.5-flash-lite"]


def run_agent(system_instruction: str, user_prompt: str, tools: list[Callable]) -> str:
    """Lanza el bucle agéntico: el modelo invoca las herramientas hasta concluir.

    Gemini ejecuta automáticamente las funciones Python que decide llamar
    (function calling). Reintenta con backoff ante saturación (503/429) y, si
    persiste, cae a un modelo de respaldo.
    """
    cliente = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools,
        temperature=0.2,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=12
        ),
    )

    for modelo in [MODEL, *_FALLBACKS]:
        for intento in range(3):
            try:
                resp = cliente.models.generate_content(
                    model=modelo, contents=user_prompt, config=config
                )
                return resp.text or "(el agente no devolvió texto)"
            except ServerError as e:  # 503/500: saturación temporal
                espera = 4 * (intento + 1)
                print(f"[{modelo}] saturado ({e.code}); reintento en {espera}s...")
                time.sleep(espera)
            except ClientError as e:  # 429: límite de cuota
                if e.code == 429:
                    print(f"[{modelo}] límite por minuto; espero 30s...")
                    time.sleep(30)
                else:
                    raise
        print(f"[{modelo}] no disponible; probando modelo de respaldo...")

    raise SystemExit("Todos los modelos de Gemini están saturados. Reintenta en unos minutos.")
