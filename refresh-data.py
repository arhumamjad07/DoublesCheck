"""Rebuild the pinned public snapshot. Downloads public data only; no AI/API credits."""
import hashlib
import json
from pathlib import Path
import runpy
import urllib.request

from catalogue import ROOT, run_showdown

if __name__ == "__main__":
    sources = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))["sources"]
    source = next(s for s in sources if "Smogon November" in s["title"])
    with urllib.request.urlopen(source["url"], timeout=90) as response:
        payload = response.read(25_000_001)
    if len(payload) > 25_000_000 or hashlib.sha256(payload).hexdigest() != source["sha256"]:
        raise RuntimeError("Public snapshot hash changed. Existing data was not replaced; review the source first.")
    filename = ROOT / "usage-original.json"
    filename.write_bytes(payload)
    print(run_showdown({"operation": "generate", "usageFile": str(filename), "output": str(ROOT / "data/catalogue.json")}))
    runpy.run_path(str(ROOT / "prepare-data.py"), run_name="__main__")
