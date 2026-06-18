"""Dictamen en el HOST a partir de los hechos extraídos en la VM (modo split).

Uso:
    python dictaminar.py <evidencia.json> [caso_id]

Lee el JSON de hechos (texto saneado, sin binario), razona con el LLM, consulta
VirusTotal con los hashes y genera el borrador de dictamen .docx.
"""

import json
import sys
from pathlib import Path

from veredictum.agent import dictaminar_desde_hechos
from veredictum.config import comprobar_clave


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python dictaminar.py <evidencia.json> [caso_id]")
        raise SystemExit(1)

    comprobar_clave()
    facts = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    caso = sys.argv[2] if len(sys.argv) > 2 else (
        facts.get("correo", {}).get("evidencia") or "CASO"
    )
    print(f"[Veredictum/Host] Dictaminando caso: {caso}\n")
    resultado = dictaminar_desde_hechos(facts, caso)
    print("\n" + "=" * 70)
    print(resultado)
    print("=" * 70)


if __name__ == "__main__":
    main()
