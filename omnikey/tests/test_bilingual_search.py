"""Unit tests for bilingual Turkish/English natural language search."""

import tempfile
import unittest
from pathlib import Path

from omnikey.db import Database
from omnikey.parsers.shell_defaults import ShellDefaultsParser


class TestBilingualSearch(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_omnikey.db"
        self.db = Database(self.db_path)
        # Sync builtins
        kbs = ShellDefaultsParser.get_all_builtins()
        self.db.sync_file_keybindings(tool="builtin", source_file="builtin://standards", new_kbs=kbs)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_turkish_complex_line_deletion_query(self):
        results = self.db.list_keybindings(search="satırın hepsini sonuna kadar silmek")
        self.assertTrue(len(results) > 0)
        combos = [r.key_combo for r in results]
        self.assertTrue("ctrl+k" in combos or "D" in combos)

    def test_english_line_deletion_query(self):
        results = self.db.list_keybindings(search="kill line from cursor to end")
        self.assertTrue(len(results) > 0)
        combos = [r.key_combo for r in results]
        self.assertIn("ctrl+k", combos)

    def test_turkish_and_english_clear_line(self):
        tr_results = self.db.list_keybindings(search="satırın başına kadar sil")
        en_results = self.db.list_keybindings(search="clear whole line")
        self.assertTrue(any(r.key_combo in ("ctrl+u", "d0") for r in tr_results))
        self.assertTrue(any(r.key_combo in ("ctrl+u", "dd") for r in en_results))

    def test_word_deletion_queries(self):
        tr_results = self.db.list_keybindings(search="kelime sil")
        en_results = self.db.list_keybindings(search="delete word forward")
        self.assertTrue(any("word" in r.action_raw or "word" in r.description.lower() for r in tr_results))
        self.assertTrue(any(r.key_combo == "alt+d" or "dw" in r.key_combo for r in en_results))

    def test_screen_clear_queries(self):
        tr_results = self.db.list_keybindings(search="ekranı temizle")
        en_results = self.db.list_keybindings(search="clear terminal screen")
        self.assertTrue(any(r.key_combo == "ctrl+l" for r in tr_results))
        self.assertTrue(any(r.key_combo == "ctrl+l" for r in en_results))


if __name__ == "__main__":
    unittest.main()
