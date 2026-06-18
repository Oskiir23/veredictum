"""Parseo de correo y extracción de indicadores (IOCs)."""

import hashlib
import re
from email import message_from_bytes, policy
from email.message import EmailMessage
from pathlib import Path

from .. import context
from ..config import CUARENTENA, SUFIJO_CUARENTENA, asegurar_directorios


def _sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def _auth_results(msg: EmailMessage) -> dict:
    """Extrae el veredicto SPF/DKIM/DMARC de las cabeceras de autenticación."""
    crudo = " ".join(msg.get_all("Authentication-Results", []))
    crudo += " " + " ".join(msg.get_all("Received-SPF", []))
    out = {"spf": "desconocido", "dkim": "desconocido", "dmarc": "desconocido"}
    for clave in out:
        m = re.search(rf"{clave}\s*=\s*(\w+)", crudo, re.IGNORECASE)
        if m:
            out[clave] = m.group(1).lower()
    return out


def _escribir_cuarentena(nombre: str, datos: bytes) -> dict:
    """Escribe un adjunto en cuarentena con sufijo NO ejecutable y lo describe."""
    sha = _sha256(datos)
    destino = CUARENTENA / f"{sha[:12]}_{Path(nombre).name}{SUFIJO_CUARENTENA}"
    destino.write_bytes(datos)
    return {
        "nombre": nombre,  # nombre original declarado en el correo
        "sha256": sha,
        "tamano_bytes": len(datos),
        "ruta": str(destino),  # ruta de la copia en cuarentena
    }


def _guardar(ruta: Path, datos_file: bytes, meta: dict, adjuntos: list) -> dict:
    """Guarda los HECHOS en el store (el dictamen los toma de aquí, no del LLM)."""
    context.EVIDENCIA["correo"] = {
        "evidencia": ruta.name,
        "tamano_bytes": len(datos_file),
        "sha256": _sha256(datos_file),
        "md5": hashlib.md5(datos_file).hexdigest(),
        "remitente": meta["remitente"],
        "destinatario": meta["destinatario"],
        "asunto": meta["asunto"],
        "fecha": meta["fecha"],
        "return_path": meta["return_path"],
        "message_id": meta["message_id"],
        "autenticacion": meta["autenticacion"],
    }
    context.EVIDENCIA["adjuntos"] = [dict(a) for a in adjuntos]
    return {**meta, "adjuntos": adjuntos}


def parse_email(file_path: str) -> dict:
    """Parsea un correo .eml o .msg y devuelve cabeceras, autenticación, cuerpo y adjuntos.

    Detecta el formato por extensión/firma. Extrae remitente, destinatario, asunto,
    fecha, Message-ID, Received, veredicto SPF/DKIM/DMARC, el cuerpo en texto y los
    adjuntos (cada uno con su SHA-256 y la ruta de la copia en cuarentena).

    Args:
        file_path: Ruta al fichero .eml o .msg en disco.
    """
    asegurar_directorios()
    ruta = Path(file_path)
    if not ruta.exists():
        return {"error": f"No existe el fichero: {file_path}"}

    datos_file = ruta.read_bytes()
    # .msg de Outlook es un contenedor OLE (firma D0 CF 11 E0).
    es_msg = ruta.suffix.lower() == ".msg" or datos_file[:4] == b"\xd0\xcf\x11\xe0"
    return _parse_msg(ruta, datos_file) if es_msg else _parse_eml(ruta, datos_file)


def _parse_eml(ruta: Path, datos_file: bytes) -> dict:
    msg: EmailMessage = message_from_bytes(datos_file, policy=policy.default)

    cuerpo = ""
    if msg.get_body(preferencelist=("plain",)):
        cuerpo = msg.get_body(preferencelist=("plain",)).get_content()
    elif msg.get_body(preferencelist=("html",)):
        cuerpo = msg.get_body(preferencelist=("html",)).get_content()

    adjuntos = [
        _escribir_cuarentena(
            parte.get_filename() or "sin_nombre.bin",
            parte.get_payload(decode=True) or b"",
        )
        for parte in msg.iter_attachments()
    ]

    meta = {
        "remitente": msg.get("From", ""),
        "destinatario": msg.get("To", ""),
        "asunto": msg.get("Subject", ""),
        "fecha": msg.get("Date", ""),
        "message_id": msg.get("Message-ID", ""),
        "return_path": msg.get("Return-Path", ""),
        "received": msg.get_all("Received", []),
        "autenticacion": _auth_results(msg),
        "cuerpo": cuerpo[:8000],
    }
    return _guardar(ruta, datos_file, meta, adjuntos)


def _parse_msg(ruta: Path, datos_file: bytes) -> dict:
    try:
        import extract_msg
    except ImportError:
        return {"error": "Para analizar .msg instala extract-msg (pip install extract-msg)."}

    try:
        m = extract_msg.Message(str(ruta))
    except Exception as e:  # noqa: BLE001 — fichero corrupto o no es un .msg válido
        return {"error": f"No se pudo abrir el .msg: {str(e)[:200]}"}

    try:
        hdr = m.header  # email.message.Message con las cabeceras de transporte, o None
        if hdr is not None:
            received = hdr.get_all("Received", [])
            autenticacion = _auth_results(hdr)
            return_path = hdr.get("Return-Path", "")
            message_id = hdr.get("Message-ID", "") or (m.messageId or "")
        else:
            received, return_path = [], ""
            autenticacion = {"spf": "desconocido", "dkim": "desconocido", "dmarc": "desconocido"}
            message_id = m.messageId or ""

        adjuntos = []
        for att in m.attachments:
            nombre = att.longFilename or att.shortFilename or "sin_nombre.bin"
            datos = att.data
            if isinstance(datos, (bytes, bytearray)):  # ignora adjuntos .msg anidados
                adjuntos.append(_escribir_cuarentena(nombre, bytes(datos)))

        meta = {
            "remitente": m.sender or "",
            "destinatario": m.to or "",
            "asunto": m.subject or "",
            "fecha": str(m.date or ""),
            "message_id": message_id,
            "return_path": return_path,
            "received": received,
            "autenticacion": autenticacion,
            "cuerpo": (m.body or "")[:8000],
        }
    finally:
        m.close()
    return _guardar(ruta, datos_file, meta, adjuntos)


# --- Extracción de IOCs ---

_RE_URL = re.compile(r"https?://[^\s\"'<>)\]]+", re.IGNORECASE)
_RE_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_RE_DOMINIO = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)
_RE_HASH = re.compile(r"\b[a-f0-9]{32,64}\b", re.IGNORECASE)


def _defang(valor: str) -> str:
    return valor.replace("http", "hxxp").replace(".", "[.]")


def extract_iocs(texto: str) -> dict:
    """Extrae indicadores de compromiso (IOCs) de un texto.

    Localiza URLs, direcciones IP, dominios, correos y hashes. Devuelve cada IOC
    también en formato 'defanged' (hxxp, [.]) para que sea seguro pegarlo en el
    dictamen sin que se convierta en enlace clicable.

    Args:
        texto: Texto donde buscar (cuerpo del correo, cabeceras, etc.).
    """
    urls = sorted(set(_RE_URL.findall(texto)))
    ips = sorted(set(_RE_IP.findall(texto)))
    correos = sorted(set(_RE_EMAIL.findall(texto)))
    hashes = sorted(set(_RE_HASH.findall(texto)))
    dominios = sorted(
        {d for d in _RE_DOMINIO.findall(texto) if "@" not in d and d not in ips}
    )
    resultado = {
        "urls": urls,
        "urls_defanged": [_defang(u) for u in urls],
        "ips": ips,
        "dominios": dominios,
        "correos": correos,
        "hashes": hashes,
    }
    # Acumula IOCs en el store (unión con lo ya encontrado).
    acc = context.EVIDENCIA.setdefault("iocs", {})
    for clave in ("urls", "ips", "dominios", "correos", "hashes"):
        previo = set(acc.get(clave, []))
        acc[clave] = sorted(previo | set(resultado[clave]))
    return resultado
