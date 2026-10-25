"""Python adapter for the pinned Meterless H-MEM engine. No model calls or keys."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def node_executable():
    explicit = os.getenv("DOUBLES_CHECK_NODE")
    candidates = [explicit, shutil.which("node")]
    local = os.getenv("LOCALAPPDATA")
    if local:
        candidates.append(str(Path(local) / "Nightshift" / "node" / "node.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise RuntimeError("Node.js is required for H-MEM. Install Node 22+ or set DOUBLES_CHECK_NODE to node.exe.")


def recall_preferences(directory, profile="default", updates=None, *, locked=None):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", profile):
        raise ValueError("Profile must contain 1-64 letters, digits, underscores or hyphens.")
    bridge = Path(__file__).resolve().with_name("hmem-bridge.mjs")
    request = {"directory": str(Path(directory).resolve()), "profile": profile,
               "updates": updates or {}}
    if locked is not None: request["locked_species"] = locked
    # Do not pass service credentials to the child process at all.
    child_env = {key: value for key, value in os.environ.items()
                 if not any(secret in key.upper() for secret in ("TOKEN", "KEY", "PASSWORD", "SECRET"))}
    try:
        result = subprocess.run([node_executable(), str(bridge)],
                                input=json.dumps(request), text=True, encoding="utf-8",
                                capture_output=True, timeout=20, check=False, env=child_env)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("H-MEM bridge could not complete; no AI request sent.") from None
    if result.returncode:
        if "Preference conflicts with avoidance" in result.stderr:
            raise ValueError("A locked favourite conflicts with your remembered avoidance. Clear or change the avoided partner first; preferences were not updated.")
        raise RuntimeError("H-MEM could not load or save this profile. Check its state files and write access; no AI request sent.")
    try:
        memory = json.loads(result.stdout)
        if not isinstance(memory, dict) or not isinstance(memory.get("memories"), list):
            raise ValueError("invalid bridge result")
        return memory
    except (ValueError, TypeError):
        raise RuntimeError("H-MEM bridge returned invalid data.") from None
