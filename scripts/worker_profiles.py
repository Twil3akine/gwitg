#!/usr/bin/env python3
"""Resolve named worker profiles to concrete model and reasoning settings."""

import json
import os
from pathlib import Path
import subprocess
import sys


DEFAULT_PROFILE = "standard"
DEFAULT_PROFILES = {
    "light": {"model": "6-luna", "reasoning_effort": "low"},
    "standard": {"model": "6-luna", "reasoning_effort": "high"},
    "strong": {"model": "6-astra", "reasoning_effort": "high"},
}


def common_config_path(environ=None):
    env = os.environ if environ is None else environ
    home = Path(env["HOME"]) if env.get("HOME") else Path.home()
    return home / ".config" / "gwitg" / "worker-profiles.json"


def project_root(cwd=None):
    working_directory = Path.cwd() if cwd is None else Path(cwd)
    working_directory = working_directory.resolve()
    git_env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        git_env.pop(name, None)
    try:
        result = subprocess.run(
            ["git", "-C", str(working_directory), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            env=git_env,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return working_directory
    return Path(result.stdout.rstrip("\r\n"))


def project_config_path(cwd=None):
    return project_root(cwd) / ".gwitg" / "worker-profiles.json"


def _validate_profiles(profiles, path="worker profiles"):
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError(f"{path}: expected a non-empty object of profiles")
    for name, settings in profiles.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"{path}: profile names must be non-empty strings")
        if not isinstance(settings, dict):
            raise ValueError(f"{path}: profile {name!r} must be an object")
        model = settings.get("model")
        effort = settings.get("reasoning_effort")
        if not isinstance(model, str) or not model.strip():
            raise ValueError(f"{path}: profile {name!r} needs a non-empty model")
        if not isinstance(effort, str) or not effort.strip():
            raise ValueError(
                f"{path}: profile {name!r} needs a non-empty reasoning_effort"
            )
        if set(settings) != {"model", "reasoning_effort"}:
            raise ValueError(
                f"{path}: profile {name!r} must contain only model and reasoning_effort"
            )
    return profiles


def read_profiles(environ=None, cwd=None):
    path = common_config_path(environ)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        path = project_config_path(cwd)
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {name: settings.copy() for name, settings in DEFAULT_PROFILES.items()}
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON: {error.msg}") from error
    if not isinstance(document, dict) or set(document) != {"profiles"}:
        raise ValueError(f"{path}: expected an object containing only profiles")
    return _validate_profiles(document["profiles"], str(path))


def resolve_worker_profile(profile=None, environ=None, cwd=None):
    """Return the concrete settings for profile, defaulting to standard.

    Custom model and effort strings are returned unchanged. This resolver does
    not select a fallback for configurations the runtime may not support.
    """
    selected = DEFAULT_PROFILE if profile is None else profile
    if not isinstance(selected, str) or not selected:
        raise ValueError("profile must be a non-empty string")
    profiles = read_profiles(environ, cwd)
    try:
        return profiles[selected].copy()
    except KeyError as error:
        available = ", ".join(sorted(profiles))
        raise ValueError(
            f"unknown worker profile {selected!r}; available profiles: {available}"
        ) from error


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else None
    if len(sys.argv) > 2:
        print("usage: worker_profiles.py [profile]", file=sys.stderr)
        return 2
    try:
        print(json.dumps(resolve_worker_profile(profile), sort_keys=True))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"gwitg worker-profiles: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
