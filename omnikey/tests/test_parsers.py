"""Unit tests for Herdr, Tmux, Neovim, and Zsh parsers."""

import tempfile
import unittest
from pathlib import Path

from omnikey.parsers.git_commands import GitCommandsParser
from omnikey.parsers.herdr import HerdrParser
from omnikey.parsers.linux_commands import LinuxCommandsParser
from omnikey.parsers.neovim import NeovimParser
from omnikey.parsers.tmux import TmuxParser
from omnikey.parsers.zsh import ZshParser


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_herdr_parser(self):
        content = """
        [keys]
        prefix = "ctrl+s"
        open_worktree = "prefix+o"
        remove_worktree = "prefix+x"
        previous_workspace = "prefix+p"
        next_workspace = "prefix+n"
        switch_workspace = "prefix+1..9"
        """
        f = self.base_path / "config.toml"
        f.write_text(content, encoding="utf-8")

        parser = HerdrParser()
        self.assertTrue(parser.can_handle(f))
        kbs = parser.parse(f)

        self.assertGreaterEqual(len(kbs), 5)
        combos = {kb.key_combo: kb for kb in kbs}
        self.assertIn("ctrl+s", combos)
        self.assertIn("prefix+x", combos)
        self.assertEqual(combos["prefix+x"].action_raw, "remove_worktree")
        self.assertIn("sil", combos["prefix+x"].tags)

    def test_tmux_parser(self):
        content = """
        # act like vim
        bind-key h select-pane -L
        bind-key j select-pane -D
        bind-key -r C-h select-window -t :-
        set -g prefix2 C-s
        """
        f = self.base_path / "tmux.conf"
        f.write_text(content, encoding="utf-8")

        parser = TmuxParser()
        self.assertTrue(parser.can_handle(f))
        kbs = parser.parse(f)

        self.assertGreaterEqual(len(kbs), 3)
        combos = {kb.key_combo: kb for kb in kbs}
        self.assertIn("prefix+h", combos)
        self.assertIn("C-s", combos)

    def test_neovim_parser(self):
        content = """
        local map = vim.keymap.set
        map("n", ";", ":", { desc = "CMD enter command mode" })
        map("i", "jk", "<ESC>")
        vim.keymap.set({"n", "v"}, "<leader>ff", "<cmd>Telescope find_files<cr>", { desc = "Find files" })
        """
        f = self.base_path / "mappings.lua"
        f.write_text(content, encoding="utf-8")

        parser = NeovimParser()
        self.assertTrue(parser.can_handle(f))
        kbs = parser.parse(f)

        self.assertEqual(len(kbs), 3)
        combos = {kb.key_combo: kb for kb in kbs}
        self.assertIn(";", combos)
        self.assertIn("jk", combos)
        self.assertIn("<leader>ff", combos)
        self.assertEqual(combos["<leader>ff"].description, "Find files")
        self.assertIn("bul", combos["<leader>ff"].tags)

    def test_zsh_parser(self):
        content = """
        alias ll="ls -al"
        alias migrate="bin/rails db:migrate" # Run migrations
        bindkey '^R' history-incremental-search-backward
        """
        f = self.base_path / ".zshrc"
        f.write_text(content, encoding="utf-8")

        parser = ZshParser()
        self.assertTrue(parser.can_handle(f))
        kbs = parser.parse(f)

        self.assertEqual(len(kbs), 3)
        combos = {kb.key_combo: kb for kb in kbs}
        self.assertIn("ll", combos)
        self.assertIn("migrate", combos)
        self.assertIn("ctrl+r", combos)

    def test_git_commands_parser(self):
        kbs = GitCommandsParser.get_all_git_recipes()
        self.assertGreaterEqual(len(kbs), 40)
        combos = {kb.key_combo: kb for kb in kbs}
        self.assertTrue(any("stash" in k for k in combos))
        self.assertTrue(any("rebase" in k for k in combos))
        self.assertTrue(any("worktree" in k for k in combos))
        self.assertTrue(any("bisect" in k for k in combos))

    def test_linux_commands_parser(self):
        kbs = LinuxCommandsParser.get_all_linux_commands()
        self.assertGreaterEqual(len(kbs), 60)
        combos = {kb.key_combo: kb for kb in kbs}
        self.assertTrue(any("lsof" in k for k in combos))
        self.assertTrue(any("find" in k for k in combos))
        self.assertTrue(any("tar" in k for k in combos))
        self.assertTrue(any("systemctl" in k for k in combos))


if __name__ == "__main__":
    unittest.main()
