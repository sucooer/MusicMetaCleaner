import importlib.util
import unittest


class ModuleStructureTest(unittest.TestCase):
    def test_routes_and_storage_modules_exist(self):
        self.assertIsNotNone(importlib.util.find_spec('storage'))
        self.assertIsNotNone(importlib.util.find_spec('routes'))
        self.assertIsNotNone(importlib.util.find_spec('services'))
        self.assertIsNotNone(importlib.util.find_spec('route_modules.upload_routes'))
        self.assertIsNotNone(importlib.util.find_spec('route_modules.path_routes'))
        self.assertIsNotNone(importlib.util.find_spec('route_modules.file_routes'))
        self.assertIsNotNone(importlib.util.find_spec('route_modules.settings_routes'))

    def test_app_file_is_reduced_after_split(self):
        with open('app.py', 'r', encoding='utf-8') as file_obj:
            line_count = sum(1 for _ in file_obj)
        self.assertLess(line_count, 450)

    def test_routes_and_frontend_aggregators_are_reduced(self):
        with open('routes.py', 'r', encoding='utf-8') as file_obj:
            routes_lines = sum(1 for _ in file_obj)
        with open('static/js/methods.js', 'r', encoding='utf-8') as file_obj:
            methods_lines = sum(1 for _ in file_obj)
        self.assertLess(routes_lines, 220)
        self.assertLess(methods_lines, 180)

    def test_storage_uses_database_entrypoint(self):
        with open('storage.py', 'r', encoding='utf-8') as file_obj:
            storage_text = file_obj.read()
        self.assertIn('sqlite3', storage_text)

    def test_routes_use_logger_not_print(self):
        with open('route_modules/upload_routes.py', 'r', encoding='utf-8') as file_obj:
            upload_text = file_obj.read()
        with open('route_modules/file_routes.py', 'r', encoding='utf-8') as file_obj:
            file_text = file_obj.read()
        self.assertNotIn('print(', upload_text)
        self.assertNotIn('print(', file_text)


if __name__ == '__main__':
    unittest.main()
