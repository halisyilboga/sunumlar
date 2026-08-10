"""Unit tests for conflict detection and key normalization."""

import unittest

from omnikey.models import Keybinding
from omnikey.semantic.conflict import ConflictDetector, normalize_key_combo


class TestConflictDetector(unittest.TestCase):
    def test_normalize_key_combo(self):
        self.assertEqual(normalize_key_combo("<C-s>"), "ctrl+s")
        self.assertEqual(normalize_key_combo("C-s"), "ctrl+s")
        self.assertEqual(normalize_key_combo("ctrl+s"), "ctrl+s")
        self.assertEqual(normalize_key_combo("prefix+x"), "prefix+x")
        self.assertEqual(normalize_key_combo("<leader>ff"), "leader+ff")
        self.assertEqual(normalize_key_combo("bind-key C-b"), "ctrl+b")

    def test_cross_tool_conflict(self):
        kb1 = Keybinding(
            tool="herdr",
            key_combo="ctrl+s",
            action_raw="prefix",
            description="Herdr prefix",
            source_file="herdr.toml",
            mode="normal",
        )
        kb2 = Keybinding(
            tool="tmux",
            key_combo="C-s",
            action_raw="set prefix2 C-s",
            description="Tmux prefix2",
            source_file="tmux.conf",
            mode="normal",
        )
        kb3 = Keybinding(
            tool="neovim",
            key_combo="<C-s>",
            action_raw="w",
            description="Save file",
            source_file="mappings.lua",
            mode="normal",
        )

        conflicts = ConflictDetector.detect_conflicts([kb1, kb2, kb3])
        self.assertEqual(len(conflicts), 1)
        c = conflicts[0]
        self.assertEqual(c.key_combo, "ctrl+s")
        self.assertEqual(len(c.tools), 3)
        self.assertIn("herdr", c.tools)
        self.assertIn("tmux", c.tools)
        self.assertIn("neovim", c.tools)


if __name__ == "__main__":
    unittest.main()
