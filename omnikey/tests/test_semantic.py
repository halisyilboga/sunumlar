"""Unit tests for semantic tagger and synonym resolution."""

import unittest

from omnikey.semantic.tagger import SemanticTagger


class TestSemanticTagger(unittest.TestCase):
    def test_generate_tags_for_herdr(self):
        tags = SemanticTagger.generate_tags(
            tool="herdr",
            key_combo="prefix+x",
            action_raw="remove_worktree",
            description="Worktree sil/kapat",
            mode="prefix",
        )
        self.assertIn("herdr", tags)
        self.assertIn("prefix", tags)
        self.assertIn("worktree", tags)
        self.assertIn("sil", tags)
        self.assertIn("remove", tags)
        self.assertIn("kapat", tags)

    def test_generate_tags_for_neovim_find_files(self):
        tags = SemanticTagger.generate_tags(
            tool="neovim",
            key_combo="<leader>ff",
            action_raw="find_files",
            description="Find files in project",
            mode="normal",
        )
        self.assertIn("neovim", tags)
        self.assertIn("leader", tags)
        self.assertIn("find", tags)
        self.assertIn("bul", tags)
        self.assertIn("dosya", tags)

    def test_generate_tags_for_tmux_pane_split(self):
        tags = SemanticTagger.generate_tags(
            tool="tmux",
            key_combo="prefix+v",
            action_raw="split-window -h",
            description="Paneli dikey böl",
            mode="prefix",
        )
        self.assertIn("tmux", tags)
        self.assertIn("split", tags)
        self.assertIn("dikey", tags)
        self.assertIn("bol", tags)


if __name__ == "__main__":
    unittest.main()
