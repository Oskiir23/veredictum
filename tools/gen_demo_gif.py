"""Genera el GIF de demostración de Veredictum (terminal-cast).

Renderiza, fotograma a fotograma con Pillow, el flujo directo:

    python run.py veredictum\\samples\\demo.eml

Muestra el comando "tecleándose", las herramientas del agente disparándose
y el veredicto final, con un efecto de terminal. El texto reproduce la salida
real del análisis de `demo.eml` (no inventa hechos).

Uso:
    python tools/gen_demo_gif.py            # -> docs/demo.gif
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- Lienzo y tipografía -------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "demo.gif"

ANCHO, ALTO = 860, 560
MARGEN_X, MARGEN_Y = 28, 24
INTERLINEA = 24
TAM_FUENTE = 16

FUENTE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", TAM_FUENTE)
FUENTE_B = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", TAM_FUENTE)

# Paleta tipo terminal oscura
FONDO = (13, 17, 23)        # gris muy oscuro (estilo GitHub dark)
BARRA = (22, 27, 34)        # barra de título
TEXTO = (201, 209, 217)     # gris claro
TENUE = (125, 133, 144)     # comentarios / tenue
PROMPT = (63, 185, 80)      # verde prompt
CYAN = (88, 166, 255)       # rutas / herramientas
AMARILLO = (210, 168, 60)   # avisos
ROJO = (248, 81, 73)        # veredicto / peligro
VERDE = (63, 185, 80)       # ok
SEP = (48, 54, 61)          # separadores

# (texto, color, negrita)
Linea = tuple


def _fondo() -> Image.Image:
    """Lienzo base con la barra de título de una ventana de terminal."""
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, ANCHO, 32], fill=BARRA)
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 20 + i * 22
        d.ellipse([cx - 6, 10, cx + 6, 22], fill=color)
    d.text((ANCHO // 2 - 95, 8), "Veredictum  —  PowerShell", font=FUENTE, fill=TENUE)
    return img


def _dibuja(lineas: list, cursor_en: int | None = None, cursor_col: int | None = None) -> Image.Image:
    """Renderiza una lista de líneas ya 'reveladas'. Cada línea es lista de
    segmentos (texto, color, negrita). `cursor_en`/`cursor_col` pinta el cursor."""
    img = _fondo()
    d = ImageDraw.Draw(img)
    y = MARGEN_Y + 18
    for idx, segmentos in enumerate(lineas):
        x = MARGEN_X
        for (txt, color, bold) in segmentos:
            fnt = FUENTE_B if bold else FUENTE
            d.text((x, y), txt, font=fnt, fill=color)
            x += d.textlength(txt, font=fnt)
        if cursor_en == idx:
            cx = MARGEN_X
            if cursor_col is not None and segmentos:
                # ancho hasta cursor_col en la primera (única) tira de texto
                full = "".join(t for t, _, _ in segmentos)
                cx = MARGEN_X + d.textlength(full[:cursor_col], font=FUENTE)
            d.rectangle([cx, y + 2, cx + 9, y + TAM_FUENTE + 2], fill=TEXTO)
        y += INTERLINEA
    return img


# --- Guion (fiel a la salida real de demo.eml) ---------------------------
PROMPT_TXT = "PS C:\\...\\Veredictum> "
COMANDO = "python run.py veredictum\\samples\\demo.eml"

# Líneas de salida tras el comando, en orden de aparición.
SALIDA = [
    [("", TEXTO, False)],
    [("[Veredictum] Analizando: ", TEXTO, False), ("veredictum\\samples\\demo.eml", CYAN, False)],
    [("", TEXTO, False)],
    [("  -> parse_email", CYAN, True), ("         cabeceras + autenticación SPF/DKIM/DMARC", TENUE, False)],
    [("  -> extract_iocs", CYAN, True), ("        URLs, IPs e indicadores del cuerpo", TENUE, False)],
    [("  -> analyze_attachment", CYAN, True), ("  factura.txt   (olevba + YARA)", TENUE, False)],
    [("  -> vt_lookup", CYAN, True), ("           VirusTotal por hash (nunca el fichero)", TENUE, False)],
    [("  -> write_report", CYAN, True), ("        render del dictamen pericial (.docx)", TENUE, False)],
    [("", TEXTO, False)],
    [("======================================================================", SEP, False)],
    [("  VEREDICTO: ", TEXTO, True), ("Phishing + distribución de malware", ROJO, True),
     ("   confianza: ", TEXTO, True), ("ALTO", ROJO, True)],
    [("======================================================================", SEP, False)],
    [("   - Suplantación de \"Banco Seguro\"  (display-name spoofing)", TEXTO, False)],
    [("   - Autenticación: SPF=fail  DKIM=none  DMARC=fail", TEXTO, False)],
    [("   - Ingeniería social: \"habilite las macros\" + urgencia", TEXTO, False)],
    [("   - URL sospechosa: login-banco-seguro.example/verificar", TEXTO, False)],
    [("   - Incertidumbres marcadas para revisión humana ", AMARILLO, False),
     ("(no alucina)", TENUE, False)],
    [("", TEXTO, False)],
    [("  [OK] Borrador generado: ", VERDE, True), ("salida\\dictamen_demo.eml.docx", CYAN, False)],
]


def construir_frames() -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    duraciones: list[int] = []  # ms

    def add(img: Image.Image, ms: int) -> None:
        frames.append(img)
        duraciones.append(ms)

    # 1) Cursor parpadeando antes de teclear
    base_prompt = [[(PROMPT_TXT, PROMPT, True)]]
    for _ in range(2):
        add(_dibuja(base_prompt, cursor_en=0, cursor_col=len(PROMPT_TXT)), 320)

    # 2) Tecleo del comando (2-3 chars por frame)
    paso = 3
    for n in range(0, len(COMANDO) + 1, paso):
        parcial = COMANDO[:n]
        linea = [[(PROMPT_TXT, PROMPT, True), (parcial, TEXTO, False)]]
        col = len(PROMPT_TXT) + len(parcial)
        add(_dibuja(linea, cursor_en=0, cursor_col=col), 55)
    # comando completo, pausa antes de "enter"
    linea_full = [[(PROMPT_TXT, PROMPT, True), (COMANDO, TEXTO, False)]]
    add(_dibuja(linea_full, cursor_en=0, cursor_col=len(PROMPT_TXT) + len(COMANDO)), 500)

    # 3) Aparicion progresiva de la salida
    acumulado = list(linea_full)
    # ritmos por linea: las herramientas con un respiro (parece trabajo)
    ritmo = {
        1: 360,   # Analizando
        3: 520, 4: 520, 5: 600, 6: 600, 7: 600,  # herramientas
        10: 450,  # veredicto
    }
    for i, seg in enumerate(SALIDA):
        acumulado.append(seg)
        ms = ritmo.get(i, 200)
        add(_dibuja(acumulado), ms)

    # 4) Hold final (mantener el resultado en pantalla)
    add(_dibuja(acumulado), 3200)

    return frames, duraciones


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    frames, duraciones = construir_frames()
    frames[0].save(
        DESTINO,
        save_all=True,
        append_images=frames[1:],
        duration=duraciones,
        loop=0,
        optimize=True,
        disposal=2,
    )
    kb = DESTINO.stat().st_size / 1024
    print(f"GIF generado: {DESTINO}  ({len(frames)} frames, {kb:.0f} KB)")


if __name__ == "__main__":
    main()
