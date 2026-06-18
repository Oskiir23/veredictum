"""Extracción forense OFFLINE — ejecutar DENTRO de la VM aislada (sin red).

Uso:
    python extraer.py <correo.eml> [evidencia.json]

Procesa el correo en estático y exporta SOLO hechos en texto. El adjunto (posible
malware) queda en cuarentena dentro de la VM; lo único que se transfiere al host
es el JSON de hechos.
"""

import sys

from veredictum.extractor import exportar


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python extraer.py <correo.eml> [evidencia.json]")
        raise SystemExit(1)

    eml = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "evidencia.json"
    print(f"[Veredictum/VM] Extrayendo en estático (offline): {eml}\n")
    ruta = exportar(eml, out)
    print(f"Hechos exportados a: {ruta}")
    print("Transfiere SOLO este JSON al host.")
    print("El binario permanece en cuarentena DENTRO de la VM y no debe salir.")


if __name__ == "__main__":
    main()
