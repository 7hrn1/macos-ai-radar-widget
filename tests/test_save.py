import base64, json, os, subprocess, sys, tempfile, unittest

SAVE = os.path.join(os.path.dirname(__file__), '..', 'widget', 'save.py')


def run_save(item, home):
    arg = base64.b64encode(json.dumps(item).encode()).decode()
    return subprocess.run([sys.executable, SAVE, arg], env={**os.environ, 'HOME': home}, capture_output=True).returncode


class Save(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(); self.path = os.path.join(self.home, 'Documents', 'ai-radar-saved.md')

    def test_writes_a_checkbox_line(self):
        self.assertEqual(run_save({'n': 'Cool repo', 'u': 'https://example.com/x', 'd': 'desc'}, self.home), 0)
        text = open(self.path).read()
        self.assertIn('- [ ] **Cool repo**', text); self.assertIn('<https://example.com/x>', text)

    def test_rejects_non_web_urls(self):
        for u in ('javascript:alert(1)', 'file:///etc/passwd', '', 'data:text/html,x'):
            self.assertNotEqual(run_save({'n': 'x', 'u': u}, self.home), 0, u)
        self.assertFalse(os.path.exists(self.path))

    def test_strips_markdown_and_newlines_from_titles(self):
        run_save({'n': 'Bad [x](y) **b**\nSECOND LINE', 'u': 'https://e.com'}, self.home)
        self.assertEqual(len(open(self.path).read().strip().splitlines()), 2)   # one title line + one link line

    def test_garbage_argument_is_ignored(self):
        r = subprocess.run([sys.executable, SAVE, 'not-base64!!'], env={**os.environ, 'HOME': self.home}, capture_output=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
