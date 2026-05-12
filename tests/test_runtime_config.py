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

    def test_process_path_rejects_non_media_path_inside_docker_by_default(self):
        with patch.dict(os.environ, {'MUSIC_CLEANER_ALLOWED_PATH': ''}, clear=False), \
             patch.object(app_module, '_is_running_in_docker', return_value=True):
            client = app_module.app.test_client()
            with patch.object(app_module.os.path, 'exists', wraps=app_module.os.path.exists):
                response = client.post('/process_path', json={'path': os.path.abspath('.')})

        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data['allowed_root'], '/media')


if __name__ == '__main__':
    unittest.main()
