import os
import unittest
from unittest.mock import patch

import app as app_module


class RuntimeConfigTest(unittest.TestCase):
    def test_runtime_config_prefers_allowed_root_inside_docker(self):
        with patch.dict(os.environ, {'MUSIC_CLEANER_ALLOWED_PATH': ''}, clear=False), \
             patch.object(app_module.os.path, 'exists', side_effect=lambda path: path in ('/.dockerenv', '/app/uploads', '/app/processed')):
            config = app_module._build_runtime_config()

        self.assertTrue(config['in_docker'])
        self.assertEqual(config['default_path'], '/media')

    def test_index_embeds_runtime_config(self):
        with patch.dict(os.environ, {'MUSIC_CLEANER_ALLOWED_PATH': ''}, clear=False), \
             patch.object(app_module.os.path, 'exists', side_effect=lambda path: path in ('/.dockerenv', '/app/uploads', '/app/processed')):
            client = app_module.app.test_client()
            response = client.get('/')

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('window.__MUSIC_META_CLEANER_RUNTIME__', html)
        self.assertIn('"defaultPath": "/media"', html)


if __name__ == '__main__':
    unittest.main()
