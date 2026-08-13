"""Parser registry for all supported configuration formats."""

from pathlib import Path
from typing import List, Optional

from omnikey.parsers.base import BaseParser
from omnikey.parsers.git_commands import GitCommandsParser
from omnikey.parsers.herdr import HerdrParser
from omnikey.parsers.linux_commands import LinuxCommandsParser
from omnikey.parsers.neovim import NeovimParser
from omnikey.parsers.shell_defaults import ShellDefaultsParser
from omnikey.parsers.tmux import TmuxParser
from omnikey.parsers.zsh import ZshParser

ALL_PARSERS: List[BaseParser] = [
    HerdrParser(),
    TmuxParser(),
    NeovimParser(),
    ZshParser(),
    ShellDefaultsParser(),
    LinuxCommandsParser(),
    GitCommandsParser(),
]


def get_parser_for_file(file_path: Path) -> Optional[BaseParser]:
    """Find the appropriate parser for a given file path."""
    for parser in ALL_PARSERS:
        if parser.can_handle(file_path):
            return parser
    return None


__all__ = [
    "BaseParser",
    "HerdrParser",
    "TmuxParser",
    "NeovimParser",
    "ZshParser",
    "ShellDefaultsParser",
    "LinuxCommandsParser",
    "GitCommandsParser",
    "ALL_PARSERS",
    "get_parser_for_file",
]
