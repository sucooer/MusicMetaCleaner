import io
import os
import sqlite3
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
        db_path = app_module.get_app_db_path()
        self.assertTrue(os.path.exists(db_path))

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute('SELECT original_name FROM filename_mappings').fetchall()

        self.assertEqual([row[0] for row in rows], ['Original Song.mp3'])

    def test_download_uses_persisted_filename_mapping_after_restart(self):
        internal_filename = '20260512_000000_song.mp3'
        processed_filename = f'cleaned_{internal_filename}'
        processed_path = os.path.join(self.processed_dir, processed_filename)
        with open(processed_path, 'wb') as file_obj:
            file_obj.write(b'processed')

        with sqlite3.connect(app_module.get_app_db_path()) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO filename_mappings (internal_name, original_name) VALUES (?, ?)',
                (internal_filename, 'Original Song.mp3')
            )
            conn.commit()

        response = self.client.get(f'/download/{processed_filename}')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Original Song.mp3', response.headers['Content-Disposition'])
        response.close()


if __name__ == '__main__':
    unittest.main()
