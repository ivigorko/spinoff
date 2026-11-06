import unittest
from pathlib import Path
from scripts.check_playbook import check
from scripts.render_playbook import rendered

ROOT=Path(__file__).resolve().parents[1]

class PlaybookTests(unittest.TestCase):
    def test_all_pinned_sources_have_preserved_bytes_and_adaptation(self):
        result=check()
        self.assertEqual(result['preserved_sources'],144)
        self.assertEqual(result['specialists'],75)
        self.assertEqual(result['team_leaders'],12)
        self.assertEqual(result['original_workflows'],11)

    def test_generated_subject_contracts_and_docs_are_in_sync(self):
        for name,text in rendered().items():
            with self.subTest(name=name):self.assertEqual((ROOT/name).read_text(),text)

    def test_currentness_corrections_have_primary_sources(self):
        text=(ROOT/'instructions/currentness.md').read_text()
        self.assertIn('07.05.2026',text)
        self.assertIn('https://developers.google.com/search/updates',text)
        self.assertIn('https://yandex.ru/dev/metrika/ru/stat/',text)
        self.assertIn('https://labrika.ru/help/ai/vidimost-ai',text)

if __name__=='__main__':unittest.main()
