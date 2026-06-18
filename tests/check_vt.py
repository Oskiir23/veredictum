"""Prueba el lookup de VirusTotal con el hash del adjunto del caso real."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from veredictum.tools.attachment_tools import vt_lookup

SHA = "72c3ce7925693b6151f39fea70436ab32fee2fe50db39b09f1a3709f340907f8"
print(vt_lookup(SHA))
