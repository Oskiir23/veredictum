"""Punto de entrada CLI de Veredictum.

Uso:
    python run.py ruta\\al\\correo.eml
"""

from __future__ import annotations

import sys

from veredictum.agent import analizar_correo
from veredictum.config import comprobar_clave


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python run.py <ruta_al_correo.eml>")
        raise SystemExit(1)

    comprobar_clave()

    ruta = sys.argv[1]
    print(f"[Veredictum] Analizando: {ruta}\n")
    resultado = analizar_correo(ruta)
    print("\n" + "=" * 70)
    print(resultado)
    print("=" * 70)


if __name__ == "__main__":
    main()
