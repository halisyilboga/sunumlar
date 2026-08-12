# 🤖 OmniKey — Dynamic Keybinding & Context Tracker Agent

> **Tüm terminal ekosistemindeki (Herdr, Neovim, Tmux, Zsh) kısayolları canlı izleyen, anlamsal (TR/EN) arama sunan, çakışmaları tespit eden ve format sonrası tek komutla kurtarılabilen (disaster-recovery) akıllı CLI aracı.**

---

## 🎯 Özellikler

- ⚡ **Living Config Watcher:** `watchdog` ile `~/.config/herdr/config.toml`, `~/.tmux.conf`, `~/.config/nvim/lua/**/*.lua` ve `~/.zshrc` dosyalarını anlık izler.
- 🦙 **Herdr Official CLI & Keymaps:** `herdr session attach`, `herdr session list`, `herdr workspace/worktree`, `herdr server reload-config` ve tüm resmi prefix kısayollarını (`prefix+?`, `prefix+s`, `prefix+d/q`, `prefix+w`, `prefix+g`, `prefix+shift+n/g/w/d`, `prefix+c`, `prefix+z`, `prefix+v/-`, `prefix+r`, `prefix+b` vb.) içerir.
- 🪟 **Tmux Official CLI & Keymaps:** `tmux attach -t`, `tmux a`, `tmux ls`, `tmux new -s`, `tmux kill-session` ve tüm standart kısayolları (`prefix+d`, `prefix+s`, `prefix+w`, `prefix+c`, `prefix+,`, `prefix+$`, `prefix+x`, `prefix+%/"`, `prefix+z`, `prefix+[` vb.) içerir.
- ✏️ **Vim / Neovim Power Commands:** `:%s/eski/yeni/g`, `:%s/eski/yeni/gc`, `:g/pattern/d`, `<C-w>v/s/q/=`, `:bnext/:bprev/:bd`, `gg/G/%/*/#`, `v/V/<C-v>`, `qa/@a/@@`, `za/zc/zo/zR/zM`, `D/C/dd/cc/yy/p/P/u/<C-r>` vb.
- 🐧 **Linux & CLI Cheat Sheet:** En sık kullanılan dosya bulma (`find`, `locate`, `fd`, `ripgrep`), port/süreç yönetimi (`lsof`, `kill -9`, `htop`), arşivleme (`tar`, `zip`), servisler (`systemctl`, `brew services`), ağ (`curl`, `rsync`, `ssh`, `ss`, `dig`) ve Git kurtarma komutlarını içerir.
- 🔍 **Bilingual Semantic Search (TR/EN):** Eylem isimlerini ve açıklamalarını Türkçe/İngilizce etiketlerle eşler (Örn: `herdr onceki session attach et` veya `portu kullanan süreci öldür` anında bulunur).
- 🎛️ **Canlı Tool Filtreleri:** `@linux`, `@nvim`, `@herdr`, `@tmux`, `@zsh` etiketleri veya `Ctrl+A/L/N/H/T/Z` kısayollarıyla araçlar arası anında geçiş.
- 🧩 **Interactive `fzf` Popup:** Terminalin her yerinden `Ctrl+Space` veya `Alt+K` ile açılan, seçilen komutu/tuşu panoya kopyalayan yüzen arama penceresi.
- ⚔️ **Cross-Tool Conflict Detector:** Herdr, Tmux, Neovim ve Zsh arasındaki aynı tuş atamalarını tespit eder ve uyarır.
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

---

## 🚀 Kullanım ve Arama Filtreleri

### A) İnteraktif Arama & Canlı Filtreler (FZF Popup)
Terminalde `Ctrl+Space` veya `Alt+K` bastığınızda açılan pencerede:
* **Hızlı Tuş Filtreleri:**
  * `Ctrl + A` ➜ **Tümü (All Tools)**
  * `Ctrl + L` ➜ **Linux / CLI Komutları**
  * `Ctrl + N` ➜ **Neovim / NvChad**
  * `Ctrl + H` ➜ **Herdr**
  * `Ctrl + T` ➜ **Tmux**
  * `Ctrl + Z` ➜ **Zsh / Readline**
* **Etiketle Filtreleme:** Arama kutusuna `@linux`, `@nvim`, `@herdr`, `@tmux`, `@zsh` yazabilirsiniz (Örn: `@linux dosya bul` veya `@nvim buffer`).

### B) CLI Komutları

| Komut | Açıklama |
| :--- | :--- |
| `omnikey search [sorgu]` | `fzf` ile interaktif arama yapar, Enter ile tuşu panoya kopyalar |
| `omnikey search -t linux "port"` | Sadece Linux komutlarında arama yapar |
| `omnikey search -t neovim "buffer"` | Sadece Neovim kısayollarında arama yapar |
| `omnikey list` | Tüm kayıtlı kısayolları renkli tablo olarak listeler (`--json` destekler) |
| `omnikey sync` | Tüm konfigürasyon dosyalarını yeniden tarayıp veritabanını günceller |
| `omnikey conflicts` | Sistemdeki araçlar arası tuş çakışmalarını analiz eder |
| `omnikey history` | Değişiklik geçmişini ve audit log kayıtlarını listeler |
| `omnikey watch` | Arka planda konfigürasyon dosyalarını canlı izleyen daemon'ı başlatır |
| `omnikey export` | Veritabanını Git için `omnikey_export.json` dosyasına aktarır |
| `omnikey import <dosya>` | JSON yedeğinden veritabanını geri yükler |

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
