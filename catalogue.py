"""Real data adapters. Sample mode is explicit; Zetaris failures never silently fall back."""
import base64
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlparse
import uuid

ROOT = Path(__file__).resolve().parent

def run_showdown(request):
    from hmem_memory import node_executable
    clean_env = {k: v for k, v in os.environ.items()
                 if not any(s in k.upper() for s in ("TOKEN", "KEY", "PASSWORD", "SECRET"))}
    try:
        result = subprocess.run([node_executable(), str(ROOT / "showdown-bridge.cjs")],
                                input=json.dumps(request), capture_output=True, text=True,
                                encoding="utf-8", env=clean_env, timeout=45)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("The local Showdown validator could not run. Check Node and npm dependencies.") from None
    if result.returncode:
        raise RuntimeError("Local Showdown validation failed. No model or paid service was called.")
    return json.loads(result.stdout)

class Zetaris:
    def __init__(self, env_file=None):
        import requests
        from dotenv import dotenv_values
        values = dotenv_values(env_file or ROOT / ".env")
        self.base = os.environ.get("ZETARIS_REST_URL", values.get("ZETARIS_REST_URL") or "").rstrip("/")
        self.key = os.environ.get("ZETARIS_API_KEY", values.get("ZETARIS_API_KEY") or "")
        self.org = os.environ.get("ZETARIS_ORG_ID", values.get("ZETARIS_ORG_ID") or "1")
        if not self.base or not self.key:
            raise RuntimeError("Zetaris settings are missing. Use --sample to run without credentials.")
        parsed = urlparse(self.base)
        if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1") or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise RuntimeError("No-credit mode permits only a local Zetaris endpoint.")
        self.session = requests.Session()
        self.session.trust_env = False

    def query(self, sql, limit=2000):
        import requests
        try:
            response = self.session.post(self.base + "/sql-editor/sqls/run",
                headers={"Authorization": "Bearer " + self.key, "X-Org-ID": self.org,
                         "X-Request-ID": str(uuid.uuid4())},
                json={"queryId": str(uuid.uuid4()), "sql": sql, "source": "SqlEditor", "limit": limit},
                timeout=(5, 90), allow_redirects=False)
            if not response.ok:
                # Permit idempotent CREATE handling without exposing response bodies or keys.
                if "already exist" in response.text.lower():
                    raise FileExistsError("Zetaris object already exists.")
                raise RuntimeError(f"Zetaris returned HTTP {response.status_code}. Check the query engine and data registration.")
            try: doc = response.json()
            except ValueError:
                raise RuntimeError("Zetaris returned invalid JSON; result withheld.") from None
        except requests.RequestException:
            raise RuntimeError("Local Zetaris did not respond. Start Docker/Zetaris or choose --sample explicitly.") from None
        if not isinstance(doc, dict) or not isinstance(doc.get("data"), list):
            raise RuntimeError("Unexpected Zetaris SQL result. No fallback or model call was made.")
        return doc["data"]

def decode(value):
    if value is None:
        return None
    try:
        return json.loads(base64.b64decode(value, validate=True))
    except (ValueError, TypeError):
        raise RuntimeError("Registered catalogue record is corrupt; rebuild data registration.") from None

def load_catalogue(sample=False, env_file=None):
    if sample:
        return json.loads((ROOT / "data/catalogue.json").read_text(encoding="utf-8")), "bundled sample snapshot"
    api = Zetaris(env_file)
    try:
        from evidence_lens import measured_query
        receipts = []
        rows = measured_query(api, "SELECT p.name, p.record_b64, u.record_b64 FROM DOUBLES_CHECK.pokedex p "
                         "LEFT JOIN DOUBLES_CHECK.vgc_usage u ON p.name = u.name ORDER BY p.name",
                         "catalogue_join", ["pokedex", "vgc_usage"], receipts)
        meta = measured_query(api, "SELECT record_b64 FROM DOUBLES_CHECK.reference WHERE name = 'metadata'",
                              "historical_reference", ["reference"], receipts, limit=2)
        expected = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
        if len(rows) != 1417 or len(meta) != 1:
            raise RuntimeError("Zetaris returned an incomplete catalogue; expected 1417 species/form rows.")
        data = decode(meta[0][0])
        if not isinstance(data, dict):
            raise RuntimeError("Malformed Zetaris reference metadata; result withheld.")
        if data["format_id"] != expected["format_id"]:
            raise RuntimeError("Zetaris catalogue and historical ruleset do not match.")
        if data.get("schema", 1) < 2:
            raise RuntimeError("Zetaris still has the older set snapshot. Run register-data.py to refresh DoublesCheck's dedicated files, then retry.")
        data["species"] = {}
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) != 3:
                raise RuntimeError("Malformed Zetaris catalogue row; result withheld.")
            name, dex_record, usage_record = row
            mon = decode(dex_record)
            history = decode(usage_record) if usage_record is not None else {"usage": 0, "raw_count": 0, "teammate_weights": {}, "sets": []}
            if not isinstance(mon, dict) or not isinstance(history, dict):
                raise RuntimeError("Malformed Zetaris species data; result withheld.")
            mon.update(history)
            if mon["name"] != name or name in data["species"]:
                raise RuntimeError("Zetaris returned inconsistent species identifiers.")
            data["species"][name] = mon
        # Live rows must represent the exact pinned snapshot, not merely its format label.
        pinned = json.loads((ROOT / "data/catalogue.json").read_text(encoding="utf-8"))
        if data != pinned:
            raise RuntimeError("Zetaris data differs from the pinned historical snapshot; refresh registration before continuing.")
        data["evidence_lens"] = {"receipts": receipts, "catalogue_rows": len(rows),
            "usage_rows": sum(1 for row in rows if row[2] is not None),
            "set_options": sum(len(mon["sets"]) for mon in data["species"].values()), "sql_ranking": False}
        return data, "Zetaris: joined Pokedex and historical VGC usage"
    finally:
        api.session.close()
