#!/usr/bin/env python3
"""Read the delegation judge selection once; the caller retains it for the task."""

import os
from pathlib import Path
import subprocess
import sys


VALID_MODELS = {"clef", "jev", "none"}


def common_config_path(environ=None):
    env = os.environ if environ is None else environ
    home = Path(env["HOME"]) if env.get("HOME") else Path.home()
    return home / ".config" / "gwitg" / "decision-model"


def project_root(cwd=None):
    working_directory = Path.cwd() if cwd is None else Path(cwd)
    working_directory = working_directory.resolve()
    git_env = os.environ.copy()
    # These variables can redirect Git away from the repository containing cwd.
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
    return project_root(cwd) / ".gwitg" / "decision-model"


def read_value(path):
    value = path.read_text(encoding="utf-8").strip()
    if value not in VALID_MODELS:
        raise ValueError(f"{path}: expected exactly one of clef, jev, none")
    return value


def read_decision_model(environ=None, cwd=None):
    path = project_config_path(cwd)
    try:
        return read_value(path)
    except FileNotFoundError:
        path = common_config_path(environ)
    try:
        return read_value(path)
    except FileNotFoundError:
        return "none"


def main():
    try:
        print(read_decision_model())
    except (OSError, UnicodeError, ValueError) as error:
        print(f"gwitg decision-model: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
