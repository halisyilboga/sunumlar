"""Unit tests for Git backup export and disaster recovery import."""

import json
import tempfile
import unittest
from pathlib import Path

from omnikey.db import Database
from omnikey.models import Keybinding


class TestExportImport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db1_path = Path(self.temp_dir.name) / "db1.db"
        self.db2_path = Path(self.temp_dir.name) / "db2.db"
        self.export_file = Path(self.temp_dir.name) / "backup.json"

        self.db1 = Database(db_path=self.db1_path)
        self.db2 = Database(db_path=self.db2_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_import_roundtrip(self):
        # Populate DB1
        kb1 = Keybinding(
            tool="herdr",
            key_combo="prefix+x",
            action_raw="remove_worktree",
            description="Worktree sil",
            source_file="config.toml",
            tags=["herdr", "sil"],
        )
        kb2 = Keybinding(
            tool="tmux",
            key_combo="prefix+h",
            action_raw="select-pane -L",
            description="Pane left",
            source_file="tmux.conf",
            tags=["tmux", "pane"],
        )
        self.db1.sync_file_keybindings("herdr", "config.toml", [kb1])
        self.db1.sync_file_keybindings("tmux", "tmux.conf", [kb2])

        # Export DB1
        data = self.db1.export_data()
        self.export_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.assertTrue(self.export_file.exists())

        # Import into empty DB2
        with open(self.export_file, "r", encoding="utf-8") as f:
            imported_data = json.load(f)

        stats = self.db2.import_data(imported_data, replace=True)
        self.assertEqual(stats["imported"], 2)

        # Verify DB2 contents match DB1
        db2_kbs = self.db2.list_keybindings()
        self.assertEqual(len(db2_kbs), 2)
        combos = {k.key_combo: k for k in db2_kbs}
        self.assertIn("prefix+x", combos)
        self.assertIn("prefix+h", combos)
        self.assertIn("sil", combos["prefix+x"].tags)


if __name__ == "__main__":
    unittest.main()
