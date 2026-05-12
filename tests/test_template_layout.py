import unittest


class TemplateLayoutTest(unittest.TestCase):
    def test_settings_panel_is_shared_and_workspace_sections_exist(self):
        with open('templates/index.html', 'r', encoding='utf-8') as file_obj:
            html = file_obj.read()

        self.assertEqual(html.count('<section class="panel settings-panel">'), 1)
        self.assertIn('workspace-shell', html)
        self.assertIn('settings-toggle-bar', html)
        self.assertIn('result-summary-card', html)
        self.assertIn('file-item-main', html)
        self.assertIn('keyword-remove-btn', html)
        self.assertIn('settings-summary-mini', html)
        self.assertNotIn('path-result-panel', html)
        self.assertIn('executionLogsModalEl', html)
        self.assertIn('openExecutionLogs', html)


if __name__ == '__main__':
    unittest.main()
