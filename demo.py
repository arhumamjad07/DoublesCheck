"""DoublesCheck connection demo: real services, explicitly mock Pokemon data.

Install: python -m pip install requests python-dotenv
Run beside your project .env: python demo.py
Or: python demo.py --env-file "C:/path/to/project/.env"

One Zetaris query and two to four Nightshift requests. No transport retries.
The SQL CTE is query-scoped. Separate Builder/Evaluator calls use deterministic
type evidence, H-MEM preference recall and one bounded revision. No full legality check.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import uuid

import requests
from dotenv import load_dotenv


LOCKED_FAVOURITE = "Charizard"
TIMEOUT = (5, 150)  # Connection timeout, then response-read timeout.
SETTINGS = (
    "ZETARIS_REST_URL", "ZETARIS_ORG_ID", "ZETARIS_API_KEY",
    "METERLESS_BASE_URL", "METERLESS_RUNTIME_TOKEN", "METERLESS_MODEL",
)
COLUMNS = ("name", "type_primary", "type_secondary", "demo_role")

# Deliberately small illustrative records, not a verified VGC catalogue.
# This one statement defines, populates, and selects a temporary relation.
MOCK_SQL = """
WITH doublescheck_mock AS (
    SELECT 'Charizard' AS name, 'Fire' AS type_primary,
           'Flying' AS type_secondary, 'Favourite attacker' AS demo_role
    UNION ALL
    SELECT 'Venusaur', 'Grass', 'Poison', 'Candidate partner A'
    UNION ALL
    SELECT 'Blastoise', 'Water', 'None', 'Candidate partner B'
)
SELECT name, type_primary, type_secondary, demo_role
FROM doublescheck_mock
ORDER BY name
"""


def required_settings() -> dict[str, str]:
    values = {key: os.getenv(key, "").strip() for key in SETTINGS}
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise ValueError("Missing settings: " + ", ".join(missing))
    return values


def post_json(session, label, url, headers, payload):
    try:
        response = session.post(
            url, headers=headers, json=payload, timeout=TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException:
        # Do not print exception details, headers, or echoed credentials.
        raise RuntimeError(
            f"{label}: connection failed or timed out. Check the service is "
            "running and the URL is correct. No retry was sent."
        ) from None
    if not 200 <= response.status_code < 300:
        raise RuntimeError(
            f"{label}: HTTP {response.status_code}. Check credentials, access, "
            "and service logs. Response body omitted to protect secrets."
        )
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(f"{label}: response was not JSON.") from None
    if not isinstance(result, dict):
        raise RuntimeError(f"{label}: expected a JSON object.")
    return result


def fetch_catalogue(session, settings):
    result = post_json(
        session, "Zetaris",
        settings["ZETARIS_REST_URL"].rstrip("/") + "/sql-editor/sqls/run",
        {
            "Authorization": "Bearer " + settings["ZETARIS_API_KEY"],
            "X-Org-ID": settings["ZETARIS_ORG_ID"],
            "X-Request-ID": str(uuid.uuid4()),
        },
        {
            "queryId": str(uuid.uuid4()), "sql": MOCK_SQL,
            "source": "SqlEditor", "limit": 3,
        },
    )
    rows = result.get("data")
    if not isinstance(rows, list) or len(rows) != 3:
        raise RuntimeError("Zetaris: expected exactly three rows in 'data'.")
    catalogue = []
    for row in rows:
        if isinstance(row, dict) and all(key in row for key in COLUMNS):
            catalogue.append({key: row[key] for key in COLUMNS})
        elif isinstance(row, list) and len(row) == len(COLUMNS):
            catalogue.append(dict(zip(COLUMNS, row)))
        else:
            raise RuntimeError("Zetaris: unexpected catalogue row structure.")
    names = {row["name"] for row in catalogue}
    if names != {"Charizard", "Venusaur", "Blastoise"}:
        raise RuntimeError("Zetaris: returned catalogue did not match the mock data.")
    return catalogue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path,
                        default=Path(__file__).resolve().with_name(".env"))
    parser.add_argument("--favourite", default=None,
                        choices=["Charizard", "Venusaur", "Blastoise"])
    parser.add_argument("--profile", default="default")
    parser.add_argument("--avoid-partner", choices=["Charizard", "Venusaur", "Blastoise"])
    parser.add_argument("--allow-all-partners", action="store_true")
    parser.add_argument("--memory-only", action="store_true", help="Save/recall preferences without any service calls")
    parser.add_argument("--memory-dir", type=Path, default=Path(__file__).resolve().parent / ".doublescheck-memory")
    args = parser.parse_args()
    if args.avoid_partner and args.allow_all_partners:
        parser.error("Choose avoidance or clearing avoidance, not both.")
    from hmem_memory import recall_preferences
    updates = {}
    if args.favourite:
        updates["favourite"] = args.favourite
    if args.avoid_partner:
        updates["avoided_partner"] = args.avoid_partner
    if args.allow_all_partners:
        updates["avoided_partner"] = None
    memory = recall_preferences(args.memory_dir, args.profile, updates)
    favourite = memory.get("favourite", "Charizard")
    print(f"H-MEM: recalled {len(memory['memories'])} preference(s) for {args.profile}.", flush=True)
    if args.memory_only:
        print(json.dumps(memory, indent=2))
        return
    if args.env_file.is_file():
        load_dotenv(args.env_file)  # Existing shell variables take precedence.
    settings = required_settings()
    print("DoublesCheck: MOCK DATA connection demo; no verified VGC regulation.")
    from coaching import run_demo
    with requests.Session() as session:
        catalogue = fetch_catalogue(session, settings)
        print("PASS: retrieved three mock records through Zetaris.", flush=True)
        run_demo(session, settings, catalogue, favourite, post_json,
                 Path(__file__).resolve().parent / "logs", memory=memory)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
