#!/usr/bin/env python3
"""Read the delegation judge selection once; the caller retains it for the task."""

import os
from pathlib import Path
import sys


VALID_MODELS = {"clef", "jev", "none"}


def config_path(environ=None):
    env = os.environ if environ is None else environ
    configured = env.get("XDG_CONFIG_HOME")
    if configured:
        root = Path(configured)
        if not root.is_absolute():
            raise ValueError("XDG_CONFIG_HOME must be an absolute path")
    else:
        root = Path(env["HOME"]) if env.get("HOME") else Path.home()
        root = root / ".config"
    return root / "gwitg" / "decision-model"


def read_decision_model(environ=None):
    path = config_path(environ)
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "none"
    if value not in VALID_MODELS:
        raise ValueError(f"{path}: expected exactly one of clef, jev, none")
    return value


def main():
    try:
        print(read_decision_model())
    except (OSError, UnicodeError, ValueError) as error:
        print(f"gwitg decision-model: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
