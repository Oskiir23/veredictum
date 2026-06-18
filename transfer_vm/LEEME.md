# Carpeta de transferencia VM ↔ host

Esta es la **única** carpeta que se comparte con la VM aislada. NO contiene el
`.env` ni la API key: solo el extractor y las carpetas de intercambio.

## Contenido
- `extraer.py`, `veredictum/`, `requirements-vm.txt` — el extractor (corre con Python puro).
- `correr_en_vm.sh` — lanza el análisis dejando la cuarentena dentro de la VM.
- `entrada/` — aquí pones el `.eml` a analizar.
- `salida/` — aquí aparece `evidencia.json` (lo único que cruza al host).

## Flujo dentro de la VM (Kali, sin red)
```bash
cd /media/sf_transfer_vm     # o donde se monte la carpeta compartida
bash correr_en_vm.sh entrada/caso.eml
# -> salida/evidencia.json
```

## Luego en el HOST
```powershell
python dictaminar.py transfer_vm\salida\evidencia.json CASO-ID
```

## Regla de oro
El binario extraído se queda en `/tmp/veredictum` DENTRO de la VM y muere al
revertir el snapshot. Nunca se copia al host. Al host solo cruza texto.
