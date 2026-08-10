# 🤖 OmniKey — Dynamic Keybinding & Context Tracker Agent

> **Tüm terminal ekosistemindeki (Herdr, Neovim, Tmux, Zsh) kısayolları canlı izleyen, anlamsal (TR/EN) arama sunan, çakışmaları tespit eden ve format sonrası tek komutla kurtarılabilen (disaster-recovery) akıllı CLI aracı.**

---

## 🎯 Özellikler

- ⚡ **Living Config Watcher:** `watchdog` ile `~/.config/herdr/config.toml`, `~/.tmux.conf`, `~/.config/nvim/lua/**/*.lua` ve `~/.zshrc` dosyalarını anlık izler.
- 🔍 **Bilingual Semantic Search (TR/EN):** Eylem isimlerini ve açıklamalarını Türkçe/İngilizce etiketlerle eşler (Örn: `sil` veya `remove` aratıldığında `prefix+x` / `remove_worktree` anında bulunur).
- 🧩 **Interactive `fzf` Popup:** Terminalin her yerinden `Ctrl+Space` veya `Alt+K` ile açılan, seçilen tuşu panoya kopyalayan yüzen arama penceresi.
- ⚔️ **Cross-Tool Conflict Detector:** Herdr, Tmux, Neovim ve Zsh arasındaki aynı tuş atamalarını (Örn: `ctrl+s` / `prefix+j` çakışmaları) tespit eder ve uyarır.
- 📜 **Trackable SQLite Audit Log:** Yapılan her ekleme (`ADDED`), güncelleme (`UPDATED`), silme (`DELETED`) ve çakışmayı (`CONFLICT_DETECTED`) zaman damgasıyla kaydeder.
- 💾 **Disaster Recovery & GitHub Backup:** `omnikey_export.json` ve `restore.sh` sayesinde bilgisayar formatlandığında tek komutla sıfır kayıpla tüm yapılandırmayı ve kısayol hafızasını geri yükler.
- 🔭 **Neovim Telescope Extension:** Neovim içinde `<leader>sk` ile tüm sistem kısayollarını arayabilme.

---

## 📦 Kurulum ve Hızlı Başlangıç

### 1. Tek Komutla Kurulum
```bash
cd omnikey
./install.sh
```

Bu komut:
1. Python paketini kurar (`pip install -e .`).
2. `omnikey` komutunu sisteme bağlar.
3. Tüm konfigürasyon dosyalarınızı (`herdr`, `tmux`, `nvim`, `zsh`) SQLite veritabanına indeksler.
4. `~/.zshrc` dosyasına ZLE widget ve kısayollarını ekler.
5. GitHub için ilk anlık yedek (`omnikey_export.json`) dosyasını üretir.

---

## 🚀 Kullanım ve CLI Komutları

| Komut | Açıklama |
| :--- | :--- |
| `omnikey search [sorgu]` | `fzf` ile interaktif arama yapar, Enter ile tuşu panoya kopyalar |
| `omnikey list` | Tüm kayıtlı kısayolları renkli tablo olarak listeler (`--json` destekler) |
| `omnikey sync` | Tüm konfigürasyon dosyalarını yeniden tarayıp veritabanını günceller |
| `omnikey conflicts` | Sistemdeki araçlar arası tuş çakışmalarını analiz eder |
| `omnikey history` | Değişiklik geçmişini ve audit log kayıtlarını listeler |
| `omnikey add <combo> <desc>` | Manuel kısayol/not ekler (Örn: `omnikey add "prefix+w" "Workspace list" -t herdr`) |
| `omnikey remove <id>` | Belirtilen ID'ye sahip kısayolu siler |
| `omnikey watch` | Arka planda konfigürasyon dosyalarını canlı izleyen daemon'ı başlatır |
| `omnikey export` | Veritabanını Git için `omnikey_export.json` dosyasına aktarır |
| `omnikey import <dosya>` | JSON yedeğinden veritabanını geri yükler |
| `omnikey doctor` | Sistem sağlık ve dosya bağlantı kontrollerini çalıştırır |

---

## 🔄 Format Sonrası Kurtarma (Disaster Recovery)

Bilgisayarınızı sıfırlayıp repoyu tekrar klonladığınızda:

```bash
cd omnikey
./restore.sh
```

`restore.sh` scripti:
1. Paketi ve bağımlılıkları yükler.
2. `omnikey_export.json` yedeğinden tüm geçmişi ve kısayolları SQLite'a aktarır.
3. Yeni sistemdeki mevcut dosyalarla diff kontrolü yaparak canlı senkronize eder.
4. Terminal kısayollarını (`Ctrl+Space`) aktif eder.

---

## ⌨️ Shell & Neovim Entegrasyonları

### Zsh Entegrasyonu
`~/.zshrc` içerisine otomatik eklenir:
```zsh
source "/path/to/omnikey/omnikey/integrations/omnikey.zsh"
```
- **Kısayol:** `Ctrl+Space` veya `Alt+K` ile terminalde anında `fzf` penceresi açılır.
- **Kısaltmalar:** `ok` (omnikey), `oks` (search), `okl` (list), `okc` (conflicts), `okw` (watch).

### Neovim Telescope Entegrasyonu
`~/.config/nvim/lua/plugins/omnikey.lua` veya init dosyanıza ekleyin:
```lua
local omnikey = require("omnikey.integrations.omnikey")
vim.keymap.set("n", "<leader>sk", omnikey.search_keybindings, { desc = "Search all system keybindings" })
```

---

## 🧪 Testleri Çalıştırma

```bash
python3 -m unittest discover -s tests -v
```

---

## 🏛️ Mimari Şeması

```
┌────────────────────────────────────────────────────────┐
│  GİRDİ KATMANI (Living / Hot-Reload)                   │
│  - Config Watcher (Herdr, Neovim, Tmux, Zsh)           │
│  - Manuel CLI / Prompt Girdileri (Ad-hoc notes)        │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│  VERİ & İZLEME KATMANI (Trackable Storage)            │
│  - SQLite Veritabanı (~/.config/omnikey/omnikey.db)    │
│  - Audit Log (Değişiklik Geçmişi & Çakışma Kayıtları)  │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│  AI & ANLAMSAL ARAMA MOTORU (Semantic & Conflict)      │
│  - Otomatik Türkçe/İngilizce Etiketleme (Bilingual)   │
│  - Çakışma Tespit Analizörü (Conflict Detection)      │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│  ERİŞİM VE ARAYÜZ KATMANI (Fast Search UI)            │
│  - Terminal Yüzen Pencere (fzf popup + clipboard copy) │
│  - Neovim Telescope Custom Picker                      │
└────────────────────────────────────────────────────────┘
```
