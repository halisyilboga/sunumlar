"""Parser for Neovim Lua keymaps (~/.config/nvim/lua/**/*.lua and NvChad)."""

import re
from pathlib import Path
from typing import List, Tuple

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


# Built-in NvChad keybindings catalogue (fallback & standard baseline)
NVCHAD_BUILTIN_BINDINGS = [
    # General / Navigation
    ("i", "<C-b>", "<ESC>^i", "Satırın başına git / Move to beginning of line"),
    ("i", "<C-e>", "<End>", "Satırın sonuna git / Move to end of line"),
    ("i", "<C-h>", "<Left>", "Sola hareket / Move cursor left"),
    ("i", "<C-l>", "<Right>", "Sağa hareket / Move cursor right"),
    ("i", "<C-j>", "<Down>", "Aşağı hareket / Move cursor down"),
    ("i", "<C-k>", "<Up>", "Yukarı hareket / Move cursor up"),
    ("n", "<C-h>", "<C-w>h", "Sol pencereye geç / Switch window left"),
    ("n", "<C-l>", "<C-w>l", "Sağ pencereye geç / Switch window right"),
    ("n", "<C-j>", "<C-w>j", "Aşağı pencereye geç / Switch window down"),
    ("n", "<C-k>", "<C-w>k", "Yukarı pencereye geç / Switch window up"),
    ("n", "<Esc>", "<cmd>noh<CR>", "Arama vurgularını temizle / Clear search highlights"),
    ("n", "<C-s>", "<cmd>w<CR>", "Dosyayı kaydet / Save file"),
    ("n", "<C-c>", "<cmd>%y+<CR>", "Tüm dosyayı kopyala / Copy whole file to clipboard"),
    ("n", "<leader>n", "<cmd>set nu!<CR>", "Satır numaralarını aç/kapat / Toggle line numbers"),
    ("n", "<leader>rn", "<cmd>set rnu!<CR>", "Göreceli satır numaralarını aç/kapat / Toggle relative numbers"),
    ("n", "<leader>ch", "<cmd>NvCheatsheet<CR>", "NvChad kısayol rehberini aç (NvCheatsheet) / Toggle NvCheatsheet"),
    ("n", "<leader>fm", "require('conform').format()", "Dosyayı formatla (Conform/Prettier) / Format file"),

    # Buffers & Tabs (tabufline)
    ("n", "<leader>b", "<cmd>enew<CR>", "Yeni boş tampon aç / New buffer"),
    ("n", "<tab>", "tabufline.next()", "Sonraki tampona/sekmesine geç / Next buffer"),
    ("n", "<S-tab>", "tabufline.prev()", "Önceki tampona/sekmesine geç / Previous buffer"),
    ("n", "<leader>x", "tabufline.close_buffer()", "Aktif tamponu kapat / Close buffer"),

    # Comments
    ("n", "<leader>/", "gcc", "Yorum satırı yap/kaldır / Toggle comment line"),
    ("v", "<leader>/", "gc", "Seçili alanı yorum yap/kaldır / Toggle comment selection"),

    # File Tree (nvim-tree)
    ("n", "<C-n>", "<cmd>NvimTreeToggle<CR>", "Dosya ağacını aç/kapat (NvimTree) / Toggle NvimTree file explorer"),
    ("n", "<leader>e", "<cmd>NvimTreeFocus<CR>", "Dosya gezginine odaklan (NvimTree) / Focus NvimTree"),

    # Telescope
    ("n", "<leader>ff", "<cmd>Telescope find_files<CR>", "Dosya ara (Telescope) / Find files"),
    ("n", "<leader>fa", "<cmd>Telescope find_files hidden=true<CR>", "Gizli dosyalar dahil tümünü ara (Telescope) / Find all files"),
    ("n", "<leader>fw", "<cmd>Telescope live_grep<CR>", "Proje içinde canlı metin ara (Telescope Live Grep) / Live grep text"),
    ("n", "<leader>fb", "<cmd>Telescope buffers<CR>", "Açık tamponları ara (Telescope) / Find open buffers"),
    ("n", "<leader>fh", "<cmd>Telescope help_tags<CR>", "Neovim yardım sayfalarını ara (Telescope) / Help pages"),
    ("n", "<leader>fo", "<cmd>Telescope oldfiles<CR>", "Son açılan geçmiş dosyaları ara (Telescope) / Find recent files"),
    ("n", "<leader>fz", "<cmd>Telescope current_buffer_fuzzy_find<CR>", "Mevcut dosyada fuzzy ara (Telescope) / Fuzzy find in buffer"),
    ("n", "<leader>cm", "<cmd>Telescope git_commits<CR>", "Git commit geçmişini listele (Telescope) / Git commits"),
    ("n", "<leader>gt", "<cmd>Telescope git_status<CR>", "Git değişiklik durumunu göster (Telescope) / Git status"),
    ("n", "<leader>pt", "<cmd>Telescope terms<CR>", "Arka plan terminallerini seç (Telescope) / Pick hidden term"),
    ("n", "<leader>ma", "<cmd>Telescope marks<CR>", "Yer imleri ve işaretleri ara (Telescope marks) / Find marks"),
    ("n", "<leader>th", "require('nvchad.themes').open()", "NvChad tema seçiciyi aç (Telescope Themes) / Theme picker"),

    # Gitsigns
    ("n", "]c", "gitsigns.next_hunk()", "Sonraki Git değişikliğine (hunk) git / Jump to next Git hunk"),
    ("n", "[c", "gitsigns.prev_hunk()", "Önceki Git değişikliğine (hunk) git / Jump to prev Git hunk"),
    ("n", "<leader>rh", "gitsigns.reset_hunk()", "Git değişikliğini geri al / Reset Git hunk"),
    ("n", "<leader>ph", "gitsigns.preview_hunk()", "Git değişikliğini satırda önizle / Preview Git hunk"),
    ("n", "<leader>gb", "gitsigns.blame_line()", "Satır yazarını göster (Git Blame) / Blame line author"),

    # LSP (Language Server Protocol)
    ("n", "gd", "vim.lsp.buf.definition", "Fonksiyon/sınıf tanımına git (LSP Definition) / Go to definition"),
    ("n", "gD", "vim.lsp.buf.declaration", "Deklarasyona git (LSP Declaration) / Go to declaration"),
    ("n", "gi", "vim.lsp.buf.implementation", "Arayüz implementasyonuna git (LSP) / Go to implementation"),
    ("n", "gr", "vim.lsp.buf.references", "Sembolün tüm kullanımlarını/referanslarını bul (LSP References) / List references"),
    ("n", "K", "vim.lsp.buf.hover", "Dokümantasyonu ve tip bilgisini göster (LSP Hover) / Hover info"),
    ("n", "<leader>ls", "vim.lsp.buf.signature_help", "Fonksiyon parametre imzasını göster (LSP Signature) / Signature help"),
    ("n", "<leader>D", "vim.lsp.buf.type_definition", "Tip tanımına git (LSP Type Definition) / Type definition"),
    ("n", "<leader>ra", "nvchad.lsp.renamer", "Sembolü yeniden adlandır (LSP Rename/Refactor) / Rename symbol"),
    ("n", "<leader>ca", "vim.lsp.buf.code_action", "Kod düzeltme ve aksiyonları (LSP Code Action) / Code action"),
    ("n", "<leader>ds", "vim.diagnostic.setloclist", "Hata ve uyarı listesi (LSP Diagnostics) / Diagnostic loclist"),
    ("n", "[d", "vim.diagnostic.goto_prev", "Önceki diagnostic hatasına git / Prev diagnostic"),
    ("n", "]d", "vim.diagnostic.goto_next", "Sonraki diagnostic hatasına git / Next diagnostic"),
    ("n", "<leader>wa", "vim.lsp.buf.add_workspace_folder", "LSP çalışma alanı klasörü ekle / Add workspace folder"),
    ("n", "<leader>wr", "vim.lsp.buf.remove_workspace_folder", "LSP çalışma alanı klasörü kaldır / Remove workspace folder"),
    ("n", "<leader>wl", "vim.lsp.buf.list_workspace_folders", "LSP çalışma alanı klasörlerini listele / List workspace folders"),

    # Terminals
    ("t", "<C-x>", "<C-\\><C-N>", "Terminal modundan çık / Escape terminal mode"),
    ("n", "<leader>h", "nvchad.term.new(sp)", "Yatay terminal aç / New horizontal terminal"),
    ("n", "<leader>v", "nvchad.term.new(vsp)", "Dikey terminal aç / New vertical terminal"),
    ("n", "<A-i>", "nvchad.term.toggle(float)", "Yüzen terminali aç/kapat (Floating Terminal) / Toggle floating terminal"),
    ("n", "<A-h>", "nvchad.term.toggle(sp)", "Yatay terminali aç/kapat / Toggle horizontal terminal"),
    ("n", "<A-v>", "nvchad.term.toggle(vsp)", "Dikey terminali aç/kapat / Toggle vertical terminal"),

    # WhichKey & UI Tools
    ("n", "<leader>wK", "<cmd>WhichKey<CR>", "Tüm Neovim kısayollarını göster (WhichKey) / WhichKey all keymaps"),
    ("n", "<leader>wk", "WhichKey query", "WhichKey kısayol sorgulama / WhichKey query lookup"),
    ("n", "<leader>cp", "minty.color_picker", "Minty renk paleti ve seçiciyi aç / Open Minty color picker"),
    ("n", "<leader>sh", "minty.shade_picker", "Minty renk tonu seçiciyi aç / Open Minty shade picker"),
    ("n", "<leader>sk", "require('omnikey').search_keybindings", "Tüm sistem kısayollarını ara (OmniKey) / Search all system keybindings"),

    # Mason, Lazy & Treesitter CLI Commands
    ("n", ":Mason", "Mason", "Mason paket yöneticisi (LSP/Linter/Formatter kurucu) / Open Mason package manager"),
    ("n", ":MasonUpdate", "MasonUpdate", "Mason paket kayıtlarını güncelle / Update Mason registries"),
    ("n", ":Lazy", "Lazy", "Lazy eklenti yöneticisini aç / Open Lazy plugin manager"),
    ("n", ":Lazy sync", "Lazy sync", "Tüm eklentileri senkronize et ve güncelle (Lazy) / Sync and update plugins"),
    ("n", ":Lazy check", "Lazy check", "Eklenti güncellemelerini kontrol et (Lazy) / Check plugin updates"),
    ("n", ":TSUpdate", "TSUpdate", "Treesitter sözdizimi ayrıştırıcılarını güncelle / Update Treesitter parsers"),
]


class NeovimParser(BaseParser):
    """Parses Neovim keymaps from Lua configuration files and NvChad."""

    @property
    def tool_name(self) -> str:
        return "neovim"

    def can_handle(self, file_path: Path) -> bool:
        p = str(file_path).lower()
        return "nvim" in p or "neovim" in p or "nvchad" in p or (p.endswith(".lua") and ("keymap" in p or "mapping" in p))

    def _parse_lua_file(self, file_path: Path) -> List[Keybinding]:
        if not file_path.is_file():
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

        keybindings: List[Keybinding] = []
        lines = content.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip comments and empty lines
            if line.startswith("--") or not line:
                i += 1
                continue

            # Look for vim.keymap.set, map, or vim.api.nvim_set_keymap calls
            if re.search(r"\b(?:vim\.keymap\.set|vim\.api\.nvim_set_keymap|\bmap)\s*\(", line) and not line.startswith("local map"):
                stmt = line
                open_parens = stmt.count("(") - stmt.count(")")
                while open_parens > 0 and i + 1 < len(lines):
                    i += 1
                    stmt += " " + lines[i].strip()
                    open_parens = stmt.count("(") - stmt.count(")")

                # Extract arguments inside outer parentheses
                m = re.search(r"\b(?:vim\.keymap\.set|vim\.api\.nvim_set_keymap|\bmap)\s*\((.*)\)", stmt, re.DOTALL)
                if m:
                    inner = m.group(1).strip()

                    # 1. Mode argument (table {"n", "v"} or string "n")
                    modes: List[str] = []
                    mode_match = re.match(r"^(?:\{([^}]*)\}|[\"']([^\"']+)[\"']|[a-zA-Z0-9_\.]+)", inner)
                    if mode_match:
                        mode_raw = mode_match.group(0)
                        rest = inner[len(mode_raw):].lstrip().lstrip(",")
                        if "{" in mode_raw:
                            modes = re.findall(r"[\"']([a-zA-Z0-9]+)[\"']", mode_raw)
                        else:
                            clean_m = mode_raw.strip("\"' ")
                            if clean_m:
                                modes = [clean_m]
                    else:
                        rest = inner

                    if not modes:
                        modes = ["normal"]

                    # 2. LHS Key combo argument
                    lhs_match = re.match(r"^\s*[\"']([^\"']+)[\"']", rest)
                    if lhs_match:
                        lhs = lhs_match.group(1).strip()
                        rest2 = rest[lhs_match.end():].lstrip().lstrip(",")

                        # 3. Description parsing from opts or comments
                        desc = ""
                        desc_m = re.search(r"desc\s*=\s*[\"']([^\"']+)[\"']", rest2)
                        if not desc_m:
                            desc_m = re.search(r"opts\s*[\"']([^\"']+)[\"']", rest2)
                        if desc_m:
                            desc = desc_m.group(1).strip()

                        # 4. RHS / Action extraction
                        rhs_m = re.match(r"^\s*[\"']([^\"']+)[\"']", rest2)
                        if rhs_m:
                            action_raw = rhs_m.group(1)
                        elif "function" in rest2:
                            action_raw = desc or "lua function"
                        else:
                            action_raw = rest2.split(",")[0].strip()

                        if not desc:
                            desc = f"Neovim komutu: {action_raw}"

                        mode_str = "/".join(modes)
                        tags = SemanticTagger.generate_tags(
                            tool="neovim",
                            key_combo=lhs,
                            action_raw=action_raw,
                            description=desc,
                            mode=mode_str,
                        )

                        keybindings.append(
                            Keybinding(
                                tool="neovim",
                                key_combo=lhs,
                                action_raw=action_raw,
                                description=desc,
                                source_file=str(file_path.resolve()),
                                mode=mode_str,
                                tags=tags,
                            )
                        )
            i += 1

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

    @classmethod
    def get_nvchad_builtins(cls) -> List[Keybinding]:
        """Return full standard NvChad keybindings with rich bilingual tags."""
        bindings: List[Keybinding] = []
        for mode, combo, action, desc in NVCHAD_BUILTIN_BINDINGS:
            tags = SemanticTagger.generate_tags(
                tool="neovim",
                key_combo=combo,
                action_raw=action,
                description=desc,
                mode=mode,
            )
            tags.extend(["nvchad", "chad", "neovim", "editor"])
            bindings.append(
                Keybinding(
                    tool="neovim",
                    key_combo=combo,
                    action_raw=action,
                    description=desc,
                    source_file="builtin://nvchad",
                    mode=mode,
                    tags=sorted(list(set(tags))),
                )
            )
        return bindings
