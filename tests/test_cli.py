import json, os, sys, tempfile, unittest
from unittest import mock

os.environ['HOME'] = tempfile.mkdtemp()            # the CLI creates ~/.local/share/radar — keep tests off the real one
os.environ.update(RADAR_NO_SAY='1', RADAR_NO_OPEN='1', RADAR_NO_REFRESH='1')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'widget'))
import radar_cli as cli


class Rules(unittest.TestCase):
    def test_mute_and_unmute(self):
        self.assertEqual(cli.rules('mute crypto')[0], {'mute_add': ['crypto']})
        self.assertEqual(cli.rules('unmute crypto')[0], {'mute_remove': ['crypto']})

    def test_boost_and_drop(self):
        self.assertEqual(cli.rules('boost voice cloning')[0], {'boost_add': ['voice cloning']})
        self.assertEqual(cli.rules('less of crypto')[0], {'boost_remove': ['crypto']})

    def test_numbers(self):
        self.assertEqual(cli.rules('minimum 500 stars')[0], {'min_stars': 500})
        self.assertEqual(cli.rules('at least 2k stars')[0], {'min_stars': 2000})
        self.assertEqual(cli.rules('show 12 items')[0], {'desk_items': 12})

    def test_whisper_punctuation_is_ignored(self):
        # speech-to-text appends '.', '?', '!' — these must still match the instant local rules
        for said, key in (('Show me the labs.', 1), ('Mute crypto.', 0), ('Open Gmail.', 5), ('Refresh!', 3), ("What's new in agents?", 3), ('Boost voice cloning, please.', 0)):
            self.assertIsNotNone(cli.rules(said), said)
        self.assertEqual(cli.rules('Mute crypto.')[0], {'mute_add': ['crypto']})
        self.assertEqual(cli.rules('Boost voice cloning, please.')[0], {'boost_add': ['voice cloning']})

    def test_polite_and_wake_prefixes(self):
        self.assertEqual(cli.rules('hey radar, please mute nft')[0], {'mute_add': ['nft']})

    def test_lanes_and_search(self):
        self.assertEqual(cli.rules('show me the labs')[1], 'labs')
        self.assertEqual(cli.rules('open agents')[1], 'repos')
        self.assertEqual(cli.rules('find reverse engineering')[2], 'reverse engineering')

    def test_open_app_from_example_config(self):
        r = cli.rules('open gmail')
        self.assertEqual(r[5][0]['name'], 'Gmail')
        self.assertEqual(cli.rules('open my inbox')[5][0]['name'], 'Gmail')

    def test_unknown_goes_to_llm(self):
        self.assertIsNone(cli.rules("I'm really into video tools this week"))


class Patch(unittest.TestCase):
    def test_clamps_and_validates(self):
        p = {'boost': [], 'mute': [], 'desk_items': 10}
        ch = cli.apply_patch(p, {'desk_items': 999, 'min_stars': -5, 'repo_days': 9999})
        self.assertEqual(ch, []); self.assertEqual(p['desk_items'], 10)

    def test_rejects_bad_repo_names_and_unknown_lanes(self):
        p = {'releases_repos': []}
        cli.apply_patch(p, {'releases_repos_add': ['a; rm -rf /', 'owner/repo', '../../etc'], 'lanes': {'evil': False, 'labs': False}})
        self.assertEqual(p['releases_repos'], ['owner/repo']); self.assertEqual(p['lanes'], {'labs': False})

    def test_dedupes_and_lowercases(self):
        p = {'boost': ['mcp'], 'mute': []}
        cli.apply_patch(p, {'boost_add': ['MCP', 'Agents'], 'mute_add': ['  NFT  ']})
        self.assertEqual(p['boost'], ['mcp', 'agents']); self.assertEqual(p['mute'], ['nft'])

    def test_ignores_bools_as_ints(self):
        p = {'desk_items': 10}; cli.apply_patch(p, {'desk_items': True}); self.assertEqual(p['desk_items'], 10)


class Ask(unittest.TestCase):
    def test_rule_match_never_calls_the_llm(self):
        with mock.patch.object(cli, 'llm', side_effect=AssertionError('LLM must not be called')), \
             mock.patch.object(cli, 'save'), mock.patch.object(cli, 'load', return_value={'boost': [], 'mute': []}):
            cli.ask('mute crypto')

    def test_blank_and_noise_ignored(self):
        with mock.patch.object(cli, 'llm', side_effect=AssertionError):
            for t in ('', '  ', '[BLANK_AUDIO]', '(silence)'): cli.ask(t)


class Feedback(unittest.TestCase):
    CLI = os.path.join(os.path.dirname(__file__), '..', 'widget', 'radar_cli.py')

    def run_cli(self, *args):
        env = {**os.environ, 'HOME': tempfile.mkdtemp(), 'RADAR_NO_SAY': '1', 'RADAR_NO_OPEN': '1', 'RADAR_NO_REFRESH': '1'}
        import subprocess
        return subprocess.run([sys.executable, self.CLI, *args], env=env, capture_output=True, text=True, timeout=30).stdout

    def test_ui_mode_emits_machine_readable_reply(self):
        out = self.run_cli('--ui', 'ask', 'show me the labs.')
        self.assertIn('@reply\tOpening labs.\topened the full page · labs', out)

    def test_plain_mode_prints_text_only(self):
        out = self.run_cli('ask', 'show me the labs')
        self.assertEqual(out.strip(), 'Opening labs.')

    def test_text_mode_never_speaks(self):
        with mock.patch.object(cli, 'load', return_value={'voice_feedback': 'text'}), mock.patch.object(cli.subprocess, 'Popen') as pop, \
             mock.patch.dict(os.environ, {'RADAR_NO_SAY': ''}):
            cli.say('hello'); pop.assert_not_called()

    def test_speech_mode_speaks(self):
        with mock.patch.object(cli, 'load', return_value={'voice_feedback': 'speech'}), mock.patch.object(cli.subprocess, 'Popen') as pop, \
             mock.patch.dict(os.environ, {'RADAR_NO_SAY': ''}):
            cli.say('hello'); self.assertEqual(pop.call_args[0][0][0], 'say')

    def test_unknown_mode_falls_back_to_both(self):
        with mock.patch.object(cli, 'load', return_value={'voice_feedback': 'banana'}):
            self.assertEqual(cli.feedback_mode(), 'both')


if __name__ == '__main__':
    unittest.main()
