#!/usr/bin/env python3
"""Resolve named worker profiles to concrete model and reasoning settings."""

import json
import importlib.util
import os
from pathlib import Path
import sys


DEFAULT_PROFILE = "standard"
DEFAULT_PROFILES = {
    "light": {"model": "6-luna", "reasoning_effort": "low"},
    "standard": {"model": "6-luna", "reasoning_effort": "high"},
    "strong": {"model": "6-astra", "reasoning_effort": "high"},
}


class InvalidJudgeResult(ValueError):
    """The judge result does not match the common result contract."""


# Reuse the repository-root lookup already used by the delegation-judge resolver.
_DECISION_MODEL_PATH = Path(__file__).with_name("decision_model.py")
_DECISION_MODEL_SPEC = importlib.util.spec_from_file_location(
    "gwitg_decision_model", _DECISION_MODEL_PATH
)
_DECISION_MODEL = importlib.util.module_from_spec(_DECISION_MODEL_SPEC)
_DECISION_MODEL_SPEC.loader.exec_module(_DECISION_MODEL)
project_root = _DECISION_MODEL.project_root


def common_config_path(environ=None):
    env = os.environ if environ is None else environ
    home = Path(env["HOME"]) if env.get("HOME") else Path.home()
    return home / ".config" / "gwitg" / "worker-profiles.json"


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


def resolve_worker_profile(profile=None, environ=None, cwd=None, judge_result=None):
    """Return the concrete settings for profile, defaulting to standard.

    An explicit profile takes precedence over a judge result. Without an
    explicit profile, a valid positive judge recommendation selects its
    configured profile. A valid negative recommendation returns None. An
    absent judge result uses the standard profile.

    Custom model and effort strings are returned unchanged. This resolver does
    not select a fallback for configurations the runtime may not support.
    """
    selected = profile
    if selected is None and judge_result is not None:
        selected = _recommended_profile(judge_result)
        if selected is None:
            return None
    if selected is None:
        selected = DEFAULT_PROFILE
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


def _recommended_profile(result):
    """Validate a common judge result and return its profile recommendation."""
    if not isinstance(result, dict) or set(result) != {"delegate", "profile", "reason"}:
        raise InvalidJudgeResult(
            "judge result must contain only delegate, profile, and reason"
        )
    delegate = result["delegate"]
    profile = result["profile"]
    reason = result["reason"]
    if type(delegate) is not bool:
        raise InvalidJudgeResult("judge result delegate must be a boolean")
    if not isinstance(reason, str) or not reason.strip():
        raise InvalidJudgeResult("judge result reason must be a non-empty string")
    if delegate:
        if not isinstance(profile, str) or not profile:
            raise InvalidJudgeResult(
                "judge result profile must be a non-empty string when delegate is true"
            )
        return profile
    if profile is not None:
        raise InvalidJudgeResult(
            "judge result profile must be null when delegate is false"
        )
    return None


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
