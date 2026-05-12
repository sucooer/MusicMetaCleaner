import unittest


class TemplateLayoutTest(unittest.TestCase):
    def test_template_uses_external_assets_and_keeps_workspace_structure(self):
        with open('templates/index.html', 'r', encoding='utf-8') as file_obj:
            html = file_obj.read()

        self.assertIn("filename='app.css'", html)
        self.assertIn("filename='app.js'", html)
        self.assertIn("filename='js/state.js'", html)
        self.assertIn("filename='js/methods.js'", html)
        self.assertNotIn('<style>', html)
        self.assertEqual(html.count('<section class="panel settings-panel">'), 1)
        self.assertIn('workspace-shell', html)
        self.assertIn('settings-toggle-bar', html)
        self.assertIn('result-summary-card', html)
        self.assertIn('file-item-main', html)
        self.assertIn('keyword-remove-btn', html)
        self.assertIn('settings-summary-mini', html)
        self.assertNotIn('path-result-panel', html)
        self.assertIn('executionLogsModalEl', html)
        self.assertNotIn('createApp({', html)


if __name__ == '__main__':
    unittest.main()
