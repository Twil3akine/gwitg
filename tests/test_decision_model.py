import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "decision_model.py"
spec = importlib.util.spec_from_file_location("decision_model", SCRIPT)
decision_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision_model)


class DecisionModelTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.cwd = self.root / "work"
        self.cwd.mkdir()
        self.home = self.root / "home"
        self.env = {"HOME": str(self.home)}

    def write_config(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    def write_common_config(self, value):
        return self.write_config(
            self.home / ".config" / "gwitg" / "decision-model", value
        )

    def write_project_config(self, value, root=None):
        root = self.cwd if root is None else Path(root)
        return self.write_config(root / ".gwitg" / "decision-model", value)

    def read(self, cwd=None):
        return decision_model.read_decision_model(self.env, self.cwd if cwd is None else cwd)

    def init_git(self, path):
        env = os.environ.copy()
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
            env.pop(name, None)
        subprocess.run(["git", "init", "--quiet", str(path)], check=True, env=env)

    def test_missing_common_and_project_configuration_uses_none(self):
        self.assertEqual(self.read(), "none")

    def test_common_configuration_has_precedence(self):
        self.write_common_config(b"clef\n")
        self.write_project_config(b"jev\n")
        self.assertEqual(self.read(), "clef")

    def test_common_none_takes_precedence_over_project_value(self):
        self.write_common_config(b"none\n")
        self.write_project_config(b"clef\n")
        self.assertEqual(self.read(), "none")

    def test_project_configuration_is_used_when_common_file_is_missing(self):
        self.write_project_config(b"jev\n")
        self.assertEqual(self.read(), "jev")

    def test_xdg_config_home_is_ignored(self):
        xdg = self.root / "xdg"
        self.write_config(xdg / "gwitg" / "decision-model", b"clef\n")
        self.write_project_config(b"jev\n")
        self.env["XDG_CONFIG_HOME"] = str(xdg)
        self.assertEqual(self.read(), "jev")

    def test_home_common_config_supports_all_values(self):
        for value in ("clef", "jev", "none"):
            with self.subTest(value=value):
                self.write_common_config((value + "\n").encode())
                self.assertEqual(self.read(), value)

    def test_nested_git_uses_nearest_repository_root(self):
        outer = self.root / "outer"
        inner = outer / "nested-repo"
        nested_cwd = inner / "deep" / "work"
        nested_cwd.mkdir(parents=True)
        try:
            self.init_git(outer)
            self.init_git(inner)
        except FileNotFoundError:
            self.skipTest("git executable is unavailable")
        self.write_project_config(b"jev\n", outer)
        self.write_project_config(b"clef\n", inner)
        self.assertEqual(self.read(nested_cwd), "clef")

    def test_git_repository_environment_does_not_redirect_root_lookup(self):
        working_repo = self.root / "working-repo"
        working_cwd = working_repo / "nested"
        working_cwd.mkdir(parents=True)
        unrelated_repo = self.root / "unrelated-repo"
        unrelated_repo.mkdir()
        try:
            self.init_git(working_repo)
            self.init_git(unrelated_repo)
        except FileNotFoundError:
            self.skipTest("git executable is unavailable")
        self.write_project_config(b"clef\n", working_repo)
        self.write_project_config(b"jev\n", unrelated_repo)
        with mock.patch.dict(
            os.environ,
            {
                "GIT_DIR": str(unrelated_repo / ".git"),
                "GIT_WORK_TREE": str(unrelated_repo),
            },
        ):
            self.assertEqual(self.read(working_cwd), "clef")

    def test_unmanaged_directory_uses_its_own_project_config(self):
        self.write_project_config(b"clef\n")
        self.assertEqual(self.read(), "clef")

    def test_git_failure_falls_back_to_working_directory(self):
        self.write_project_config(b"jev\n")
        with mock.patch.object(
            decision_model.subprocess, "run", side_effect=FileNotFoundError("git")
        ):
            self.assertEqual(self.read(), "jev")

    def test_invalid_project_configuration_is_an_error(self):
        self.write_project_config(b"CLEF\n")
        with self.assertRaises(ValueError):
            self.read()

    def test_common_configuration_error_does_not_fall_back(self):
        self.write_common_config(b"invalid\n")
        self.write_project_config(b"jev\n")
        with self.assertRaises(ValueError):
            self.read()

    def test_unreadable_common_configuration_does_not_fall_back(self):
        common_path = self.write_common_config(b"clef\n")
        self.write_project_config(b"jev\n")
        original_read_text = Path.read_text

        def fail_for_common(path, *args, **kwargs):
            if path == common_path:
                raise PermissionError("denied")
            return original_read_text(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", fail_for_common):
            with self.assertRaises(PermissionError):
                self.read()

    def test_invalid_selections_are_rejected(self):
        for value in (b"", b"unknown\n", b"Clef\n", b"clef\njev\n", b"clef # comment\n"):
            with self.subTest(value=value):
                self.write_common_config(value)
                with self.assertRaises(ValueError):
                    self.read()

    def test_directory_instead_of_common_config_reports_error(self):
        (self.home / ".config" / "gwitg" / "decision-model").mkdir(parents=True)
        self.write_project_config(b"jev\n")
        with self.assertRaises(OSError):
            self.read()

    def test_separate_reads_observe_configuration_changes(self):
        path = self.write_common_config(b"clef\n")
        self.write_project_config(b"none\n")
        self.assertEqual(self.read(), "clef")
        path.write_bytes(b"jev\n")
        self.assertEqual(self.read(), "jev")
        path.unlink()
        self.assertEqual(self.read(), "none")

    def test_invalid_utf8_is_rejected(self):
        self.write_common_config(b"\xff")
        with self.assertRaises(UnicodeError):
            self.read()

    def test_whitespace_and_crlf_are_accepted(self):
        self.write_common_config(b"  clef\r\n")
        self.assertEqual(self.read(), "clef")

    def test_cli_reads_from_process_cwd_and_does_not_write_settings(self):
        path = self.write_project_config(b"jev\n")
        before = path.read_bytes()
        env = os.environ.copy()
        env.update(self.env)
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=self.cwd,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "jev\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(path.read_bytes(), before)

    def test_cli_error_has_nonzero_exit_and_no_selection(self):
        self.write_common_config(b"unknown\n")
        env = os.environ.copy()
        env.update(self.env)
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=self.cwd,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("expected exactly one of clef, jev, none", result.stderr)


if __name__ == "__main__":
    unittest.main()
