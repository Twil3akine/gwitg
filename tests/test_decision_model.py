import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "decision_model.py"
spec = importlib.util.spec_from_file_location("decision_model", SCRIPT)
decision_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision_model)


class DecisionModelTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = {"HOME": str(self.root / "home")}

    def write_config(self, root, value):
        path = root / "gwitg" / "decision-model"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    def test_missing_configuration_uses_none(self):
        self.assertEqual(decision_model.read_decision_model(self.env), "none")

    def test_home_fallback_and_supported_values(self):
        for value in ("clef", "jev", "none"):
            with self.subTest(value=value):
                self.write_config(Path(self.env["HOME"]) / ".config", (value + "\n").encode())
                self.assertEqual(decision_model.read_decision_model(self.env), value)

    def test_xdg_configuration_takes_precedence(self):
        self.write_config(Path(self.env["HOME"]) / ".config", b"clef\n")
        xdg = self.root / "xdg"
        self.write_config(xdg, b"jev\n")
        self.env["XDG_CONFIG_HOME"] = str(xdg)
        self.assertEqual(decision_model.read_decision_model(self.env), "jev")

    def test_empty_xdg_uses_home(self):
        self.env["XDG_CONFIG_HOME"] = ""
        self.write_config(Path(self.env["HOME"]) / ".config", b"clef\n")
        self.assertEqual(decision_model.read_decision_model(self.env), "clef")

    def test_separate_reads_observe_configuration_changes(self):
        path = self.write_config(Path(self.env["HOME"]) / ".config", b"clef\n")
        self.assertEqual(decision_model.read_decision_model(self.env), "clef")
        path.write_bytes(b"jev\n")
        self.assertEqual(decision_model.read_decision_model(self.env), "jev")
        path.unlink()
        self.assertEqual(decision_model.read_decision_model(self.env), "none")

    def test_whitespace_and_crlf_are_accepted(self):
        self.write_config(Path(self.env["HOME"]) / ".config", b"  clef\r\n")
        self.assertEqual(decision_model.read_decision_model(self.env), "clef")

    def test_invalid_selections_are_rejected(self):
        for value in (b"", b"unknown\n", b"Clef\n", b"clef\njev\n", b"clef # comment\n"):
            with self.subTest(value=value):
                self.write_config(Path(self.env["HOME"]) / ".config", value)
                with self.assertRaises(ValueError):
                    decision_model.read_decision_model(self.env)

    def test_relative_xdg_is_rejected(self):
        self.env["XDG_CONFIG_HOME"] = "relative"
        with self.assertRaises(ValueError):
            decision_model.read_decision_model(self.env)

    def test_invalid_utf8_is_rejected(self):
        self.write_config(Path(self.env["HOME"]) / ".config", b"\xff")
        with self.assertRaises(UnicodeError):
            decision_model.read_decision_model(self.env)

    def test_directory_instead_of_config_reports_error(self):
        path = Path(self.env["HOME"]) / ".config" / "gwitg" / "decision-model"
        path.mkdir(parents=True)
        with self.assertRaises(OSError):
            decision_model.read_decision_model(self.env)

    def run_script(self):
        env = os.environ.copy()
        env.pop("XDG_CONFIG_HOME", None)
        env.update(self.env)
        return subprocess.run([sys.executable, str(SCRIPT)], env=env, text=True, capture_output=True)

    def test_cli_prints_only_selection_and_does_not_write(self):
        path = self.write_config(Path(self.env["HOME"]) / ".config", b"jev\n")
        before = path.read_bytes()
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "jev\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(path.read_bytes(), before)

    def test_cli_error_has_nonzero_exit_and_no_selection(self):
        self.write_config(Path(self.env["HOME"]) / ".config", b"unknown\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("expected exactly one of clef, jev, none", result.stderr)


if __name__ == "__main__":
    unittest.main()
