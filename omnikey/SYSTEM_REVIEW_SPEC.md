# 📋 OmniKey — System Review Specification & Audit Brief

> **Belge Amacı:** Bu doküman, **OmniKey** (Canlı Kısayol Takipçisi, Çift Dilli Semantik Arama Motoru, NvChad/Neovim, Herdr, Tmux ve Zsh Entegrasyonları) üzerinde gerçekleştirilen mimari, arama algoritması, parser'lar ve otomatik yedekleme mekanizmasının başka bir AI Agent (Code Reviewer / Architect / QA) tarafından bağımsız olarak denetlenmesi (review) amacıyla hazırlanmıştır.

---

## 📌 1. Yönetici Özeti (Executive Summary)

**OmniKey**, modern terminal iş akışlarındaki tüm kısayol katmanlarını (`Herdr`, `Neovim / NvChad`, `Tmux`, `Zsh`, `Readline / Vim Standartları`) tek bir merkezde toplayan, canlı takip eden ve çift dilli (Türkçe/İngilizce) doğal dil araması sunan akıllı bir CLI aracıdır.

Bu review kapsamında denetlenecek temel alanlar:
1. **Çift Dilli Doğal Dil ve Semantik Arama Motoru:** TR/EN sözlük, kök ayıklama (`strip_suffixes`), stop-word filtresi ve ağırlıklı puanlamalı sıralama (`relevancy scoring`).
2. **NvChad & Çok Satırlı Lua Parser İyileştirmesi:** Lua `function() ... end`, `{ desc = "..." }` ve `opts "..."` formatlarının ayrıştırılması, NvChad standartlarının indekslenmesi.
3. **Ekosistem Arayüzleri & Canlı Entegrasyonlar:**
   - Neovim içi Telescope özel arama eklentisi (`<leader>sk`).
   - Zsh ZLE widget'ı (`Ctrl+Space`, `Alt+K`) ve CLI kısayolları (`ok`, `oks`, `oksy`, `oke`).
   - Herdr pop-up arama penceresi.
4. **Otomatik Canlı Git Yedekleme (Hot Backup):** `sync`, `add`, `remove` veya arka plan izleyicisi (`watchdog`) tetiklendiğinde `omnikey_export.json` dosyasının otomatik güncellenmesi.
5. **Format Sonrası Felaket Kurtarma (Disaster Recovery):** `restore.sh` ile sıfır veri kaybıyla anında kurulum.

---

## 🏛️ 2. Sistem Mimarisi ve Bileşen Haritası

```mermaid
graph TD
    subgraph Inputs["1. Canlı Girdi & Parser Katmanı"]
        H["Herdr (config.toml)"]
        T["Tmux (tmux.conf)"]
        N["Neovim / NvChad (*.lua)"]
        Z["Zsh (.zshrc, .aliases)"]
        B["Builtin Shell / Vim Standards"]
    end

    subgraph Core["2. Semantik & Veri Katmanı"]
        TAG["Semantic Tagger (TR/EN + Stopwords + Normalizer)"]
        DB[(SQLite omnikey.db)]
        AUDIT["Audit Logger (ADD/UPDATE/DEL)"]
        CONF["Conflict Detector"]
    end

    subgraph UI["3. Arayüz & Entegrasyonlar"]
        CLI["OmniKey CLI"]
        FZF["Interactive FZF Popup"]
        ZLE["Zsh ZLE Widget (Ctrl+Space / Alt+K)"]
        TEL["Neovim Telescope (<leader>sk)"]
        WATCH["Config Watcher Daemon (Debounced)"]
        EXP["Git Snapshot (omnikey_export.json)"]
    end

    H --> TAG
    T --> TAG
    N --> TAG
    Z --> TAG
    B --> TAG
    TAG --> DB
    DB --> AUDIT
    DB --> CONF
    DB --> CLI
    CLI --> FZF
    CLI --> ZLE
    CLI --> TEL
    WATCH --> DB
    DB --> EXP
```

---

## 🔍 3. Review Edilecek Temel Dosyalar ve Değişiklikler

### A. Semantik Arama ve Doğal Dil İşleme
| Dosya Yolu | Sorumluluk | Review Odak Noktası |
| :--- | :--- | :--- |
| [`omnikey/semantic/tagger.py`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/semantic/tagger.py) | Çift dilli eş anlamlı haritası, ek temizleme, stop-word filtreleme | TR/EN lemma çıkarma (`strip_suffixes`), stopword filtreleme doğruluğu, `SYNONYM_MAP` kapsamı |
| [`omnikey/db.py`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/db.py) | Veritabanı işlemleri ve puanlamalı arama algoritması | `list_keybindings` içindeki relevancy scoring (tam eşleşme: +120, çoklu token bonusu: +50, etiket eşleşmesi: +25) |
| [`omnikey/parsers/shell_defaults.py`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/parsers/shell_defaults.py) | Zsh/Readline ve Vim yerleşik kısayolları | Evrensel kısayol tanımlarının eksiksizliği (`ctrl+k`, `ctrl+u`, `ctrl+w`, `D`, `dd`, `d0` vb.) |

### B. Neovim & NvChad Entegrasyonu
| Dosya Yolu | Sorumluluk | Review Odak Noktası |
| :--- | :--- | :--- |
| [`omnikey/parsers/neovim.py`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/parsers/neovim.py) | Lua keymap ayrıştırıcı & NvChad standardı | `function() ... end` bloklarında dengeli parantez sayımı, `desc = "..."` ve `opts "..."` ayrıştırma kalitesi |
| [`~/.config/nvim/lua/omnikey.lua`](file:///Users/halisyilboga/.config/nvim/lua/omnikey.lua) | Neovim Telescope özel picker | Telescope API uyumluluğu, JSON parse güvenliği ve `+` register'ına kopyalama |
| [`~/.config/nvim/lua/mappings.lua`](file:///Users/halisyilboga/.config/nvim/lua/mappings.lua) | NvChad kullanıcı tuş ataması | `<leader>sk` mapping tanımlaması |

### C. Yaşayan Konfigürasyon ve Otomatik Git Yedekleme
| Dosya Yolu | Sorumluluk | Review Odak Noktası |
| :--- | :--- | :--- |
| [`omnikey/cli.py`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/cli.py) | Komut satırı arayüzü | `cmd_sync`, `cmd_add`, `cmd_remove` işlemlerinde otomatik `omnikey_export.json` dışa aktarımı |
| [`omnikey/watcher.py`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/watcher.py) | Canlı dosya izleyici (watchdog) | Debounce mekanizması (0.5s), dosya değişikliğinde anında veritabanı senkronizasyonu ve otomatik export |
| [`omnikey/integrations/omnikey.zsh`](file:///Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey/integrations/omnikey.zsh) | Zsh terminal entegrasyonu | PATH yönetimi, ZLE widget (`Ctrl+Space`, `Alt+K`), `ok`, `oks`, `oksy`, `oke` takma adları |

---

## 🧪 4. Doğrulama ve Test Kapsamı

Testler `unittest` kütüphanesi ile yazılmış olup 21 ayrı test senaryosunu doğrulamaktadır:

```bash
python3 -m unittest discover -s tests -v
```

### Test Edilen Kritik Alanlar:
1. **`test_bilingual_search.py`:**
   - Türkçe karmaşık cümle: *"satırın hepsini sonuna kadar silmek"* ➜ `[ZSH] ctrl+k` ve `[NEOVIM] D` en başta.
   - İngilizce arama: *"kill line from cursor to end"* ➜ `[ZSH] ctrl+k` en başta.
   - Satır başı/temizleme: *"satırın başına kadar sil"* ve *"clear whole line"* ➜ `ctrl+u`, `dd`, `d0`.
   - Kelime silme: *"kelime sil"* ve *"delete word forward"* ➜ `ctrl+w`, `alt+d`, `diw`.
   - Ekran temizleme: *"ekranı temizle"* ve *"clear terminal screen"* ➜ `ctrl+l`.
2. **`test_parsers.py`:**
   - Herdr TOML parser doğrulaması (`keys.prefix`, `keys.command`, workspace/agent/worktree mappingleri).
   - Tmux `.tmux.conf` parser doğrulaması (bind/bind-key, prefix, -n flags).
   - Neovim Lua parser doğrulaması (`map`, `vim.keymap.set`, opts table, multi-line).
   - Zsh alias & bindkey parser doğrulaması.
3. **`test_db.py` & `test_conflict.py`:**
   - Upsert bütünlüğü, tag indeksleme, audit log geçmişi ve araçlar arası tuş çakışması tespiti.
4. **`test_export_import.py`:**
   - JSON export ve Disaster Recovery (import) sıfır veri kaybı testi.

---

## 💡 5. İnceleyecek Agent İçin Değerlendirme Kriterleri (Review Checklist)

Gözden geçirme yapacak Agent'ın şu soruları yanıtlaması önerilir:

1. **Doğal Dil Arama Kalitesi:**
   - Eklenen Türkçe ve İngilizce stop-word filtresi ile normalizasyon algoritması uç durumlarda (edge cases) beklenmedik filtreleme yapıyor mu?
   - Relevancy scoring formülü adil ve dengeli mi?
2. **Hata Dayanıklılığı ve Güvenlik (Resilience & Safety):**
   - SQLite `FOREIGN KEY` ve `ON CONFLICT` mekanizmaları çoklu eş zamanlı işlemlerde güvenli mi?
   - Dosya okuma hatalarında (UTF-8 decode, bozuk TOML/Lua dosyaları) parser'lar graceful degradation sağlıyor mu?
3. **Performans:**
   - 200+ kısayol içeren veritabanında FZF ve Neovim Telescope aramaları gecikmesiz (<15ms) çalışıyor mu?
   - `watchdog` debounce mekanizması disk IO yükünü engelliyor mu?
4. **Disaster Recovery (Kurtarılabilirlik):**
   - `restore.sh` ve `omnikey_export.json` temiz bir macOS/Linux sisteminde ek bağımlılık olmadan çalışabilecek yapıda mı?

---

## 📂 6. İlgili Dosyaların Tam Konumları

- **OmniKey Ana Dizin:** `/Users/halisyilboga/develop/studyws/sunumlar/omnikey`
- **Veritabanı Dosyası:** `~/.config/omnikey/omnikey.db`
- **Git Yedek Dosyası:** `/Users/halisyilboga/develop/studyws/sunumlar/omnikey/omnikey_export.json`
- **Neovim Yapılandırması:** `~/.config/nvim/lua/` (`mappings.lua`, `omnikey.lua`)
- **Zsh Entegrasyonu:** `~/.zshrc` ve `omnikey/omnikey/integrations/omnikey.zsh`
