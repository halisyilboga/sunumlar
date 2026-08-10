"""Unit tests for CLI command parser and executions."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnikey.cli import build_parser, main
from omnikey.db import Database


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "cli_test.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parser_commands(self):
        parser = build_parser()
        args_sync = parser.parse_args(["sync"])
        self.assertEqual(args_sync.command, "sync")

        args_add = parser.parse_args(["add", "prefix+w", "Workspace list", "-t", "herdr"])
        self.assertEqual(args_add.command, "add")
        self.assertEqual(args_add.combo, "prefix+w")
        self.assertEqual(args_add.tool, "herdr")

        args_list = parser.parse_args(["list", "--json"])
        self.assertEqual(args_list.command, "list")
        self.assertTrue(args_list.json)

    def test_cli_add_and_list(self):
        with patch.dict("os.environ", {"OMNIKEY_DB_PATH": str(self.db_path)}):
            main(["add", "prefix+t", "New Tab", "--tool", "herdr"])
            db = Database(self.db_path)
            kbs = db.list_keybindings()
            self.assertEqual(len(kbs), 1)
            self.assertEqual(kbs[0].key_combo, "prefix+t")


if __name__ == "__main__":
    unittest.main()
