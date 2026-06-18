"""Comprueba si la VT key (free) da acceso a datos de COMPORTAMIENTO (dinámico)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vt

from veredictum.config import VT_API_KEY

SHA = "72c3ce7925693b6151f39fea70436ab32fee2fe50db39b09f1a3709f340907f8"

with vt.Client(VT_API_KEY) as c:
    try:
        s = c.get_data(f"/files/{SHA}/behaviour_summary")
        print("BEHAVIOUR_SUMMARY: ACCESIBLE (free tier OK)")
        for k in ("processes_created", "files_written", "files_dropped",
                  "registry_keys_set", "ip_traffic", "dns_lookups",
                  "mitre_attack_techniques"):
            v = s.get(k)
            if v:
                print(f"  {k}: {len(v)} entradas")
    except vt.APIError as e:
        print(f"BEHAVIOUR_SUMMARY: NO accesible -> {e.code}: {e.message[:120]}")
