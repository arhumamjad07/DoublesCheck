"""Deterministic relational projection of the existing pinned public snapshot.

No download or enrichment. Original encoded tables and offline catalogue remain unchanged.
"""
import csv
import hashlib
import json
from pathlib import Path

from catalogue import ROOT
from evidence_lens import FORMAT, MONTH, CUTOFF, BATTLES

VERSION = 1
DATABASE = "DOUBLES_CHECK_LENS"
DESTINATION = "/home/zetaris/customer-data/shared/doublescheck-evidence-v1"
FIELDS = {
    "pokemon_facts": ["name", "species_id", "base_species", "type_1", "type_2", "eligible", "set_count"],
    "usage_snapshots": ["name", "format_id", "snapshot_month", "cutoff", "usage", "raw_count"],
    "teammate_relationships": ["favourite", "favourite_id", "partner", "format_id", "snapshot_month", "cutoff", "association_weight"],
    "sourced_sets": ["set_id", "name", "format_id", "snapshot_month", "cutoff", "ability", "item", "nature", "tera_type", "level",
                     "move_1", "move_2", "move_3", "move_4"] + ["ev_"+s for s in ("hp","atk","def","spa","spd","spe")] +
                    ["iv_"+s for s in ("hp","atk","def","spa","spd","spe")] + ["ability_share","item_share","spread_share","set_sha256"],
    "source_metadata": ["schema_version", "format_id", "snapshot_month", "cutoff", "battles", "catalogue_sha256", "usage_sha256", "showdown_version"],
}


def set_digest(option):
    return hashlib.sha256(json.dumps(option, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def project(data, root=ROOT):
    """Row grains and field order are explicit; no arbitrary JSON fields enter CSV."""
    result = {table: [] for table in FIELDS}
    with (root / "data/zetaris/vgc_usage/data.csv").open(encoding="utf-8", newline="") as handle:
        usage_names = {r["name"] for r in csv.DictReader(handle)}
    for name, mon in sorted(data["species"].items()):
        result["pokemon_facts"].append([name, mon["id"], mon["base_species"], mon["types"][0],
                                         mon["types"][1] if len(mon["types"]) > 1 else "none", int(mon["eligible_species"]), len(mon["sets"])])
        if name in usage_names:
            result["usage_snapshots"].append([name, FORMAT, MONTH, CUTOFF, mon["usage"], mon["raw_count"]])
        for partner, weight in sorted(mon["teammate_weights"].items()):
            result["teammate_relationships"].append([name, mon["id"], partner, FORMAT, MONTH, CUTOFF, weight])
        for i, option in enumerate(mon["sets"]):
            evidence = option["evidence"]
            result["sourced_sets"].append([mon["id"]+":"+str(i), name, FORMAT, MONTH, CUTOFF,
                option["ability"], option["item"], option["nature"], option["teraType"], option["level"], *option["moves"],
                *[option["evs"][s] for s in ("hp","atk","def","spa","spd","spe")],
                *[option["ivs"][s] for s in ("hp","atk","def","spa","spd","spe")],
                evidence["ability_share"], evidence["item_share"], evidence["spread_share"], set_digest(option)])
    sources = json.loads((root / "data/sources.json").read_text(encoding="utf-8"))
    result["source_metadata"].append([VERSION, FORMAT, MONTH, CUTOFF, BATTLES,
        hashlib.sha256((root / "data/catalogue.json").read_bytes()).hexdigest(), sources["sources"][2]["sha256"], "0.11.11"])
    return result


def prepare(root=ROOT):
    catalogue = root / "data/catalogue.json"
    original = json.loads((root / "data/sources.json").read_text(encoding="utf-8"))
    if hashlib.sha256(catalogue.read_bytes()).hexdigest() != original["files"]["data/catalogue.json"]:
        raise RuntimeError("Pinned catalogue hash mismatch; normalisation stopped.")
    data = json.loads(catalogue.read_text(encoding="utf-8"))
    if data["format_id"] != FORMAT or data["statistics"]["cutoff"] != CUTOFF or data["statistics"]["number of battles"] != BATTLES:
        raise RuntimeError("Pinned historical scope mismatch.")
    rows = project(data, root)
    tables = {}
    for table, values in rows.items():
        file = root / "data/zetaris-lens" / table / "data.csv"
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(FIELDS[table]); writer.writerows(values)
        tables[table] = {"rows": len(values), "sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "columns": FIELDS[table]}
    manifest = {"schema_version": VERSION, "format_id": FORMAT, "snapshot": MONTH, "cutoff": CUTOFF,
                "catalogue_sha256": original["files"]["data/catalogue.json"],
                "usage_sha256": original["sources"][2]["sha256"], "tables": tables}
    (root / "data/zetaris-lens/manifest.json").write_text(json.dumps(manifest, indent=2)+"\n",encoding="utf-8")
    return manifest


if __name__ == "__main__":
    manifest = prepare()
    print("Normalised existing snapshot:", {k:v["rows"] for k,v in manifest["tables"].items()})
