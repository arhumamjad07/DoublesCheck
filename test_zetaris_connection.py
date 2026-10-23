"""One-shot Zetaris SQL connection test. Never prints secrets."""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any

import requests
from dotenv import load_dotenv

TIMEOUT_SECONDS = 60
SKIP_KEYS = {
    "limit",
    "queryid",
    "query_id",
    "requestid",
    "request_id",
    "status",
    "code",
}


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required setting: {name}")
    return value


def _redact(text: str, secrets: list[str]) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def _is_one(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if value == 1:
        return True
    return isinstance(value, str) and value.strip() == "1"


def _result_contains_one(obj: Any) -> bool:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in SKIP_KEYS:
                continue
            if key.lower() == "one" and _is_one(value):
                return True
            if _result_contains_one(value):
                return True
        return False
    if isinstance(obj, list):
        return any(_result_contains_one(item) for item in obj)
    return _is_one(obj)


def main() -> None:
    load_dotenv()

    rest_url = _required_env("ZETARIS_REST_URL").rstrip("/")
    org_id = _required_env("ZETARIS_ORG_ID")
    api_key = _required_env("ZETARIS_API_KEY")
    secrets = [api_key, org_id]
    url = f"{rest_url}/sql-editor/sqls/run"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Org-ID": org_id,
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    payload = {
        "queryId": str(uuid.uuid4()),
        "sql": "SELECT 1 AS one",
        "source": "SqlEditor",
        "limit": 1,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if not _result_contains_one(data):
            print("Query succeeded but the result did not contain 1.", file=sys.stderr)
            raise SystemExit(1)
        print("PASS")
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        body = ""
        if exc.response is not None:
            body = _redact(exc.response.text, secrets)
        print(
            f"Request failed with HTTP {status}.\n{_redact(str(exc), secrets)}",
            file=sys.stderr,
        )
        if body:
            print(f"Response body: {body}", file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(_redact(str(exc), secrets), file=sys.stderr)
        raise SystemExit(1)
    except (ValueError, TypeError) as exc:
        print(
            f"Unexpected response shape: {_redact(str(exc), secrets)}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
