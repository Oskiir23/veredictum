"""Análisis estático de adjuntos y consulta a VirusTotal."""

import hashlib
from pathlib import Path

from .. import context
from ..config import VT_API_KEY

# Firmas de cabecera (magic bytes) para identificar el tipo real, no la extensión.
_FIRMAS = {
    b"MZ": "ejecutable_PE",
    b"PK\x03\x04": "zip_u_ofimatica_moderna",  # docx/xlsx/pptx/zip
    b"\xd0\xcf\x11\xe0": "ofimatica_OLE",  # doc/xls/ppt antiguos
    b"%PDF": "pdf",
    b"\x7fELF": "ejecutable_ELF",
}


def _hashes(datos: bytes) -> dict:
    return {
        "md5": hashlib.md5(datos).hexdigest(),
        "sha1": hashlib.sha1(datos).hexdigest(),
        "sha256": hashlib.sha256(datos).hexdigest(),
    }


def _tipo_real(datos: bytes) -> str:
    for firma, tipo in _FIRMAS.items():
        if datos.startswith(firma):
            return tipo
    return "desconocido"


def _analizar_macros(ruta: str) -> dict:
    """Usa olevba (oletools) para detectar y volcar macros VBA sospechosas."""
    try:
        from oletools.olevba import VBA_Parser
    except ImportError:
        return {"macros": "oletools_no_instalado"}

    try:
        vp = VBA_Parser(ruta)
        if not vp.detect_vba_macros():
            vp.close()
            return {"macros": "sin_macros"}

        indicadores, codigo = [], []
        for _, _, _, vba in vp.extract_macros():
            codigo.append(vba)
        for tipo, palabra, desc in vp.analyze_macros():
            indicadores.append({"tipo": tipo, "palabra_clave": palabra, "descripcion": desc})
        vp.close()
        return {
            "macros": "DETECTADAS",
            "indicadores": indicadores,
            "codigo_vba": ("\n".join(codigo))[:6000],
        }
    except Exception as e:  # noqa: BLE001
        return {"macros": "error", "detalle": str(e)}


def analyze_attachment(file_path: str) -> dict:
    """Analiza un adjunto en estático (NO lo ejecuta).

    Calcula MD5/SHA1/SHA256, identifica el tipo real por magic bytes (no por la
    extensión) y, si es un documento ofimático, extrae y analiza las macros VBA
    con olevba marcando indicadores sospechosos (AutoOpen, Shell, descargas, etc.).

    Args:
        file_path: Ruta al adjunto ya extraído (la da parse_email en 'ruta').
    """
    ruta = Path(file_path)
    if not ruta.exists():
        return {"error": f"No existe el adjunto: {file_path}"}

    datos = ruta.read_bytes()
    resultado = {
        "nombre": ruta.name,
        "tamano_bytes": len(datos),
        "tipo_real": _tipo_real(datos),
        "hashes": _hashes(datos),
    }
    if resultado["tipo_real"] in ("ofimatica_OLE", "zip_u_ofimatica_moderna"):
        resultado.update(_analizar_macros(str(ruta)))

    # Enriquece el adjunto correspondiente en el store (match por SHA-256).
    sha = resultado["hashes"]["sha256"]
    for adj in context.EVIDENCIA.get("adjuntos", []):
        if adj.get("sha256") == sha:
            adj.update(
                {
                    "tipo_real": resultado["tipo_real"],
                    "md5": resultado["hashes"]["md5"],
                    "sha1": resultado["hashes"]["sha1"],
                    "macros": resultado.get("macros", "sin_macros"),
                }
            )
            break
    return resultado


def vt_lookup(sha256: str) -> dict:
    """Consulta un hash SHA-256 en VirusTotal (solo el hash, nunca el fichero).

    Requiere VT_API_KEY en el .env. Sin clave devuelve 'no_consultado' para que
    el agente lo deje reflejado como pendiente de verificación humana.

    Args:
        sha256: Hash SHA-256 del fichero a consultar.
    """
    if not VT_API_KEY:
        res = {"estado": "no_consultado", "motivo": "sin VT_API_KEY en .env"}
        context.EVIDENCIA.setdefault("vt", {})[sha256] = res
        return res
    try:
        import vt

        with vt.Client(VT_API_KEY) as cliente:
            f = cliente.get_object(f"/files/{sha256}")
            stats = f.last_analysis_stats
            res = {
                "estado": "consultado",
                "deteccion": f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                "maliciosos": stats.get("malicious", 0),
                "nombre_comun": getattr(f, "meaningful_name", ""),
                "tipo": getattr(f, "type_description", ""),
            }
    except Exception as e:  # noqa: BLE001 — incluye 404 = no visto en VT
        res = {"estado": "error_o_no_encontrado", "detalle": str(e)}
    context.EVIDENCIA.setdefault("vt", {})[sha256] = res
    return res


def _top(lst, n):
    return (lst or [])[:n]


def vt_behaviour(sha256: str) -> dict:
    """Obtiene el COMPORTAMIENTO DINÁMICO observado en los sandboxes de VirusTotal.

    NO ejecuta el fichero en este equipo: recupera el resumen de la detonación que
    VirusTotal ya realizó en sus entornos (procesos creados, ficheros soltados,
    cambios en el registro, conexiones de red y técnicas MITRE ATT&CK). Requiere
    VT_API_KEY. Úsalo tras vt_lookup cuando el adjunto sea ejecutable/sospechoso.

    Args:
        sha256: Hash SHA-256 del fichero.
    """
    store = context.EVIDENCIA.setdefault("comportamiento", {})
    if not VT_API_KEY:
        store[sha256] = {"estado": "no_consultado", "motivo": "sin VT_API_KEY en .env"}
        return store[sha256]
    try:
        import vt

        with vt.Client(VT_API_KEY) as cliente:
            s = cliente.get_data(f"/files/{sha256}/behaviour_summary")
    except Exception as e:  # noqa: BLE001 — 404 = sin informe de comportamiento
        store[sha256] = {"estado": "sin_datos_o_error", "detalle": str(e)[:200]}
        return store[sha256]

    def _reg(r):
        return r.get("key", "") if isinstance(r, dict) else str(r)

    res = {
        "estado": "consultado",
        "fuente": "sandboxes de VirusTotal (detonación externa)",
        "procesos": _top(s.get("processes_created") or s.get("command_executions"), 15),
        "ficheros_soltados": [
            {"ruta": d.get("path", ""), "sha256": d.get("sha256", "")}
            for d in _top(s.get("files_dropped"), 10)
        ],
        "ficheros_escritos": _top(s.get("files_written"), 10),
        "registro": [_reg(r) for r in _top(s.get("registry_keys_set"), 15)],
        "ips": [
            f"{t.get('destination_ip', '')}:{t.get('destination_port', '')}"
            f"/{t.get('transport_layer_protocol', '')}"
            for t in _top(s.get("ip_traffic"), 10)
        ],
        "dns": [d.get("hostname", "") for d in _top(s.get("dns_lookups"), 10)],
        "mitre": [
            f"{m.get('id', '')} — {m.get('signature_description', '')}".strip(" —")
            for m in _top(s.get("mitre_attack_techniques"), 20)
        ],
    }
    store[sha256] = res
    return res
