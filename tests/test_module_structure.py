import importlib.util
import unittest


class ModuleStructureTest(unittest.TestCase):
    def test_routes_and_storage_modules_exist(self):
        self.assertIsNotNone(importlib.util.find_spec('storage'))
        self.assertIsNotNone(importlib.util.find_spec('routes'))
        self.assertIsNotNone(importlib.util.find_spec('services'))

    def test_app_file_is_reduced_after_split(self):
        with open('app.py', 'r', encoding='utf-8') as file_obj:
            line_count = sum(1 for _ in file_obj)
        self.assertLess(line_count, 450)


if __name__ == '__main__':
    unittest.main()
