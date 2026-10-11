import os, sys, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'widget'))
import engine


class SafeUrl(unittest.TestCase):
    def test_accepts_plain_web_links(self):
        self.assertEqual(engine.safe_url('https://example.com/a/b?x=1#top'), 'https://example.com/a/b?x=1#top')
        self.assertTrue(engine.safe_url('http://example.com'))

    def test_rejects_non_web_schemes(self):
        for u in ('javascript:alert(1)', 'data:text/html,<script>', 'file:///etc/passwd', 'ftp://x.com/a', 'vbscript:x', '', None, '//example.com', 'example.com'):
            self.assertEqual(engine.safe_url(u), '', u)

    def test_neutralises_shell_and_html_metacharacters(self):
        hostile = 'https://evil.example/x"; touch /tmp/pwned; echo \'a" onmouseover="alert(1)'
        out = engine.safe_url(hostile)
        self.assertTrue(out.startswith('https://evil.example/'))
        for ch in ('"', "'", ' ', '<', '>', '`'):
            self.assertNotIn(ch, out)


class ReadmeParsing(unittest.TestCase):
    BASE = 'https://raw.githubusercontent.com/o/r/HEAD/'

    def test_image_skips_badges_and_svg(self):
        md = '![build](https://img.shields.io/x.svg)\n<img src="logo.svg">\n![shot](docs/screenshot.png)'
        self.assertEqual(engine.readme_image(md, self.BASE), self.BASE + 'docs/screenshot.png')

    def test_image_absolute_and_protocol_relative(self):
        self.assertEqual(engine.readme_image('<img src="//cdn.x.com/a.jpg">', self.BASE), 'https://cdn.x.com/a.jpg')
        self.assertEqual(engine.readme_image('![a](https://x.com/a.png)', self.BASE), 'https://x.com/a.png')

    def test_image_none(self):
        self.assertEqual(engine.readme_image('just text', self.BASE), '')

    def test_snippet_strips_markup_and_short_lines(self):
        md = '---\ntitle: x\n---\n# Title\n![b](x.png)\n[![badge](a)](b)\n\nThis tool lets agents reverse-engineer any app and rebuild it from scratch.\n'
        out = engine.readme_snip(md)
        self.assertIn('reverse-engineer any app', out)
        self.assertNotIn('badge', out); self.assertNotIn('title:', out)


class Scoring(unittest.TestCase):
    NOW = datetime.now(timezone.utc)

    def item(self, hours, title='something', **kw):
        return {'t': title, 'b': '', 'd': (self.NOW - timedelta(hours=hours)).isoformat(), 's': 'x', **kw}

    def test_newer_scores_higher(self):
        self.assertGreater(engine.score(self.item(1), 'launches', {}), engine.score(self.item(100), 'launches', {}))

    def test_boost_keyword_raises_score(self):
        a = engine.score(self.item(5, 'A new MCP server'), 'repos', {'boost': ['mcp']})
        b = engine.score(self.item(5, 'A new MCP server'), 'repos', {'boost': []})
        self.assertGreater(a, b)

    def test_stars_matter_for_repos(self):
        self.assertGreater(engine.score(self.item(5, stars=5000), 'repos', {}), engine.score(self.item(5, stars=50), 'repos', {}))


class Helpers(unittest.TestCase):
    def test_kfmt(self):
        self.assertEqual((engine.kfmt(999), engine.kfmt(1500), engine.kfmt(2_300_000)), ('999', '1.5k', '2.3M'))

    def test_parse_date_formats(self):
        for s in ('Tue, 06 Oct 2026 10:00:00 GMT', '2026-10-06T10:00:00Z', '2026-10-06T10:00:00+00:00'):
            self.assertIsNotNone(engine.parse_date(s), s)
        self.assertIsNone(engine.parse_date('not a date'))

    def test_clean_strips_html(self):
        self.assertEqual(engine.clean('<p>Hello&nbsp;<b>world</b></p>'), 'Hello world')


if __name__ == '__main__':
    unittest.main()
