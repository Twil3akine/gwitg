import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "worker_profiles.py"
spec = importlib.util.spec_from_file_location("worker_profiles", SCRIPT)
worker_profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker_profiles)


class WorkerProfileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.cwd = self.root / "work"
        self.cwd.mkdir()
        self.home = self.root / "home"
        self.env = {"HOME": str(self.home)}

    def write_config(self, path, document):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def write_common_config(self, profiles):
        return self.write_config(
            self.home / ".config" / "gwitg" / "worker-profiles.json",
            {"profiles": profiles},
        )

    def write_project_config(self, profiles):
        return self.write_config(
            self.cwd / ".gwitg" / "worker-profiles.json", {"profiles": profiles}
        )

    def resolve(self, profile=None):
        return worker_profiles.resolve_worker_profile(profile, self.env, self.cwd)

    def test_missing_configuration_uses_default_profiles_and_standard(self):
        self.assertEqual(
            self.resolve(), {"model": "6-luna", "reasoning_effort": "high"}
        )
        self.assertEqual(
            self.resolve("light"), {"model": "6-luna", "reasoning_effort": "low"}
        )
        self.assertEqual(
            self.resolve("strong"), {"model": "6-astra", "reasoning_effort": "high"}
        )

    def test_configured_profiles_resolve_to_concrete_settings(self):
        profiles = {
            "standard": {"model": "custom-worker", "reasoning_effort": "medium"},
            "fast-task": {"model": "custom-worker-v2", "reasoning_effort": "xhigh"},
        }
        self.write_common_config(profiles)
        self.assertEqual(self.resolve(), profiles["standard"])
        self.assertEqual(self.resolve("fast-task"), profiles["fast-task"])

    def test_common_configuration_precedes_project_configuration(self):
        self.write_common_config(
            {"standard": {"model": "common", "reasoning_effort": "high"}}
        )
        self.write_project_config(
            {"standard": {"model": "project", "reasoning_effort": "low"}}
        )
        self.assertEqual(
            self.resolve(), {"model": "common", "reasoning_effort": "high"}
        )

    def test_invalid_configuration_is_rejected(self):
        config = self.home / ".config" / "gwitg" / "worker-profiles.json"
        config.parent.mkdir(parents=True)
        config.write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            self.resolve()

    def test_invalid_profile_settings_are_rejected(self):
        self.write_common_config({"standard": {"model": "only-a-model"}})
        with self.assertRaisesRegex(ValueError, "reasoning_effort"):
            self.resolve()

    def test_unknown_profile_is_rejected_without_substitution(self):
        self.write_common_config(
            {"default": {"model": "worker-v9", "reasoning_effort": "unlisted"}}
        )
        with self.assertRaisesRegex(ValueError, "unknown worker profile"):
            self.resolve("standard")


if __name__ == "__main__":
    unittest.main()
