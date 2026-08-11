"""Unit tests for SQLite database and audit tracking layer."""

import tempfile
import unittest
from pathlib import Path

from omnikey.db import Database
from omnikey.models import Keybinding


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_omnikey.db"
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_tables(self):
        self.assertTrue(self.db_path.exists())
        kbs = self.db.list_keybindings()
        self.assertEqual(len(kbs), 0)

    def test_add_manual_keybinding(self):
        kb = Keybinding(
            tool="herdr",
            key_combo="prefix+w",
            action_raw="workspace_picker",
            description="Workspace seçici",
            source_file="manual",
            tags=["herdr", "workspace", "sec"],
        )
        saved = self.db.add_manual_keybinding(kb)
        self.assertIsNotNone(saved.id)
        self.assertTrue(saved.is_manual)

        # Retrieve
        fetched = self.db.get_keybinding(saved.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.key_combo, "prefix+w")
        self.assertIn("workspace", fetched.tags)

        # Audit log verification
        audits = self.db.get_audit_history()
        self.assertTrue(any(a.change_type in ("ADDED", "UPDATED") for a in audits))

    def test_sync_file_keybindings_diff(self):
        tool = "tmux"
        source_file = "/tmp/test_tmux.conf"

        kb1 = Keybinding(tool=tool, key_combo="h", action_raw="select-pane -L", description="Left", source_file=source_file)
        kb2 = Keybinding(tool=tool, key_combo="j", action_raw="select-pane -D", description="Down", source_file=source_file)

        # First sync: 2 additions
        stats1 = self.db.sync_file_keybindings(tool, source_file, [kb1, kb2])
        self.assertEqual(stats1["added"], 2)
        self.assertEqual(len(self.db.list_keybindings(tool="tmux")), 2)

        # Second sync with update and deletion
        kb1_modified = Keybinding(tool=tool, key_combo="h", action_raw="select-pane -L", description="Modified Left", source_file=source_file)
        kb3_new = Keybinding(tool=tool, key_combo="k", action_raw="select-pane -U", description="Up", source_file=source_file)

        stats2 = self.db.sync_file_keybindings(tool, source_file, [kb1_modified, kb3_new])
        self.assertEqual(stats2["added"], 1)     # kb3
        self.assertEqual(stats2["updated"], 1)   # kb1
        self.assertEqual(stats2["deleted"], 1)   # kb2 removed

        all_tmux = self.db.list_keybindings(tool="tmux")
        self.assertEqual(len(all_tmux), 2)
        combos = [k.key_combo for k in all_tmux]
        self.assertIn("h", combos)
        self.assertIn("k", combos)
        self.assertNotIn("j", combos)

    def test_search_by_tag_and_desc(self):
        kb1 = Keybinding(
            tool="herdr",
            key_combo="prefix+x",
            action_raw="remove_worktree",
            description="Worktree sil",
            source_file="config.toml",
            tags=["herdr", "worktree", "sil", "remove"],
        )
        kb2 = Keybinding(
            tool="neovim",
            key_combo="<leader>ff",
            action_raw="find_files",
            description="Dosya ara",
            source_file="mappings.lua",
            tags=["nvim", "find", "dosya", "ara"],
        )
        self.db.sync_file_keybindings("herdr", "config.toml", [kb1])
        self.db.sync_file_keybindings("neovim", "mappings.lua", [kb2])

        # Search by tag "sil"
        res_sil = self.db.list_keybindings(search="sil")
        self.assertEqual(len(res_sil), 1)
        self.assertEqual(res_sil[0].key_combo, "prefix+x")

        # Search by desc "dosya"
        res_dosya = self.db.list_keybindings(search="dosya")
        self.assertEqual(len(res_dosya), 1)
        self.assertEqual(res_dosya[0].tool, "neovim")

    def test_settings_roundtrip(self):
        self.assertIsNone(self.db.get_setting("active_tools"))
        self.db.set_active_tools(["herdr", "tmux"])
        self.assertEqual(self.db.get_active_tools(), ["herdr", "tmux"])
        self.db.set_active_tools(None)
        self.assertIsNone(self.db.get_active_tools())
        self.db.set_active_tools([])
        self.assertIsNone(self.db.get_active_tools())

    def test_active_tools_filter(self):
        kb1 = Keybinding(tool="herdr", key_combo="prefix+w", action_raw="workspace_picker", description="WS", source_file="a")
        kb2 = Keybinding(tool="neovim", key_combo="dd", action_raw="delete_line", description="Satir sil", source_file="b")
        self.db.sync_file_keybindings("herdr", "a", [kb1])
        self.db.sync_file_keybindings("neovim", "b", [kb2])

        # tools restriction applies
        self.db.set_active_tools(["herdr"])
        active = self.db.get_active_tools()
        res = self.db.list_keybindings(tools=active)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].tool, "herdr")

        # search + tools restriction combined
        res2 = self.db.list_keybindings(tools=["herdr"], search="satir")
        self.assertEqual(len(res2), 0)

        # tools=[] means no restriction
        res3 = self.db.list_keybindings(tools=[])
        self.assertEqual(len(res3), 2)

    def test_export_import_preserves_active_tools(self):
        self.db.set_active_tools(["herdr"])
        data = self.db.export_data()
        self.assertEqual(data["active_tools"], ["herdr"])

        other = Database(db_path=Path(self.temp_dir.name) / "other.db")
        other.import_data(data)
        self.assertEqual(other.get_active_tools(), ["herdr"])


if __name__ == "__main__":
    unittest.main()
