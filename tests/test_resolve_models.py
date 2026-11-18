import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "resolve_models.py"


def config(model="custom-worker"):
    return {
        "runtimes": {
            "codex-cli": {
                "worker": {"model": model, "reasoning_effort": "high"},
            }
        }
    }


class ResolveModelsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def write_project(self, value):
        path = self.project / ".gwitg" / "models.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def write_user(self, value):
        path = self.home / ".config" / "gwitg" / "models.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def resolve(self, runtime="codex-native", role="worker"):
        from importlib.util import module_from_spec, spec_from_file_location

        spec = spec_from_file_location("resolve_models", SCRIPT)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.resolve(runtime, role, start=self.project, home=self.home)

    def test_builtin_codex_native_worker_and_author(self):
        self.assertEqual(
            self.resolve(),
            {"runtime": "codex-native", "role": "worker", "status": "resolved", "model": "6-luna", "reasoning_effort": "high"},
        )
        self.assertEqual(self.resolve(role="author")["model"], "6.1-sol")
        self.assertEqual(self.resolve(role="author")["reasoning_effort"], "medium")

    def test_builtin_codex_cli_worker_and_unavailable_author(self):
        self.assertEqual(
            self.resolve("codex-cli"),
            {"runtime": "codex-cli", "role": "worker", "status": "resolved", "model": "gpt-6-luna", "reasoning_effort": "high"},
        )
        self.assertEqual(
            self.resolve("codex-cli", "author"),
            {"runtime": "codex-cli", "role": "author", "status": "unavailable"},
        )

    def test_project_setting_takes_precedence(self):
        self.write_user(config("user-worker"))
        self.write_project(config("project-worker"))
        self.assertEqual(self.resolve("codex-cli")["model"], "project-worker")

    def test_user_setting_is_used_when_project_file_is_absent(self):
        self.write_user(config("user-worker"))
        self.assertEqual(self.resolve("codex-cli")["model"], "user-worker")

    def test_missing_non_native_runtime_is_unavailable(self):
        self.assertEqual(
            self.resolve("claude-code"),
            {"runtime": "claude-code", "role": "worker", "status": "unavailable"},
        )

    def test_missing_runtime_in_selected_file_uses_builtin_or_is_unavailable(self):
        self.write_project(config())
        self.write_user(config("user-worker"))
        self.assertEqual(self.resolve("codex-native")["model"], "6-luna")
        self.assertEqual(self.resolve("claude-code")["status"], "unavailable")

    def test_invalid_project_file_does_not_fall_back(self):
        self.write_user(config("user-worker"))
        self.write_project("{")
        with self.assertRaisesRegex(Exception, "cannot read configuration"):
            self.resolve("codex-cli")

    def test_duplicate_json_key_is_error(self):
        self.write_project('{"runtimes":{},"runtimes":{}}')
        with self.assertRaisesRegex(Exception, "duplicate JSON key"):
            self.resolve("codex-cli")
        self.write_project('{"runtimes": NaN}')
        with self.assertRaisesRegex(Exception, "invalid JSON constant"):
            self.resolve("codex-cli")

    def test_partial_role_configuration_and_blank_values(self):
        self.write_project(config())
        self.assertEqual(self.resolve("codex-cli")["model"], "custom-worker")
        self.assertEqual(self.resolve("codex-cli", "author")["status"], "unavailable")

        invalid = config("")
        self.write_project(invalid)
        with self.assertRaisesRegex(Exception, "non-empty strings"):
            self.resolve("codex-cli")
        self.write_project({"runtimes": {"codex-cli": {"worker": {}}}})
        with self.assertRaisesRegex(Exception, "model and reasoning_effort"):
            self.resolve("codex-cli")
        self.write_project({"runtimes": {"codex-cli": {}}})
        with self.assertRaisesRegex(Exception, "worker, author, or both"):
            self.resolve("codex-cli")

    def test_isolated_cli_outputs_resolved_json(self):
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "codex-cli", "worker"],
            cwd=self.project,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(result.stdout)["model"], "gpt-6-luna")
        self.assertEqual(json.loads(result.stdout)["reasoning_effort"], "high")

    def test_isolated_cli_reports_unavailable_with_exit_one(self):
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "codex-cli", "author"],
            cwd=self.project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "unavailable")

    def test_isolated_cli_reports_configuration_error_with_exit_two(self):
        self.write_project("{")
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "codex-cli", "worker"],
            cwd=self.project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("cannot read configuration", result.stderr)


if __name__ == "__main__":
    unittest.main()
