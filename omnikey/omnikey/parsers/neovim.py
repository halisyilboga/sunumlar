"""Parser for Neovim Lua keymaps (~/.config/nvim/lua/**/*.lua)."""

import re
from pathlib import Path
from typing import List

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


class NeovimParser(BaseParser):
    """Parses Neovim keymaps from Lua configuration files."""

    @property
    def tool_name(self) -> str:
        return "neovim"

    def can_handle(self, file_path: Path) -> bool:
        p = str(file_path).lower()
        return "nvim" in p or "neovim" in p or (p.endswith(".lua") and ("keymap" in p or "mapping" in p))

    def _parse_lua_file(self, file_path: Path) -> List[Keybinding]:
        if not file_path.is_file():
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        keybindings: List[Keybinding] = []

        # Matches:
        # map("n", ";", ":", { desc = "CMD enter command mode" })
        # map("i", "jk", "<ESC>")
        # vim.keymap.set({"n", "v"}, "<leader>ff", "<cmd>Telescope find_files<cr>", { desc = "Find files" })
        # vim.api.nvim_set_keymap("n", "<leader>e", ":NvimTreeToggle<CR>", { noremap = true })
        pattern = re.compile(
            r"""(?:vim\.keymap\.set|vim\.api\.nvim_set_keymap|\bmap)\s*\(\s*(\{[^}]*\}|["'][^"']*["']|[a-zA-Z0-9_\.]+)\s*,\s*["']([^"']+)["']\s*,\s*(["'][^"']*["']|[^\,\)\s]+)(?:\s*,\s*(\{.*?\})\s*)?\s*\)""",
            re.DOTALL,
        )

        for match in pattern.finditer(content):
            mode_raw = match.group(1).strip()
            lhs = match.group(2).strip()
            rhs_raw = match.group(3).strip().strip("\"'")
            opts_raw = match.group(4) or ""

            # Parse modes: can be "n" or {"n", "i", "v"}
            modes: List[str] = []
            if "{" in mode_raw:
                modes = re.findall(r"""["']([a-zA-Z0-9]+)["']""", mode_raw)
            else:
                clean_m = mode_raw.strip("\"' ")
                if clean_m:
                    modes = [clean_m]
            if not modes:
                modes = ["normal"]

            # Parse description from opts { desc = "..." }
            desc = ""
            desc_match = re.search(r"""desc\s*=\s*["']([^"']+)["']""", opts_raw)
            if desc_match:
                desc = desc_match.group(1).strip()
            else:
                desc = f"Neovim komutu: {rhs_raw}"

            mode_str = "/".join(modes)

            tags = SemanticTagger.generate_tags(
                tool="neovim",
                key_combo=lhs,
                action_raw=rhs_raw,
                description=desc,
                mode=mode_str,
            )

            keybindings.append(
                Keybinding(
                    tool="neovim",
                    key_combo=lhs,
                    action_raw=rhs_raw,
                    description=desc,
                    source_file=str(file_path.resolve()),
                    mode=mode_str,
                    tags=tags,
                )
            )

        return keybindings

    def parse(self, target_path: Path) -> List[Keybinding]:
        if not target_path.exists():
            return []

        results: List[Keybinding] = []
        if target_path.is_dir():
            for lua_file in target_path.rglob("*.lua"):
                if ".git" in lua_file.parts:
                    continue
                results.extend(self._parse_lua_file(lua_file))
        else:
            results.extend(self._parse_lua_file(target_path))

        return results
