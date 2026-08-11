"""Semantic tagger and normalizer generating comprehensive bilingual (TR/EN) search keywords."""

import re
from typing import Dict, List, Set, Tuple

# Comprehensive Bilingual Domain Synonym Dictionary
SYNONYM_MAP: Dict[str, List[str]] = {
    # Line & Text Units
    "line": ["satir", "satır", "satirlar", "satırlar", "line", "lines", "row", "rows", "satirin", "satırın", "satiri", "satırı"],
    "satir": ["line", "lines", "satir", "satır", "row", "satirlar", "satırlar", "satirin", "satırın", "satiri", "satırı"],
    "satır": ["line", "lines", "satir", "satır", "row", "satirlar", "satırlar", "satirin", "satırın", "satiri", "satırı"],
    "word": ["kelime", "kelimeler", "sozcuk", "sözcük", "word", "words"],
    "kelime": ["word", "words", "kelime", "kelimeler", "sozcuk", "sözcük"],
    "char": ["karakter", "harf", "char", "character"],
    "karakter": ["char", "character", "harf", "karakter"],

    # Positions & Boundaries
    "end": ["son", "sonu", "sonuna", "sonunda", "end", "eol", "tail", "finish"],
    "son": ["end", "eol", "son", "sonu", "sonuna", "sonunda", "tail", "finish"],
    "sonuna": ["end", "eol", "son", "sonu", "sonuna", "tail"],
    "beginning": ["bas", "baş", "basa", "başa", "basi", "başı", "start", "bol", "head", "home", "beginning"],
    "start": ["bas", "baş", "basa", "başa", "basi", "başı", "start", "beginning", "bol", "home"],
    "bas": ["beginning", "start", "bas", "baş", "basa", "başa", "basi", "başı", "home"],
    "baş": ["beginning", "start", "bas", "baş", "basa", "başa", "basi", "başı", "home"],
    "cursor": ["imlec", "imleç", "pointer", "cursor", "point"],
    "imlec": ["cursor", "imlec", "imleç", "pointer"],
    "imleç": ["cursor", "imlec", "imleç", "pointer"],

    # Delete / Remove / Kill / Clear / Kes
    "delete": ["sil", "silme", "silmek", "siler", "kaldir", "kaldır", "remove", "kill", "erase", "delete", "kes", "kesme"],
    "sil": ["delete", "remove", "kill", "erase", "clear", "sil", "silme", "silmek", "siler", "kaldir", "kaldır", "kes", "kesme"],
    "silme": ["delete", "remove", "kill", "erase", "clear", "sil", "silme", "silmek", "kes"],
    "silmek": ["delete", "remove", "kill", "erase", "clear", "sil", "silme", "silmek", "kes"],
    "kill": ["oldur", "öldür", "kes", "kesme", "sil", "silme", "silmek", "kill", "terminate", "delete"],
    "remove": ["sil", "silme", "kaldir", "kaldır", "remove", "delete", "kill"],
    "clear": ["temizle", "temizleme", "bosalt", "boşalt", "clear", "wipe", "flush", "reset"],
    "temizle": ["clear", "wipe", "reset", "temizle", "temizleme", "sil", "silme"],
    "kes": ["cut", "kill", "sil", "silme", "kes", "kesme", "delete"],

    # Quantifiers & Scope
    "all": ["hepsi", "hepsini", "tum", "tüm", "tumu", "tümü", "tumunu", "tümünü", "tamami", "tamamı", "all", "entire", "whole"],
    "hepsi": ["all", "entire", "whole", "hepsi", "hepsini", "tum", "tüm", "tümü", "tamamı"],
    "hepsini": ["all", "entire", "whole", "hepsi", "hepsini", "tum", "tüm", "tümü", "tamamı"],
    "tum": ["all", "entire", "whole", "tum", "tüm", "hepsi", "hepsini"],
    "tüm": ["all", "entire", "whole", "tum", "tüm", "hepsi", "hepsini"],

    # Direction & Movement
    "next": ["sonraki", "ileri", "next", "forward", "after"],
    "previous": ["onceki", "önceki", "geri", "prev", "previous", "backward", "before"],
    "prev": ["onceki", "önceki", "geri", "prev", "previous", "backward"],
    "forward": ["ileri", "sonraki", "forward", "next", "after"],
    "backward": ["geri", "onceki", "önceki", "backward", "prev", "previous", "before"],
    "ileri": ["forward", "next", "ileri", "after"],
    "geri": ["backward", "prev", "previous", "geri", "before"],

    # Actions / Operations
    "switch": ["gecis", "geçiş", "degistir", "değiştir", "switch", "toggle", "sec", "seç"],
    "toggle": ["ac-kapa", "aç-kapa", "degistir", "değiştir", "toggle", "switch"],
    "focus": ["odaklan", "odak", "sec", "seç", "focus", "select"],
    "select": ["sec", "seç", "secim", "seçim", "select", "choose", "focus"],
    "goto": ["git", "yonlen", "yönlen", "goto", "jump", "atla"],
    "jump": ["atla", "git", "jump", "goto"],
    "copy": ["kopyala", "kopyalama", "panoya-al", "copy", "yank", "clipboard"],
    "yank": ["kopyala", "yank", "copy", "panoya-al"],
    "kopyala": ["copy", "yank", "kopyala", "panoya-al", "clipboard"],
    "paste": ["yapistir", "yapıştır", "yapistirma", "yapıştırma", "paste", "put"],
    "yapistir": ["paste", "put", "yapistir", "yapıştır"],
    "yapıştır": ["paste", "put", "yapistir", "yapıştır"],
    "undo": ["geri-al", "geri", "revert", "undo", "iptal"],
    "redo": ["ileri-al", "yinele", "redo"],
    "cancel": ["iptal", "vazgec", "vazgeç", "cancel", "abort", "interrupt"],
    "quit": ["cikis", "çıkış", "kapat", "exit", "quit"],
    "exit": ["cikis", "çıkış", "kapat", "exit", "quit", "eof"],
    "detach": ["ayril", "ayrıl", "arka-plan", "detach", "disconnect"],

    # Structural Elements
    "workspace": ["calisma-alani", "çalışma-alanı", "alan", "workspace", "space", "proje", "project"],
    "worktree": ["worktree", "git-dal", "calisma-agaci", "çalışma-ağacı", "dal", "branch", "repo"],
    "tab": ["sekme", "tab", "pencere", "sayfa"],
    "pane": ["panel", "bolme", "bölme", "pane", "bolum", "bölüm", "cerceve", "çerçeve"],
    "window": ["pencere", "window", "ekran"],
    "screen": ["ekran", "screen", "terminal"],
    "split": ["bol", "böl", "bolme", "bölme", "split", "divide", "ayir", "ayır"],
    "vertical": ["dikey", "vertical", "vsplit", "dik"],
    "horizontal": ["yatay", "horizontal", "hsplit", "yan"],
    "resize": ["boyutlandir", "boyutlandır", "yeniden-boyutlandir", "resize", "scale"],
    "zoom": ["buyut", "büyüt", "odak", "zoom", "fullscreen", "tam-ekran"],

    # AI & Agents
    "agent": ["ajan", "ai", "yapay-zeka", "bot", "agent", "asistan", "assistant"],
    "ai": ["yapay-zeka", "ai", "agent", "llm", "ajan"],

    # Files, Buffers, Editing
    "file": ["dosya", "dosyalar", "file", "files", "belge"],
    "files": ["dosya", "dosyalar", "file", "files", "belge"],
    "dosya": ["file", "files", "dosya", "dosyalar", "belge"],
    "buffer": ["tampon", "buffer", "buffers", "dosya", "sekme"],
    "buffers": ["tampon", "buffer", "buffers", "dosya", "sekme"],
    "save": ["kaydet", "yaz", "save", "write"],
    "kaydet": ["save", "write", "kaydet"],
    "edit": ["duzenle", "düzenle", "yaz", "edit", "modify"],
    "duzenle": ["edit", "modify", "duzenle", "düzenle"],
    "düzenle": ["edit", "modify", "duzenle", "düzenle"],

    # Search & History & Helpers
    "search": ["ara", "arama", "bul", "search", "find", "grep", "lookup"],
    "find": ["bul", "ara", "arama", "find", "search", "lookup"],
    "history": ["gecmis", "geçmiş", "scrollback", "history", "kayit", "kayıt"],
    "help": ["yardim", "yardım", "destek", "help", "kilavuz", "kılavuz", "rehber"],
    "reload": ["yenile", "tekrar-yukle", "tekrar-yükle", "reload", "refresh"],
}

# Stopwords to filter out from conversational search queries (both TR and EN)
STOP_WORDS: Set[str] = {
    # Turkish stop words
    "ve", "ile", "veya", "de", "da", "ki", "icin", "için", "olan", "olarak",
    "kadar", "nasil", "nasıl", "gibi", "bir", "cok", "çok", "bunu", "buna",
    "bunu", "istiyorum", "nasil", "yapilir", "yapılır", "etmek", "yapmak",
    "mesela", "turlu", "türlü", "ben", "sen", "bu", "su", "şu", "o", "mi",
    "mu", "mü", "mı", "var", "yok", "ile", "hepsini", "tumunu", "tümünü",
    # English stop words
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "is", "are", "it", "this", "that", "how", "can", "i", "you", "want",
    "would", "like", "to", "do", "does", "from", "with", "into", "all",
    "please", "me", "my", "your",
}


def normalize_text(text: str) -> str:
    """Normalize Turkish/English text to lower case and ascii-equivalent letters."""
    if not text:
        return ""
    mapping = {
        "İ": "i", "I": "ı", "ı": "i",
        "Ğ": "g", "ğ": "g",
        "Ü": "u", "ü": "u",
        "Ş": "s", "ş": "s",
        "Ö": "o", "ö": "o",
        "Ç": "c", "ç": "c",
    }
    for tr_char, ascii_char in mapping.items():
        text = text.replace(tr_char, ascii_char)
    text = text.lower()
    # Strip non-alphanumeric except space, dash, plus
    text = re.sub(r"[^\w\s\-\+]", " ", text)
    return text


def strip_suffixes(word: str) -> str:
    """Strip common Turkish and English grammatical suffixes to extract core lemma."""
    w = word.strip()
    if len(w) <= 3:
        return w

    # Turkish suffixes
    tr_suffixes = [
        "nin", "nın", "nun", "nün", "in", "ın", "un", "ün",
        "ini", "ını", "unu", "ünü", "sini", "sını", "sunu", "sünü",
        "deki", "daki", "teki", "taki", "den", "dan", "ten", "tan",
        "ler", "lar", "mek", "mak", "me", "ma", "ye", "ya", "e", "a",
        "le", "la", "yle", "yla", "si", "sı", "su", "sü",
    ]
    for suf in tr_suffixes:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]

    # English suffixes
    en_suffixes = ["tion", "ment", "ing", "ies", "es", "ed", "s"]
    for suf in en_suffixes:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            if suf == "ies":
                return w[:-3] + "y"
            return w[:-len(suf)]

    return w


class SemanticTagger:
    """Extracts and expands multilingual semantic tags for keybindings and search queries."""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Split text into normalized tokens."""
        if not text:
            return []
        norm = normalize_text(text)
        raw_tokens = re.split(r"[\s_\-\+:\/]+", norm)
        tokens: List[str] = []
        for t in raw_tokens:
            t = t.strip()
            if len(t) >= 2:
                tokens.append(t)
                stem = strip_suffixes(t)
                if stem != t and len(stem) >= 2:
                    tokens.append(stem)
        return list(dict.fromkeys(tokens))

    @classmethod
    def expand_tokens(cls, tokens: List[str]) -> Set[str]:
        """Expand list of tokens with all matching synonyms."""
        expanded: Set[str] = set(tokens)
        for token in tokens:
            if token in SYNONYM_MAP:
                for syn in SYNONYM_MAP[token]:
                    expanded.add(syn)
                    expanded.add(normalize_text(syn))
            # Also check stem
            stem = strip_suffixes(token)
            if stem in SYNONYM_MAP:
                for syn in SYNONYM_MAP[stem]:
                    expanded.add(syn)
                    expanded.add(normalize_text(syn))
        return set(t for t in expanded if len(t) >= 2)

    @classmethod
    def process_query(cls, query: str) -> Tuple[List[str], Set[str]]:
        """
        Process a user search query into:
        1. Clean meaningful core tokens
        2. Broad synonym-expanded tokens for query matching
        """
        tokens = cls.tokenize(query)
        # Filter stop words
        core_tokens = [t for t in tokens if t not in STOP_WORDS]
        if not core_tokens:
            core_tokens = tokens  # fallback if all were stop words

        expanded = cls.expand_tokens(core_tokens)
        return core_tokens, expanded

    @classmethod
    def generate_tags(
        cls,
        tool: str,
        key_combo: str,
        action_raw: str,
        description: str,
        mode: str = "normal",
    ) -> List[str]:
        """Generate comprehensive search tags for a keybinding."""
        tags: Set[str] = set()

        tool_clean = normalize_text(tool).strip()
        tags.add(tool_clean)
        if tool_clean in ("nvim", "neovim"):
            tags.update(["nvim", "neovim", "vim", "editor"])
        elif tool_clean == "herdr":
            tags.update(["herdr", "multiplexer", "terminal-manager", "workspace"])
        elif tool_clean == "tmux":
            tags.update(["tmux", "multiplexer", "terminal"])
        elif tool_clean in ("zsh", "bash", "shell", "readline"):
            tags.update(["zsh", "bash", "shell", "readline", "terminal", "prompt"])

        if mode and mode != "normal":
            tags.add(normalize_text(mode))

        corpus = f"{action_raw} {description} {key_combo}"
        tokens = cls.tokenize(corpus)
        for t in tokens:
            tags.add(t)

        expanded = cls.expand_tokens(list(tags))
        tags.update(expanded)

        combo_norm = normalize_text(key_combo)
        if "prefix" in combo_norm:
            tags.add("prefix")
        if "ctrl" in combo_norm or "c-" in combo_norm:
            tags.add("ctrl")
        if "alt" in combo_norm or "m-" in combo_norm:
            tags.add("alt")
        if "shift" in combo_norm:
            tags.add("shift")
        if "leader" in combo_norm:
            tags.add("leader")

        clean_results = sorted(list(set(t.strip() for t in tags if len(t.strip()) >= 2)))
        return clean_results
