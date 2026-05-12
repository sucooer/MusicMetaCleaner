import subprocess
import unittest


class FrontendRuntimeRunnerTest(unittest.TestCase):
    def test_node_frontend_runtime(self):
        result = subprocess.run(
            ['node', 'tests/test_frontend_runtime.js'],
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            self.fail(result.stderr or result.stdout)


if __name__ == '__main__':
    unittest.main()
