# Veredictum

**Agente DFIR autónomo: triaje de correo malicioso → borrador de dictamen pericial.**

Le pasas un correo (`.eml` o `.msg`). Veredictum lo analiza en estático con herramientas
forenses, un agente LLM razona sobre los hechos y genera un **borrador de
dictamen pericial en Word** — marcando lo que **no** puede confirmar para que un
perito humano lo valide, en lugar de alucinar conclusiones.

> Misma idea que hizo grande a VirusTotal: coger algo que hoy solo sabe hacer un
> analista senior —lento y artesanal— y democratizarlo. El perito pasa de
> **redactar** a **validar**.

> ⚠️ **Es una herramienta de apoyo.** Genera un BORRADOR que SIEMPRE requiere
> revisión y validación de un perito antes de su emisión. No sustituye el juicio
> pericial humano.

> 📖 **¿Nunca has hecho esto?** Hay una **guía paso a paso desde cero** (clic a clic,
> incluido cómo crear máquinas virtuales, carpetas compartidas y aislar la red):
> **[`GUIA.md`](GUIA.md)** — y la misma en Word: **[`GUIA.docx`](GUIA.docx)**.

---

## Índice

1. [Características](#características)
2. [Arquitectura](#arquitectura)
3. [Requisitos](#requisitos)
4. [Instalación](#instalación)
5. [Claves de API (gratis)](#claves-de-api-gratis)
6. [Uso — Modo directo](#uso--modo-directo)
7. [Uso — Modo aislado en VM (malware real)](#uso--modo-aislado-en-vm-malware-real)
8. [Modelo de seguridad](#modelo-de-seguridad)
9. [Estructura del proyecto](#estructura-del-proyecto)
10. [Limitaciones y aviso legal](#limitaciones-y-aviso-legal)
11. [Roadmap](#roadmap)
12. [Autor y licencia](#autor-y-licencia)

---

## Características

- **Parseo de correo** (`.eml` y `.msg` de Outlook): cabeceras, autenticación SPF/DKIM/DMARC, cuerpo, adjuntos.
- **Extracción de IOCs**: URLs, IPs, dominios, correos y hashes (en formato *defang*).
- **Análisis de adjuntos en estático**: hashes (MD5/SHA-1/SHA-256), tipo real por
  *magic bytes* (detecta un `.exe` disfrazado de `.zip`), y macros VBA con `olevba`.
- **VirusTotal**: consulta por hash (nunca se sube el fichero).
- **Reglas YARA**: escaneo de adjuntos con `yara-x`; reglas ampliables en
  `veredictum/rules/` (o vía `VEREDICTUM_YARA_RULES`).
- **Comportamiento dinámico**: recupera el informe de detonación de los sandboxes de
  VirusTotal (procesos, ficheros soltados, registro, red y técnicas MITRE ATT&CK) sin
  ejecutar nada en local.
- **Detonación propia**: ingiere artefactos de Process Monitor (CSV) de una detonación
  en laboratorio aislado → procesos, ficheros, persistencia y red en el dictamen.
- **Dictamen en Word** con plantilla pericial: portada TLP, juramento, normativa,
  metodología, IOCs, conclusiones numeradas, cadena de custodia.
- **Marcado de incertidumbre**: lo no concluyente se lleva a una sección de
  "Limitaciones y puntos para validación pericial". No inventa veredictos.
- **Modo aislado**: la manipulación de muestras vivas ocurre en una VM sin red;
  al host solo cruza texto. El binario nunca toca tu equipo.

---

## Arquitectura

Los **hechos** (hashes, autenticación, IOCs) los aportan las herramientas
forenses; el **razonamiento** (veredicto, conclusiones, incertidumbres) lo aporta
el LLM. Así los hechos no se pueden alucinar.

**Modo directo** (muestras benignas/conocidas) — todo en una máquina:

```
.eml → [agente LLM + herramientas] → dictamen .docx
```

**Modo aislado** (malware real) — la parte peligrosa se separa:

```
   VM aislada (SIN red)                 │  host (con internet)
   ───────────────────                  │  ──────────────────
   extraer.py                           │
   .eml → parse + hash + olevba         │
        → evidencia.json  ──────────────┼──►  dictaminar.py
   (binario → /tmp, NO sale)   carpeta  │     LLM + VirusTotal
                              compartida │     → dictamen .docx
```

El motor LLM está aislado en `veredictum/llm.py` (hoy Gemini); para usar un
modelo local (p. ej. Ollama) solo se reimplementa ese fichero.

---

## Requisitos

- **Python 3.10+**
- **Node.js 18+** (el dictamen `.docx` se genera con `docx-js`)
- Una clave de API de **Gemini** (gratis) — ver más abajo
- *(Opcional)* clave de **VirusTotal** (gratis)
- *(Opcional, para malware real)* **VirtualBox** + una VM Linux (Kali/Parrot)

---

## Instalación

```bash
# 1. Clonar
git clone https://github.com/<tu-usuario>/veredictum.git
cd veredictum

# 2. Entorno virtual de Python
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# 3. Dependencias de Python
pip install -r requirements.txt

# 4. Dependencias de Node (el renderer del .docx)
npm install

# 5. Configurar las claves (ver siguiente sección)
copy .env.example .env      # Windows  (Linux/Mac: cp .env.example .env)
# edita .env y pega tus claves
```

---

## Claves de API (gratis)

Las claves **no se incluyen** en el repositorio. Cada usuario pone las suyas en
un fichero `.env` (que está en `.gitignore` y nunca se sube).

### Gemini (obligatoria, gratis)

1. Entra en **https://aistudio.google.com/app/apikey** (cuenta de Google).
2. Pulsa **Crear clave de API** (si pide proyecto, crea uno nuevo).
3. Copia la clave.

### VirusTotal (opcional, gratis)

1. Crea una cuenta en **https://www.virustotal.com**.
2. Ve a **https://www.virustotal.com/gui/my-apikey** y copia tu API key.
3. Sin esta clave, el análisis de hash se marca como "no consultado" (pendiente
   de verificación humana) — funciona igual, pero sin el veredicto multimotor.

### Dónde ponerlas

Edita `.env` (copiado de `.env.example`):

```ini
GEMINI_API_KEY=tu_clave_de_gemini
VT_API_KEY=tu_clave_de_virustotal      # opcional
VEREDICTUM_MODEL=gemini-2.5-flash      # modelo del free tier
```

---

## Uso — Modo directo

Para muestras **inofensivas o ya conocidas**, sin VM. Analiza y genera el
dictamen en un solo paso:

```bash
python run.py veredictum/samples/demo.eml
```

El dictamen aparece en `salida/dictamen_<caso>.docx`.

---

## Uso — Modo aislado en VM (malware real)

Para correos con **adjuntos potencialmente maliciosos**, la manipulación se hace
en una máquina virtual **sin salida a internet**. El binario nunca toca el host;
solo cruza un JSON de texto con los hechos.

> Se usa **VirtualBox** con un guest **Linux** (Kali o Parrot van perfectos: ya
> traen Python). El motivo de elegir VirtualBox es que sus *carpetas compartidas*
> funcionan por el hipervisor (no por red), así puedes transferir ficheros con la
> red de la VM **apagada**.

### 1. Preparar la VM

Crea (o clona) una VM Linux en VirtualBox. Recomendado partir de una imagen ya
instalada de Kali/Parrot. **Trabaja siempre sobre un clon desechable**, no sobre
tu VM principal.

**Instala las dependencias del extractor MIENTRAS la VM aún tiene red** (antes de
aislarla en el paso 2). Las wheels son específicas de Linux, por eso se instalan
dentro de la VM y no se pueden empaquetar desde el host:

```bash
pip install yara-x oletools extract-msg        # en la VM, con red
```

Si alguna falta, el extractor la omite sin romper (p. ej. sin `yara-x` no escanea
reglas, sin `oletools` no analiza macros).

### 2. Endurecer la VM (qué desactivar)

Con la VM **apagada**, abre **Configuración** y aplica:

**a) Desactivar la red** (lo más importante — sin esto el malware tendría salida):
- `Configuración → Red → Adaptador 1`
- **Desmarca "Habilitar adaptador de red"**.
- Repite para los adaptadores 2–4 si estuvieran activos.

**b) Desactivar portapapeles y arrastrar-soltar** (vectores de contaminación):
- `Configuración → General → Avanzado` (o pestaña *Features* en modo Expert)
- **Portapapeles compartido → Inhabilitado**
- **Arrastrar y soltar → Inhabilitado**

### 3. Crear la carpeta compartida (canal de transferencia)

Esta carpeta es el **único** puente VM↔host. Comparte SOLO la carpeta del
extractor — **nunca** la carpeta del proyecto que contiene tu `.env`.

1. En el host, genera la carpeta de transferencia (copia el extractor sin el
   `.env`, y crea `entrada/` y `salida/`):
   ```bash
   python preparar_transfer.py
   ```
2. `Configuración → Carpetas compartidas → (icono +)`
3. Rellena:
   - **Ruta de la carpeta**: ruta a `transfer_vm/` en tu host.
   - **Nombre de la carpeta**: `transfer_vm`.
   - **Automontar**: ✅ marcado.
   - **Sólo lectura**: ❌ sin marcar (la VM debe escribir el `evidencia.json`).
4. Acepta. En Kali se montará en `/media/sf_transfer_vm`.

> Si dentro de la VM da "Permission denied" al entrar en `/media/sf_transfer_vm`,
> el usuario no está en el grupo `vboxsf`:
> ```bash
> sudo usermod -aG vboxsf $USER && newgrp vboxsf
> ```

### 4. Tomar una instantánea (snapshot) del estado limpio

Antes de meter malware, captura un punto de retorno:
- En la ventana de la VM: `Máquina → Tomar instantánea` (nómbrala `limpio`).

### 5. Flujo de análisis

```
[Host]  Copia el correo a analizar en  transfer_vm/entrada/caso.eml
[VM]    Arranca la VM (login por defecto en imágenes Kali: kali / kali)
[VM]    En una terminal:
            cd /media/sf_transfer_vm
            bash correr_en_vm.sh entrada/caso.eml
        -> genera salida/evidencia.json (solo texto)
        -> el binario queda en /tmp/veredictum DENTRO de la VM
[Host]  python dictaminar.py transfer_vm/salida/evidencia.json CASO-ID
        -> salida/dictamen_CASO-ID.docx
```

### 6. Limpieza (importante)

Cuando termines, **revierte la instantánea** (`Máquina → Instantáneas →
Restaurar 'limpio'`). Esto borra el binario y deja la VM limpia para el siguiente
caso.

---

## Análisis dinámico propio (detonación)

Opcional, para obtener comportamiento de **tu propia detonación** (no solo el de
VirusTotal). Aquí **sí se ejecuta el malware**, así que requiere disciplina de
sandbox. El adjunto del caso es un PE de Windows → se detona en una **VM Windows
instrumentada**.

> ⚠️ Detonar malware es peligroso. Hazlo solo en una VM desechable, aislada y con
> snapshot. Nunca en tu equipo de trabajo.

### 1. Preparar la VM Windows
- VM Windows **desechable** en VirtualBox, con **Guest Additions** instaladas
  (necesarias para la carpeta compartida).
- Instala **Process Monitor** (Procmon, de Sysinternals) dentro de la VM.
- `Dispositivos → Carpetas compartidas`: comparte la carpeta `transfer_vm` del
  proyecto (**Automontar** + **Make Machine-permanent**). Quedará en
  `\\VBOXSVR\transfer_vm`.
- Copia el `.eml` a analizar en `transfer_vm/entrada/`.

### 2. Aislar la VM
- `Dispositivos → Red` → **desmarca "Conectar adaptador de red"** (sin salida).
- `Dispositivos → Portapapeles compartido` y `Arrastrar y soltar` → **Inhabilitado**.

### 3. Excluir la carpeta de análisis en Windows Defender
Defender borra la muestra en cuanto se escribe (es malware real). Para poder detonar:
- **Seguridad de Windows → Protección antivirus y contra amenazas → Administrar la
  configuración → Exclusiones → Agregar → Carpeta → `C:\analisis`**.
- *(Alternativa más brusca: desactivar la Protección en tiempo real.)*

### 4. Extraer el PE del correo (sin ejecutarlo)
En una PowerShell de la VM:
```powershell
mkdir C:\analisis -Force | Out-Null
powershell -ExecutionPolicy Bypass -File \\VBOXSVR\transfer_vm\extraer_pe.ps1 -Eml \\VBOXSVR\transfer_vm\entrada\EV-MAIL-01.eml -Out C:\analisis\muestra.bin
```
Debe imprimir **`Cabecera MZ (PE): True`**.

### 5. Snapshot (punto de retorno)
`Máquina → Tomar instantánea` → nómbrala `pre-detonacion`.

### 6. Detonar con Procmon
1. Abre **Procmon** (acepta UAC + licencia). Empieza a capturar solo.
2. **Filter → Filter…** → `Process Name` `is` `muestra.exe` → `Include` → **Add** → **OK**.
3. **Edit → Clear Display** (limpia el ruido previo).
4. Detona:
   ```powershell
   copy C:\analisis\muestra.bin C:\analisis\muestra.exe
   C:\analisis\muestra.exe
   ```
   Déjalo **~30–60 s**.
5. **Ctrl+E** para parar la captura.
6. **File → Save** → **"Events displayed using current filter"** + formato **CSV** →
   `\\VBOXSVR\transfer_vm\salida\procmon.csv`.
   > ⚠️ Si guardas **"All events"** el CSV sale enorme (cientos de MB con ruido del
   > sistema). En ese caso, filtra al árbol de la muestra con `--proceso` (paso 7).

### 7. Generar el dictamen (en el host)
```bash
python dictaminar.py transfer_vm/salida/evidencia.json CASO-ID --procmon transfer_vm/salida/procmon.csv --proceso muestra.exe
```
`--proceso muestra.exe` filtra al **árbol de procesos** de la muestra (la muestra y
los procesos que crea), descartando el ruido del sistema aunque hayas guardado
"All events". El dictamen incluirá la **§8.7 "Análisis dinámico propio"** (procesos,
ficheros escritos, persistencia en registro y red), diferenciada del comportamiento
de VirusTotal (§8.6).

### 8. Limpiar
**Revierte** la instantánea `pre-detonacion` → elimina el malware ejecutado, su
persistencia, los ficheros soltados y la exclusión de Defender. VM como nueva.

---

## Modelo de seguridad

- **Nunca se ejecuta** ningún adjunto. Solo análisis estático.
- Los adjuntos se escriben con sufijo **`.quarantine`** (no ejecutable, no
  doble-clicable) en una carpeta de cuarentena.
- En modo aislado, la cuarentena vive **dentro de la VM** (`/tmp/veredictum`); al
  host solo cruza `evidencia.json` (texto).
- A VirusTotal va **solo el hash**, jamás el fichero.
- El SHA-256 se calcula **en memoria antes de tocar disco**: aunque el antivirus
  borre la muestra, el dictamen conserva el hash.
- El `.env` con tus claves está en `.gitignore` y no se sube.

> Para analizar binarios maliciosos en profundidad (análisis **dinámico**), hazlo
> siempre en una VM aislada y desechable, nunca en tu equipo de trabajo.

---

## Estructura del proyecto

```
veredictum/
  config.py            Claves, modelo, rutas (dotenv opcional)
  context.py           Store de hechos compartido entre herramientas
  llm.py               Capa LLM aislada (Gemini; cambiable a local)
  agent.py             Persona del perito + orquestación (directo y split)
  extractor.py         Extracción offline (para la VM)
  tools/
    email_tools.py     parse_email, extract_iocs
    attachment_tools.py analyze_attachment (olevba), vt_lookup
    report_tools.py    write_report (invoca el renderer Node)
  render/
    gen_dictamen.js    Renderer del .docx (docx-js) con la plantilla pericial
  samples/demo.eml     Correo de demostración (inofensivo)
run.py                 CLI modo directo
extraer.py             CLI extracción (en la VM)
dictaminar.py          CLI dictamen desde hechos (en el host)
transfer_vm/           Carpeta a compartir con la VM (extractor + entrada/salida)
tests/                 Pruebas de humo
```

---

## Limitaciones y aviso legal

- El resultado es un **borrador** sujeto a validación pericial. No es un dictamen
  firmado ni asesoramiento legal.
- El análisis de macros (`olevba`) requiere `oletools`; en una VM sin él, se
  omite (los PE no necesitan macros).
- Soporte `.msg` (Outlook) y reglas YARA: en el roadmap.
- Úsalo solo sobre evidencias para las que tengas autorización.

---

## Roadmap

- [x] **Análisis dinámico** vía sandboxes de VirusTotal (comportamiento + MITRE ATT&CK).
- [x] Soporte de correo `.msg` (Outlook).
- [x] Reglas **YARA** sobre adjuntos (motor `yara-x`; reglas en `veredictum/rules/`).
- [x] **Detonación propia**: ingesta de artefactos (Procmon CSV) → dictamen. Ver guía abajo.
- [ ] Automatizar el laboratorio de detonación (orquestar Sysmon/pcap).
- [ ] Opción de **LLM local** (Ollama) para flujo 100 % offline.

---

## Autor y licencia

**Óscar Carretero Hilillo** — Técnico Superior en ASIR · Máster en Ciberseguridad.

Licencia **MIT** (ver `LICENSE`).
