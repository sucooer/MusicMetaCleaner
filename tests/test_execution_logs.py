import os
import tempfile
import unittest
from unittest.mock import patch

import app as app_module


class ExecutionLogsTest(unittest.TestCase):
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

    def test_upload_process_writes_failed_and_ignored_log_entry(self):
        response = self.client.post('/process', json={
            'filenames': ['missing.mp3']
        })
        self.assertEqual(response.status_code, 200)

        logs_response = self.client.get('/execution_logs')
        self.assertEqual(logs_response.status_code, 200)
        data = logs_response.get_json()

        self.assertEqual(len(data['logs']), 1)
        log_entry = data['logs'][0]
        self.assertEqual(log_entry['mode'], 'upload')
        self.assertEqual(log_entry['failed_count'], 1)
        self.assertEqual(log_entry['ignored_count'], 0)
        self.assertEqual(log_entry['failed_files'][0]['filename'], 'missing.mp3')

    def test_path_process_writes_ignored_log_entry(self):
        target_dir = os.path.join(self.tempdir.name, 'music')
        os.makedirs(target_dir, exist_ok=True)
        sample_file = os.path.join(target_dir, 'song.mp3')
        with open(sample_file, 'wb') as file_obj:
            file_obj.write(b'not-real-audio')

        with patch.object(app_module, 'process_audio_file', return_value=(None, 0)):
            response = self.client.post('/process_path', json={
                'path': target_dir,
                'dry_run': False,
                'backup': False
            })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['ignored_count'], 1)

        logs_response = self.client.get('/execution_logs')
        self.assertEqual(logs_response.status_code, 200)
        log_entry = logs_response.get_json()['logs'][0]
        self.assertEqual(log_entry['mode'], 'path')
        self.assertEqual(log_entry['ignored_count'], 1)
        self.assertEqual(log_entry['target_path'], os.path.abspath(target_dir))

    def test_cleanup_keeps_execution_log_file(self):
        self.client.post('/process', json={'filenames': ['missing.mp3']})

        response = self.client.post('/cleanup')
        self.assertEqual(response.status_code, 200)

        self.assertTrue(os.path.exists(app_module.get_execution_log_path()))


if __name__ == '__main__':
    unittest.main()
