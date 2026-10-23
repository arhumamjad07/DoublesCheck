"""One-shot Meterless Nightshift connection test. Never prints secrets."""

from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv

TIMEOUT_SECONDS = 60


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


def main() -> None:
    from credit_policy import require_model_opt_in
    require_model_opt_in()
    load_dotenv()

    base_url = _required_env("METERLESS_BASE_URL").rstrip("/")
    token = _required_env("METERLESS_RUNTIME_TOKEN")
    model = _required_env("METERLESS_MODEL")
    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "meterless-app": "hackathon-setup-test",
        "meterless-scope": "user",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word: ready"}],
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
        reply = data["choices"][0]["message"]["content"]
        print(f"Model reply: {reply}")
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        body = ""
        if exc.response is not None:
            body = _redact(exc.response.text, [token])
        print(
            f"Request failed with HTTP {status}.\n{_redact(str(exc), [token])}",
            file=sys.stderr,
        )
        if body:
            print(f"Response body: {body}", file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(_redact(str(exc), [token]), file=sys.stderr)
        raise SystemExit(1)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        print(
            f"Unexpected response shape: {_redact(str(exc), [token])}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
