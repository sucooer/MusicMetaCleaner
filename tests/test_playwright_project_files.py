import json
import unittest


class PlaywrightProjectFilesTest(unittest.TestCase):
    def test_package_json_contains_playwright_script(self):
        with open('package.json', 'r', encoding='utf-8') as file_obj:
            package_data = json.load(file_obj)

        self.assertIn('scripts', package_data)
        self.assertIn('test:e2e', package_data['scripts'])
        self.assertIn('playwright', json.dumps(package_data, ensure_ascii=False).lower())


if __name__ == '__main__':
    unittest.main()
