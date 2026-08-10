"""OmniKey configuration and path resolution."""

import os
from pathlib import Path
from typing import Dict, List


def get_config_dir() -> Path:
    """Return the base configuration directory for OmniKey."""
    config_dir = os.environ.get("OMNIKEY_CONFIG_DIR")
    if config_dir:
        path = Path(config_dir).expanduser().resolve()
    else:
        path = Path.home() / ".config" / "omnikey"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    """Return the SQLite database path."""
    db_env = os.environ.get("OMNIKEY_DB_PATH")
    if db_env:
        return Path(db_env).expanduser().resolve()
    return get_config_dir() / "omnikey.db"


def get_export_path() -> Path:
    """Return the default export path."""
    export_env = os.environ.get("OMNIKEY_EXPORT_PATH")
    if export_env:
        return Path(export_env).expanduser().resolve()
    # Default to current repo location or user config
    repo_export = Path(__file__).resolve().parent.parent / "omnikey_export.json"
    if repo_export.parent.exists():
        return repo_export
    return get_config_dir() / "omnikey_export.json"


def get_default_watch_targets() -> Dict[str, List[Path]]:
    """Return standard paths to watch per tool, resolving symlinks where useful."""
    home = Path.home()
    targets: Dict[str, List[Path]] = {
        "herdr": [
            home / ".config" / "herdr" / "config.toml",
        ],
        "tmux": [
            home / ".tmux.conf",
            home / ".tmux.conf.local",
            home / ".config" / "tmux" / "tmux.conf",
        ],
        "neovim": [
            home / ".config" / "nvim" / "init.lua",
            home / ".config" / "nvim" / "lua",
        ],
        "zsh": [
            home / ".zshrc",
            home / ".zshrc.local",
            home / ".aliases",
            home / ".aliases.local",
        ],
    }
    return targets
