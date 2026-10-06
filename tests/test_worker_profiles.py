import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
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
            "light": {"model": "custom-worker-v2", "reasoning_effort": "low"},
        }
        self.write_common_config(profiles)
        self.assertEqual(self.resolve(), profiles["standard"])

    def test_explicit_profile_takes_precedence_over_standard_default(self):
        profiles = {
            "standard": {"model": "default-worker", "reasoning_effort": "high"},
            "light": {"model": "selected-worker", "reasoning_effort": "low"},
        }
        self.write_common_config(profiles)
        selected_profile = "light"

        self.assertEqual(self.resolve(selected_profile), profiles[selected_profile])

    def test_judge_recommendation_resolves_the_configured_profile(self):
        profiles = {
            "standard": {"model": "default-worker", "reasoning_effort": "high"},
            "light": {"model": "recommended-worker", "reasoning_effort": "low"},
        }
        self.write_common_config(profiles)
        judge_result = {
            "delegate": True,
            "profile": "light",
            "reason": "The work is independent and bounded",
        }

        self.assertEqual(
            worker_profiles.resolve_worker_profile(
                judge_result=judge_result, environ=self.env, cwd=self.cwd
            ),
            profiles["light"],
        )

    def test_explicit_profile_precedes_judge_recommendation(self):
        profiles = {
            "standard": {"model": "default-worker", "reasoning_effort": "high"},
            "light": {"model": "explicit-worker", "reasoning_effort": "low"},
            "strong": {"model": "judge-worker", "reasoning_effort": "high"},
        }
        self.write_common_config(profiles)
        invalid_judge_result = {"delegate": True, "profile": "strong"}

        self.assertEqual(
            worker_profiles.resolve_worker_profile(
                "light", self.env, self.cwd, invalid_judge_result
            ),
            profiles["light"],
        )

    def test_negative_judge_recommendation_does_not_resolve_a_worker(self):
        judge_result = {
            "delegate": False,
            "profile": None,
            "reason": "The parent should keep the task",
        }

        self.assertIsNone(
            worker_profiles.resolve_worker_profile(
                judge_result=judge_result, environ=self.env, cwd=self.cwd
            )
        )

    def test_invalid_judge_result_is_rejected_as_a_whole(self):
        results = (
            {"delegate": True, "profile": "light", "reason": " ", "extra": 1},
            {"delegate": True, "profile": "light"},
            {"delegate": False, "profile": "light", "reason": "valid"},
            {"delegate": "true", "profile": "light", "reason": "valid"},
        )
        for judge_result in results:
            with self.subTest(judge_result=judge_result):
                with self.assertRaises(worker_profiles.InvalidJudgeResult):
                    worker_profiles.resolve_worker_profile(
                        judge_result=judge_result, environ=self.env, cwd=self.cwd
                    )

    def test_valid_but_unconfigured_judge_profile_is_not_substituted(self):
        self.write_common_config(
            {"standard": {"model": "default-worker", "reasoning_effort": "high"}}
        )
        judge_result = {
            "delegate": True,
            "profile": "missing",
            "reason": "A configured profile should be used",
        }

        with self.assertRaises(ValueError) as error:
            worker_profiles.resolve_worker_profile(
                judge_result=judge_result, environ=self.env, cwd=self.cwd
            )
        self.assertNotIsInstance(error.exception, worker_profiles.InvalidJudgeResult)
        self.assertIn("unknown worker profile 'missing'", str(error.exception))

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

    def test_cli_imports_resolver_outside_repository(self):
        profiles = {
            "standard": {"model": "custom-worker", "reasoning_effort": "medium"}
        }
        self.write_project_config(profiles)
        env = os.environ.copy()
        env.update(self.env)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "standard"],
            cwd=self.cwd,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), profiles["standard"])
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
