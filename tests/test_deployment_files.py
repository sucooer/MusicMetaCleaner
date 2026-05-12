import unittest


class DeploymentFilesTest(unittest.TestCase):
    def test_dockerfile_uses_gunicorn(self):
        with open('Dockerfile', 'r', encoding='utf-8') as file_obj:
            dockerfile = file_obj.read()
        self.assertIn('CMD ["gunicorn"', dockerfile)
        self.assertNotIn('CMD ["python", "app.py"]', dockerfile)

    def test_requirements_include_gunicorn(self):
        with open('requirements.txt', 'r', encoding='utf-8') as file_obj:
            requirements = file_obj.read()
        self.assertIn('gunicorn', requirements)


if __name__ == '__main__':
    unittest.main()
