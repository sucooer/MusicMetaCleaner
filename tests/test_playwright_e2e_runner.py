import subprocess
import unittest


class PlaywrightE2ERunnerTest(unittest.TestCase):
    def test_browser_renders_vue_content(self):
        result = subprocess.run(
            ['node', 'tests/test_playwright_e2e.mjs'],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            self.fail(result.stderr or result.stdout)


if __name__ == '__main__':
    unittest.main()
