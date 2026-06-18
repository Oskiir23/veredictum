"""Prepara la carpeta transfer_vm/ para compartir con la VM aislada.

Copia el extractor (paquete veredictum + extraer.py + requirements-vm.txt) a
transfer_vm/ y crea entrada/ y salida/. NO copia el .env (las claves nunca entran
en la VM). Ejecuta esto una vez antes de compartir la carpeta con VirtualBox:

    python preparar_transfer.py
"""

import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DST = RAIZ / "transfer_vm"


def main() -> None:
    (DST / "entrada").mkdir(parents=True, exist_ok=True)
    (DST / "salida").mkdir(parents=True, exist_ok=True)

    # Paquete del extractor (sin .env: el paquete no lo contiene).
    destino_pkg = DST / "veredictum"
    if destino_pkg.exists():
        shutil.rmtree(destino_pkg)
    shutil.copytree(
        RAIZ / "veredictum",
        destino_pkg,
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    for f in ("extraer.py", "requirements-vm.txt"):
        shutil.copy2(RAIZ / f, DST / f)

    # Por seguridad: aborta si se cuela un .env.
    fugas = list(DST.rglob(".env"))
    if fugas:
        raise SystemExit(f"PELIGRO: .env detectado en transfer_vm: {fugas}")

    print(f"transfer_vm/ preparado en: {DST}")
    print("Comparte ESTA carpeta con la VM (automontaje). Pon el .eml en entrada/.")


if __name__ == "__main__":
    main()
