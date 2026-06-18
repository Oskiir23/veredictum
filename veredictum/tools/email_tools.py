"""Parseo de correo y extracción de indicadores (IOCs)."""

import hashlib
import re
from email import message_from_binary_file, policy
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


def parse_email(file_path: str) -> dict:
    """Parsea un correo .eml y devuelve cabeceras, autenticación, cuerpo y adjuntos.

    Extrae remitente, destinatario, asunto, fecha, Message-ID, ruta de servidores
    (Received), veredicto SPF/DKIM/DMARC, el cuerpo en texto y la lista de adjuntos
    (cada uno con su SHA-256 y la ruta donde se ha guardado para analizar después).

    Args:
        file_path: Ruta al fichero .eml en disco.
    """
    asegurar_directorios()
    ruta = Path(file_path)
    if not ruta.exists():
        return {"error": f"No existe el fichero: {file_path}"}

    with ruta.open("rb") as f:
        msg: EmailMessage = message_from_binary_file(f, policy=policy.default)

    cuerpo = ""
    if msg.get_body(preferencelist=("plain",)):
        cuerpo = msg.get_body(preferencelist=("plain",)).get_content()
    elif msg.get_body(preferencelist=("html",)):
        cuerpo = msg.get_body(preferencelist=("html",)).get_content()

    adjuntos = []
    for parte in msg.iter_attachments():
        nombre = parte.get_filename() or "sin_nombre.bin"
        datos = parte.get_payload(decode=True) or b""
        sha = _sha256(datos)
        # Se escribe en cuarentena con sufijo NO ejecutable: aunque el adjunto
        # sea un .exe disfrazado, el fichero en disco no es doble-clicable.
        destino = CUARENTENA / f"{sha[:12]}_{Path(nombre).name}{SUFIJO_CUARENTENA}"
        destino.write_bytes(datos)
        adjuntos.append(
            {
                "nombre": nombre,  # nombre original declarado en el correo
                "sha256": sha,
                "tamano_bytes": len(datos),
                "ruta": str(destino),  # ruta de la copia en cuarentena
            }
        )

    resultado = {
        "remitente": msg.get("From", ""),
        "destinatario": msg.get("To", ""),
        "asunto": msg.get("Subject", ""),
        "fecha": msg.get("Date", ""),
        "message_id": msg.get("Message-ID", ""),
        "return_path": msg.get("Return-Path", ""),
        "received": msg.get_all("Received", []),
        "autenticacion": _auth_results(msg),
        "cuerpo": cuerpo[:8000],
        "adjuntos": adjuntos,
    }

    # Guarda los HECHOS en el store (el dictamen los toma de aquí, no del LLM).
    datos_eml = ruta.read_bytes()
    context.EVIDENCIA["correo"] = {
        "evidencia": ruta.name,
        "tamano_bytes": len(datos_eml),
        "sha256": _sha256(datos_eml),
        "md5": hashlib.md5(datos_eml).hexdigest(),
        "remitente": resultado["remitente"],
        "destinatario": resultado["destinatario"],
        "asunto": resultado["asunto"],
        "fecha": resultado["fecha"],
        "return_path": resultado["return_path"],
        "message_id": resultado["message_id"],
        "autenticacion": resultado["autenticacion"],
    }
    context.EVIDENCIA["adjuntos"] = [dict(a) for a in adjuntos]
    return resultado


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
