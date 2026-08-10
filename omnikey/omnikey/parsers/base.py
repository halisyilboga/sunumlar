"""Abstract base parser for configuration files."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from omnikey.models import Keybinding


class BaseParser(ABC):
    """Base class for all config file keybinding parsers."""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the tool (e.g. 'herdr', 'tmux', 'neovim', 'zsh')."""
        pass

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> List[Keybinding]:
        """Parse keybindings from the file and return a list of Keybinding models."""
        pass
