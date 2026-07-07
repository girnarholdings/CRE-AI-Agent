"""Guard for audit finding H18: every dashboard input JSON named in
rebuild_all.py must exist and be tracked by git (not gitignored), so the
deployed dashboards can be reproduced from a fresh clone.

Run with: python3 -m unittest tests.test_rebuild_inputs_tracked
"""
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REBUILD_SCRIPT = REPO_ROOT / "rebuild_all.py"


def dashboard_inputs():
    """Extract the "input" paths from the DASHBOARDS list in rebuild_all.py."""
    text = REBUILD_SCRIPT.read_text()
    paths = re.findall(r'"input":\s*"([^"]+)"', text)
    return [Path(p) for p in paths]


class TestRebuildInputsTracked(unittest.TestCase):
    def test_script_exists_and_names_six_inputs(self):
        self.assertTrue(REBUILD_SCRIPT.exists(), "rebuild_all.py missing")
        self.assertEqual(len(dashboard_inputs()), 6)

    def test_inputs_exist_and_not_gitignored(self):
        for path in dashboard_inputs():
            with self.subTest(input=str(path)):
                self.assertTrue(path.exists(), f"missing input: {path}")
                rel = path.relative_to(REPO_ROOT)
                ignored = subprocess.run(
                    ["git", "check-ignore", "-q", str(rel)],
                    cwd=REPO_ROOT,
                ).returncode == 0
                self.assertFalse(ignored, f"gitignored input: {rel}")

    def test_inputs_tracked_in_git(self):
        for path in dashboard_inputs():
            rel = path.relative_to(REPO_ROOT)
            with self.subTest(input=str(rel)):
                tracked = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", str(rel)],
                    cwd=REPO_ROOT,
                    capture_output=True,
                ).returncode == 0
                self.assertTrue(tracked, f"untracked input: {rel}")


if __name__ == "__main__":
    unittest.main()
