import unittest

from app import app


class CacheHeadersTest(unittest.TestCase):
    def test_static_cache_is_long_lived(self):
        client = app.test_client()
        response = client.get('/static/app.css')
        self.assertEqual(response.status_code, 200)
        cache_control = response.headers.get('Cache-Control', '')
        self.assertIn('max-age=31536000', cache_control)
        response.close()


if __name__ == '__main__':
    unittest.main()
