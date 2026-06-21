"""Verifica y parsea el CSV de Procmon del caso real."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum.detonacion import parse_procmon

CSV = Path(__file__).resolve().parent.parent / "transfer_vm" / "salida" / "procmon.csv"
if not CSV.exists():
    print("NO existe:", CSV)
    raise SystemExit(1)

print(f"CSV: {CSV.name}  {CSV.stat().st_size/1024/1024:.2f} MB")
r = parse_procmon(str(CSV), proceso="muestra.exe")
print("estado:", r["estado"], "| proceso:", r.get("proceso"))
if r["estado"] != "analizado":
    print(r.get("detalle"))
    raise SystemExit(0)
for k in ("procesos", "ficheros_escritos", "registro", "persistencia", "red"):
    vals = r.get(k, [])
    print(f"  {k}: {len(vals)}")
    for v in vals[:4]:
        print(f"      - {v[:90]}")
