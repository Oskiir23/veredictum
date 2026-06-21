# Guía completa de Veredictum (paso a paso, desde cero)

Esta guía está pensada para que **cualquiera**, sin conocimientos previos, pueda
montar y usar Veredictum de principio a fin: desde instalarlo hasta analizar un
correo malicioso real detonándolo en una máquina virtual aislada.

Lee los avisos ⚠️. Trabajar con malware real solo se hace dentro de una máquina
virtual aislada, **nunca en tu ordenador normal**.

---

## Índice
1. ¿Qué hace Veredictum?
2. Instalar lo necesario (Python, Node, el proyecto)
3. Conseguir las claves gratis (Gemini y VirusTotal)
4. Uso básico: analizar un correo inofensivo
5. Conceptos de VirtualBox (máquina virtual, carpeta compartida, snapshot)
6. Analizar malware real — Parte A: extracción aislada (VM Linux)
7. Analizar malware real — Parte B: detonación (VM Windows)
8. Limpieza y reglas de seguridad

---

## 1. ¿Qué hace Veredictum?

Le das un correo electrónico (`.eml` o `.msg`) y te devuelve un **borrador de
dictamen pericial** en Word: analiza cabeceras, autenticación, enlaces y adjuntos,
consulta VirusTotal, y —si quieres— ejecuta el adjunto en un laboratorio aislado
para ver qué hace. Marca lo que no puede confirmar para que lo valide un perito.

---

## 2. Instalar lo necesario

### 2.1 Instalar Python
1. Entra en https://www.python.org/downloads/ y descarga la última versión.
2. Ejecuta el instalador. **MUY IMPORTANTE:** marca la casilla
   **"Add python.exe to PATH"** antes de pulsar "Install Now".
3. Para comprobarlo: abre **PowerShell** (botón Inicio → escribe `powershell` →
   Enter) y escribe `python --version`. Debe salir un número de versión.

### 2.2 Instalar Node.js
1. Entra en https://nodejs.org/ y descarga la versión **LTS**.
2. Instálala con las opciones por defecto (Siguiente → Siguiente → Instalar).
3. Comprueba: en PowerShell, `node --version`.

### 2.3 Descargar el proyecto
1. Entra en https://github.com/Oskiir23/veredictum
2. Botón verde **Code → Download ZIP** (o, si tienes Git, `git clone`).
3. Descomprime el ZIP en una carpeta, p. ej. el Escritorio.

### 2.4 Instalar las dependencias
Abre PowerShell **dentro de la carpeta del proyecto** (en el Explorador, escribe
`powershell` en la barra de direcciones de la carpeta y pulsa Enter). Ejecuta:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
```
Si `Activate.ps1` da un error de permisos, ejecuta antes:
`Set-ExecutionPolicy -Scope Process Bypass -Force`.

---

## 3. Conseguir las claves gratis

Las claves son como contraseñas para usar servicios. **No se comparten** y no se
suben a internet. Se guardan en un fichero llamado `.env`.

### 3.1 Clave de Gemini (obligatoria, gratis)
1. Entra en https://aistudio.google.com/app/apikey (inicia sesión con tu cuenta de
   Google).
2. Pulsa **"Crear clave de API"**. Si te pide un proyecto, crea uno nuevo.
3. Copia la clave (una cadena larga de letras y números).

### 3.2 Clave de VirusTotal (opcional, gratis)
1. Crea una cuenta gratis en https://www.virustotal.com
2. Entra en https://www.virustotal.com/gui/my-apikey y copia tu API key.

### 3.3 Crear el fichero `.env`
1. En la carpeta del proyecto hay un fichero `.env.example`. Haz una copia y
   renómbrala a `.env` (sin nada delante del punto).
2. Ábrela con el Bloc de notas y pega tus claves:
```ini
GEMINI_API_KEY=pega_aqui_tu_clave_de_gemini
VT_API_KEY=pega_aqui_tu_clave_de_virustotal
VEREDICTUM_MODEL=gemini-2.5-flash
```
3. Guarda.

---

## 4. Uso básico: analizar un correo inofensivo

Para probar que todo funciona, hay un correo de ejemplo (inofensivo) incluido.
En PowerShell, dentro del proyecto:
```powershell
python run.py veredictum\samples\demo.eml
```
Al terminar, el dictamen aparece en la carpeta `salida\` como un `.docx`.

> Esto vale para correos **inofensivos o ya conocidos**. Para malware de verdad,
> usa el modo aislado (secciones 6 y 7).

---

## 5. Conceptos de VirtualBox (para las secciones 6 y 7)

Para analizar malware real necesitas una **máquina virtual (VM)**: un ordenador
"de mentira" que vive dentro del tuyo, aislado. Si el malware lo rompe, no pasa
nada: tu ordenador real no se toca.

- **VirtualBox**: el programa gratuito que crea y ejecuta máquinas virtuales.
  Descárgalo de https://www.virtualbox.org si no lo tienes.
- **Carpeta compartida**: una carpeta de tu ordenador real que la VM también puede
  ver. Es el "puente" para pasar ficheros sin usar internet.
- **Snapshot (instantánea)**: una "foto" del estado de la VM. Si algo sale mal (o
  detonas malware), puedes **revertir** a esa foto y la VM vuelve a estar limpia.
- **Guest Additions**: un pequeño complemento que se instala dentro de la VM y que,
  entre otras cosas, hace que funcionen las carpetas compartidas.

### 5.1 Cómo crear una CARPETA COMPARTIDA (clic a clic)
Con la VM **encendida** (o apagada, da igual):
1. En la ventana de la VM, menú de arriba: **Dispositivos → Carpetas compartidas →
   Preferencias de carpetas compartidas…**
2. A la derecha, pulsa el icono de **carpeta con un "+"** (añadir).
3. En **"Ruta de la carpeta"**, despliega y elige **"Otro…"**.
4. Se abre un explorador. Abajo, en el campo **"Carpeta:"**, escribe (o pega) la
   ruta de la carpeta `transfer_vm` del proyecto, por ejemplo:
   `C:\Users\TU_USUARIO\Desktop\Veredictum\transfer_vm` → pulsa **"Seleccionar carpeta"**.
5. Marca las casillas **"Automontar"** y **"Make Machine-permanent"** (para que no
   se pierda al reiniciar). Deja "Sólo lectura" SIN marcar.
6. Pulsa **Aceptar**, y **Aceptar** otra vez.
7. Dentro de la VM, la carpeta aparece como `\\VBOXSVR\transfer_vm` (Windows) o en
   `/media/sf_transfer_vm` (Linux).

### 5.2 Cómo DESCONECTAR LA RED de la VM (clic a clic)
1. En la ventana de la VM: **Dispositivos → Red**.
2. Haz clic en **"Conectar adaptador de red"** para **quitarle la marca**. Sin
   marca = sin internet. (Vuelve a hacer clic para reconectar, cuando ya no haya
   malware.)

### 5.3 Cómo HACER UNA SNAPSHOT (clic a clic)
1. En la ventana de la VM: **Máquina → Tomar instantánea…**
2. Ponle un nombre (p. ej. `limpio` o `pre-detonacion`) y pulsa **Aceptar**.
3. Para volver a ese estado: apaga la VM, en VirtualBox selecciona la VM → pestaña
   de **Instantáneas** → elige la instantánea → **Restaurar**.

---

## 6. Analizar malware real — Parte A: extracción aislada (VM Linux)

Aquí **NO se ejecuta** el malware: solo se analiza en estático (cabeceras, hashes,
macros, IOCs) dentro de una VM Linux (Kali o Parrot valen). Solo cruza al
ordenador real un fichero de **texto** (`evidencia.json`), nunca el binario.

1. **Prepara la carpeta de transferencia** (en tu ordenador real, en el proyecto):
   ```powershell
   python preparar_transfer.py
   ```
   Esto crea `transfer_vm\` con el extractor y las subcarpetas `entrada\` y `salida\`.
2. **Instala las dependencias dentro de la VM Linux**, con la VM aún con internet:
   ```bash
   pip install oletools extract-msg yara-x
   ```
3. **Comparte** la carpeta `transfer_vm` con la VM (ver 5.1) y **desconecta la red**
   (ver 5.2).
4. **Snapshot** del estado limpio (ver 5.3).
5. Pon el correo a analizar en `transfer_vm\entrada\` (en tu ordenador real).
6. **Dentro de la VM Linux**, abre un terminal y ejecuta:
   ```bash
   cd /media/sf_transfer_vm
   bash correr_en_vm.sh entrada/correo.eml
   ```
   (Si da "Permission denied": `sudo usermod -aG vboxsf $USER && newgrp vboxsf` y
   repite.) Genera `salida/evidencia.json`.
7. **En tu ordenador real**, genera el dictamen:
   ```powershell
   python dictaminar.py transfer_vm\salida\evidencia.json CASO-ID
   ```
8. **Revierte** la snapshot de la VM.

---

## 7. Analizar malware real — Parte B: detonación (VM Windows)

Aquí **SÍ se ejecuta** el malware para ver su comportamiento (procesos que crea,
ficheros que suelta, persistencia, red). Se hace en una **VM Windows** porque el
adjunto del caso es un programa de Windows.

> ⚠️ Máxima precaución. VM **desechable**, **sin red**, con **snapshot**. El malware
> muere al revertir.

### 7.1 Preparar la VM Windows
1. Una VM Windows desechable en VirtualBox, con **Guest Additions** instaladas
   (menú **Dispositivos → Insertar imagen de CD de los complementos del invitado…**,
   luego ejecuta el instalador dentro de Windows y reinicia).
2. Descarga **Process Monitor (Procmon)** de Sysinternals dentro de la VM
   (https://learn.microsoft.com/sysinternals/downloads/procmon) y descomprímelo.
   No se instala: es un `.exe` que se ejecuta directamente.
3. **Comparte** la carpeta `transfer_vm` con la VM (ver 5.1).
4. Copia el correo a analizar en `transfer_vm\entrada\` (en tu ordenador real).

### 7.2 Aislar la VM
1. **Desconecta la red** (ver 5.2).
2. **Dispositivos → Portapapeles compartido → Inhabilitado** y
   **Dispositivos → Arrastrar y soltar → Inhabilitado**.

### 7.3 Excluir la carpeta de análisis en Windows Defender
El antivirus de Windows borra el malware en cuanto aparece. Para poder detonarlo,
hay que decirle que ignore una carpeta:
1. Menú Inicio → **Seguridad de Windows**.
2. **Protección antivirus y contra amenazas**.
3. En "Configuración de antivirus y protección contra amenazas",
   **Administrar la configuración**.
4. Baja hasta **Exclusiones → Agregar o quitar exclusiones** (acepta el aviso de
   permisos / UAC).
5. **Agregar una exclusión → Carpeta** → elige **`C:\analisis`**.

### 7.4 Extraer el programa del correo (sin ejecutarlo)
Abre **PowerShell** dentro de la VM (clic derecho en Inicio → Terminal) y ejecuta:
```powershell
mkdir C:\analisis -Force | Out-Null
powershell -ExecutionPolicy Bypass -File \\VBOXSVR\transfer_vm\extraer_pe.ps1 -Eml \\VBOXSVR\transfer_vm\entrada\EV-MAIL-01.eml -Out C:\analisis\muestra.bin
```
Debe decir **`Cabecera MZ (PE): True`**. (Se guarda como `.bin` para que NO se
ejecute por accidente con un doble clic.)

### 7.5 Snapshot
**Máquina → Tomar instantánea** → nómbrala `pre-detonacion` (ver 5.3).

### 7.6 Detonar y grabar con Procmon
1. Abre **Procmon** (doble clic en `Procmon64.exe`). Acepta el aviso de permisos
   (UAC) y la licencia (Agree). Empieza a grabar automáticamente.
2. Filtra para ver solo el malware: menú **Filter → Filter…**, elige
   **"Process Name"**, condición **"is"**, escribe **`muestra.exe`**, acción
   **"Include"** → pulsa **Add** → **OK**.
3. Limpia lo ya grabado: menú **Edit → Clear Display**.
4. Ahora detona, en la PowerShell:
   ```powershell
   copy C:\analisis\muestra.bin C:\analisis\muestra.exe
   C:\analisis\muestra.exe
   ```
   ⚠️ Esto ejecuta el malware. Déjalo correr **30–60 segundos**.
5. Para de grabar: pulsa **Ctrl + E** en Procmon.
6. Guarda los datos: menú **File → Save…** → marca
   **"Events displayed using current filter"** y el formato **CSV** → guárdalo en
   `\\VBOXSVR\transfer_vm\salida\procmon.csv`.

### 7.7 Generar el dictamen (en tu ordenador real)
```powershell
python dictaminar.py transfer_vm\salida\evidencia.json CASO-ID --procmon transfer_vm\salida\procmon.csv --proceso muestra.exe
```
El `--proceso muestra.exe` se queda solo con la actividad del malware (y de los
programas que lanza), descartando el ruido del sistema. El dictamen tendrá la
sección **"Análisis dinámico propio"** con procesos, ficheros, persistencia y red.

### 7.8 Limpiar
**Revierte** la snapshot `pre-detonacion` (ver 5.3). Esto borra el malware, su
persistencia, los ficheros que soltó y la exclusión de Defender. La VM queda como
nueva.

---

## 8. Limpieza y reglas de seguridad

- El malware **nunca toca tu ordenador real**: vive y muere dentro de la VM.
- Solo cruzan al ordenador real ficheros de **texto** (`evidencia.json`,
  `procmon.csv`), nunca el programa.
- A VirusTotal se envía **solo el hash** (huella), nunca el fichero.
- Tras analizar, **revierte siempre la snapshot** de la VM.
- Tus claves (`.env`) son privadas y no se suben a ningún sitio.

---

*Veredictum — Óscar Carretero Hilillo. Herramienta de apoyo: el dictamen es un
borrador que siempre debe validar un perito.*
