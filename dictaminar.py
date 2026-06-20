"""Dictamen en el HOST a partir de los hechos extraídos en la VM (modo split).

Uso:
    python dictaminar.py <evidencia.json> [caso_id] [--procmon <procmon.csv>]

Lee el JSON de hechos (texto saneado, sin binario), razona con el LLM, consulta
VirusTotal con los hashes y genera el borrador de dictamen .docx. Si se aporta un
CSV de Process Monitor (--procmon), incorpora el análisis dinámico de la detonación.
"""

import json
import sys
from pathlib import Path

from veredictum.agent import dictaminar_desde_hechos
from veredictum.config import comprobar_clave
from veredictum.detonacion import parse_procmon


def main() -> None:
    args = sys.argv[1:]
    procmon = None
    if "--procmon" in args:
        i = args.index("--procmon")
        procmon = args[i + 1] if i + 1 < len(args) else None
        del args[i : i + 2]

    if not args:
        print("Uso: python dictaminar.py <evidencia.json> [caso_id] [--procmon <procmon.csv>]")
        raise SystemExit(1)

    comprobar_clave()
    facts = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    caso = args[1] if len(args) > 1 else (facts.get("correo", {}).get("evidencia") or "CASO")

    detonacion = None
    if procmon:
        detonacion = parse_procmon(procmon)
        print(f"[detonación] Procmon: {detonacion.get('estado')} "
              f"(procesos={len(detonacion.get('procesos', []))}, "
              f"red={len(detonacion.get('red', []))})")

    print(f"[Veredictum/Host] Dictaminando caso: {caso}\n")
    resultado = dictaminar_desde_hechos(facts, caso, detonacion=detonacion)
    print("\n" + "=" * 70)
    print(resultado)
    print("=" * 70)


if __name__ == "__main__":
    main()
