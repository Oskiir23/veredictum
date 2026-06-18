#!/usr/bin/env bash
# Ejecutar DENTRO de la VM Kali (aislada, sin red), desde la carpeta compartida.
#
# Uso:  bash correr_en_vm.sh entrada/correo.eml
#
# La cuarentena del binario (posible malware) se queda en /tmp DENTRO de la VM y
# muere al revertir el snapshot. A la carpeta compartida solo sale evidencia.json.
set -e

EML="${1:?Uso: bash correr_en_vm.sh entrada/correo.eml}"

# La cuarentena vive en la VM, NO en la carpeta compartida.
export VEREDICTUM_SALIDA=/tmp/veredictum
mkdir -p "$VEREDICTUM_SALIDA"

python3 extraer.py "$EML" "salida/evidencia.json"

echo
echo "[OK] evidencia.json en la carpeta compartida (carpeta salida/)."
echo "El binario quedó en $VEREDICTUM_SALIDA (dentro de la VM)."
echo "Cópialo NUNCA al host. Al terminar, revierte el snapshot."
