import os
import tempfile
import unittest

import app as app_module


class KeywordSettingsApiTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_upload = app_module.app.config['UPLOAD_FOLDER']
        self.original_processed = app_module.app.config['PROCESSED_FOLDER']

        self.upload_dir = os.path.join(self.tempdir.name, 'uploads')
        self.processed_dir = os.path.join(self.tempdir.name, 'processed')
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        app_module.app.config['TESTING'] = True
        app_module.app.config['UPLOAD_FOLDER'] = self.upload_dir
        app_module.app.config['PROCESSED_FOLDER'] = self.processed_dir
        app_module.configure_keyword_settings_storage()

        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.app.config['UPLOAD_FOLDER'] = self.original_upload
        app_module.app.config['PROCESSED_FOLDER'] = self.original_processed
        app_module.configure_keyword_settings_storage()
        self.tempdir.cleanup()

    def test_get_keywords_returns_defaults_when_settings_file_missing(self):
        response = self.client.get('/settings/lyrics_keywords')
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn('keywords', data)
        self.assertIn('default_keywords', data)
        self.assertIn('作词', data['keywords'])
        self.assertEqual(data['keywords'], data['default_keywords'])

    def test_save_keywords_persists_and_updates_cleaning_rule(self):
        payload = {
            'keywords': ['自定义字段', '自定义字段', '  ', '保留测试']
        }

        save_response = self.client.post('/settings/lyrics_keywords', json=payload)
        self.assertEqual(save_response.status_code, 200)

        saved_data = save_response.get_json()
        self.assertEqual(saved_data['keywords'], ['自定义字段', '保留测试'])

        get_response = self.client.get('/settings/lyrics_keywords')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json()['keywords'], ['自定义字段', '保留测试'])

        cleaned_lyrics, removed_lines = app_module.clean_lyrics(
            '[00:01.00]自定义字段：词作者\n[00:02.00]正式歌词'
        )
        self.assertEqual(cleaned_lyrics, '[00:02.00]正式歌词')
        self.assertEqual(removed_lines, ['[00:01.00]自定义字段：词作者'])

    def test_cleanup_keeps_keyword_settings_file(self):
        self.client.post('/settings/lyrics_keywords', json={'keywords': ['保留字段']})

        uploaded_file = os.path.join(self.upload_dir, 'demo.txt')
        with open(uploaded_file, 'w', encoding='utf-8') as file_obj:
            file_obj.write('temporary')

        response = self.client.post('/cleanup')
        self.assertEqual(response.status_code, 200)

        settings_path = os.path.join(
            self.upload_dir,
            app_module.app.config['KEYWORD_SETTINGS_FILENAME']
        )
        self.assertTrue(os.path.exists(settings_path))
        self.assertFalse(os.path.exists(uploaded_file))


if __name__ == '__main__':
    unittest.main()
