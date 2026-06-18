"""Herramientas forenses que el agente puede invocar."""

from .attachment_tools import analyze_attachment, vt_behaviour, vt_lookup
from .email_tools import extract_iocs, parse_email

# write_report depende de python-docx + Node; en la VM aislada no está disponible.
# Se importa de forma tolerante para que el extractor offline pueda usar el resto.
try:
    from .report_tools import write_report

    HERRAMIENTAS = [
        parse_email, extract_iocs, analyze_attachment, vt_lookup, vt_behaviour, write_report,
    ]
except ImportError:
    write_report = None
    HERRAMIENTAS = [parse_email, extract_iocs, analyze_attachment, vt_lookup, vt_behaviour]
