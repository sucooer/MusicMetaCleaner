import subprocess
import unittest


class FrontendRuntimeRunnerTest(unittest.TestCase):
    def test_methods_do_not_use_window_prompt(self):
        with open('static/js/methods/files.js', 'r', encoding='utf-8') as file_obj:
            files_methods = file_obj.read()
        self.assertNotIn('window.prompt', files_methods)

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
