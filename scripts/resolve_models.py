#!/usr/bin/env python3
"""Resolve fixed Worker/Author settings for a gwitg runtime."""

import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULTS = {
    "codex-native": {
        "worker": {"model": "6-luna", "reasoning_effort": "high"},
        "author": {"model": "6.1-sol", "reasoning_effort": "medium"},
    },
    "codex-cli": {
        "worker": {"model": "gpt-6-luna", "reasoning_effort": "high"},
    },
}
RUNTIME_RE = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")


class ConfigError(Exception):
    pass


def _object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_json_constant(value):
    raise ConfigError(f"invalid JSON constant: {value}")


def _project_root(start):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return start
    return Path(result.stdout.strip()) if result.stdout.strip() else start


def _read_config(path):
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(
                stream,
                object_pairs_hook=_object_no_duplicates,
                parse_constant=_reject_non_json_constant,
            )
    except ConfigError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read configuration {path}: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {"runtimes"}:
        raise ConfigError("top-level object must contain only 'runtimes'")
    runtimes = data["runtimes"]
    if not isinstance(runtimes, dict):
        raise ConfigError("'runtimes' must be an object")
    for runtime_name, roles in runtimes.items():
        if not isinstance(runtime_name, str) or not RUNTIME_RE.fullmatch(runtime_name):
            raise ConfigError(f"invalid runtime name: {runtime_name!r}")
        if (not isinstance(roles, dict) or not roles
                or not set(roles) <= {"worker", "author"}):
            raise ConfigError(f"runtime {runtime_name!r} must define worker, author, or both")
        for role, settings in roles.items():
            if not isinstance(settings, dict) or set(settings) != {"model", "reasoning_effort"}:
                raise ConfigError(f"{runtime_name}.{role} must define only model and reasoning_effort")
            if any(not isinstance(settings[key], str) or not settings[key].strip()
                   for key in ("model", "reasoning_effort")):
                raise ConfigError(f"{runtime_name}.{role} values must be non-empty strings")
    return runtimes


def resolve(runtime, role, start=None, home=None):
    if not isinstance(runtime, str) or not RUNTIME_RE.fullmatch(runtime):
        raise ConfigError("runtime must use lowercase letters, digits, '.', '_' or '-' and start with a letter or digit")
    if role not in ("worker", "author"):
        raise ConfigError("role must be 'worker' or 'author'")

    start = Path(start or Path.cwd()).resolve()
    home = Path(home or Path.home()).expanduser()
    project_file = _project_root(start) / ".gwitg" / "models.json"
    user_file = home / ".config" / "gwitg" / "models.json"
    selected = project_file if project_file.exists() else user_file if user_file.exists() else None

    configured = {}
    if selected is not None:
        runtimes = _read_config(selected)
        configured = runtimes.get(runtime, {})

    settings = configured.get(role) or DEFAULTS.get(runtime, {}).get(role)
    if settings is None:
        return {"runtime": runtime, "role": role, "status": "unavailable"}

    return {
        "runtime": runtime,
        "role": role,
        "status": "resolved",
        "model": settings["model"],
        "reasoning_effort": settings["reasoning_effort"],
    }


def main(argv):
    if len(argv) != 3:
        print("usage: resolve_models.py RUNTIME worker|author", file=sys.stderr)
        return 2
    try:
        result = resolve(argv[1], argv[2])
    except ConfigError as exc:
        print(f"resolve_models.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "resolved" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
