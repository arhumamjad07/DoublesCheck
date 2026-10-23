"""Prepare the downloaded historical data for local sample mode and Zetaris."""
import base64
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))
def encode(obj):
    return base64.b64encode(json.dumps(obj, separators=(",", ":")).encode()).decode()
def save(folder, rows):
    directory = ROOT / "data/zetaris" / folder
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "data.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "record_b64"])
        writer.writerows(rows)

data = read("data/catalogue.json")
original = read("usage-original.json")
base, usage = [], []
for name, mon in data["species"].items():
    history_keys = ["usage", "raw_count", "teammate_weights", "sets"]
    base.append([name, encode({k: v for k, v in mon.items() if k not in history_keys})])
    if name in original["data"]:
        usage.append([name, encode({k: mon[k] for k in history_keys})])
save("pokedex", base)
save("vgc_usage", usage)
save("reference", [["metadata", encode({k: v for k, v in data.items() if k != "species"})]])
history = read("historical-formats-source.json")
manifest = {
    "retrieved_date": "2026-10-23", "format_id": data["format_id"],
    "format_scope": "Historical Scarlet/Violet VGC Regulation H, November 2024 ladder. Not current 2026 rules.",
    "sources": [
        {"title": "Pokemon Showdown dex and validator", "url": "https://github.com/smogon/pokemon-showdown", "package": "pokemon-showdown@0.11.11", "license": "MIT"},
        {"title": "Historical Showdown format definition", **history, "license": "MIT"},
        {"title": "Smogon November 2024 VGC Regulation H ladder statistics", "url": "https://www.smogon.com/stats/2024-11/chaos/gen9vgc2024regh-1500.json",
         "sha256": hashlib.sha256((ROOT / "usage-original.json").read_bytes()).hexdigest(),
         "battles": original["info"]["number of battles"], "cutoff": 1500,
         "interpretation": "Aggregate weighted ladder usage, not official tournament history or a win-rate predictor."},
        {"title": "Official Pokemon Regulation H announcement", "url": "https://sv-news.pokemon.co.jp/en/page/245.html"}],
    "files": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / "data").rglob("*") if p.is_file() and p.name != "sources.json"}}
(ROOT / "data/sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Prepared Zetaris source rows: {len(base)} Pokedex, {len(usage)} historical usage, 1 reference.")
