import io
import json
import os
import tempfile
import unittest

import app as app_module


class FilenameMappingPersistenceTest(unittest.TestCase):
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

    def test_upload_persists_filename_mapping_to_disk(self):
        response = self.client.post(
            '/upload',
            data={'files': (io.BytesIO(b'fake-audio'), 'Original Song.mp3')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 200)
        mapping_path = app_module.get_filename_mapping_path()
        self.assertTrue(os.path.exists(mapping_path))

        with open(mapping_path, 'r', encoding='utf-8') as file_obj:
            mapping = json.load(file_obj)

        self.assertEqual(list(mapping.values()), ['Original Song.mp3'])

    def test_download_uses_persisted_filename_mapping_after_restart(self):
        internal_filename = '20260512_000000_song.mp3'
        processed_filename = f'cleaned_{internal_filename}'
        processed_path = os.path.join(self.processed_dir, processed_filename)
        with open(processed_path, 'wb') as file_obj:
            file_obj.write(b'processed')

        with open(app_module.get_filename_mapping_path(), 'w', encoding='utf-8') as file_obj:
            json.dump({internal_filename: 'Original Song.mp3'}, file_obj, ensure_ascii=False)

        response = self.client.get(f'/download/{processed_filename}')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Original Song.mp3', response.headers['Content-Disposition'])
        response.close()


if __name__ == '__main__':
    unittest.main()
