# 📋 Neovim Kısayolları (Keybindings) Referans Kataloğu

Bu belge, modern bir Neovim geliştirme ortamında (NvChad / LazyVim / Standart Neovim) en çok kullanılan standart, dosya arama, LSP ve pencere yönetimi kısayollarını listeler.

---

## ⚙️ Yapılandırma Dosyası Konumu
* **Yol:** `~/.config/nvim/lua/mappings.lua` veya `~/.config/nvim/init.lua`

---

## 1. ⚡ Genel & Navigasyon Kısayolları

| Mod | Tuş Kombinasyonu | Eylem | Açıklama |
| :--- | :--- | :--- | :--- |
| `n` | `;` | `:` | Komut moduna hızlı giriş |
| `i` | `jk` | `<ESC>` | Insert modundan çıkış (ESC alternatifi) |
| `n` | `<leader>w` | `:w<CR>` | Dosyayı hızlı kaydetme |
| `n` | `<leader>q` | `:q<CR>` | Mevcut pencereden çıkış |
| `n` | `<leader>x` | `:bdelete<CR>` | Aktif tamponu (buffer) kapatma |
| `n` | `<ESC>` | `:nohlsearch<CR>` | Arama vurgulamalarını temizleme |

---

## 2. 🪟 Pencere (Window) ve Bölme (Split) Yönetimi

| Mod | Tuş Kombinasyonu | Eylem | Açıklama |
| :--- | :--- | :--- | :--- |
| `n` | `<C-h>` | `<C-w>h` | Soldaki pencereye geçiş |
| `n` | `<C-l>` | `<C-w>l` | Sağdaki pencereye geçiş |
| `n` | `<C-j>` | `<C-w>j` | Aşağıdaki pencereye geçiş |
| `n` | `<C-k>` | `<C-w>k` | Yukarıdaki pencereye geçiş |
| `n` | `<leader>sv` | `:vsplit<CR>` | Pencereyi dikey böl (yan yana) |
| `n` | `<leader>sh` | `:split<CR>` | Pencereyi yatay böl (alt alta) |
| `n` | `<leader>se` | `<C-w>=` | Pencereleri eşit boyuta getir |
| `n` | `<leader>sx` | `:close<CR>` | Aktif pencere bölmesini kapat |

---

## 3. 🔍 Telescope / Dosya ve Metin Arama

| Mod | Tuş Kombinasyonu | Eylem | Açıklama |
| :--- | :--- | :--- | :--- |
| `n` | `<leader>ff` | `Telescope find_files` | Projede dosya ara |
| `n` | `<leader>fa` | `Telescope find_files follow=true no_ignore=true hidden=true` | Gizli ve tüm dosyaları ara |
| `n` | `<leader>fg` | `Telescope live_grep` | Proje içinde metin ara (Live Grep) |
| `n` | `<leader>fb` | `Telescope buffers` | Açık tamponları (buffers) listele |
| `n` | `<leader>fo` | `Telescope oldfiles` | Son açılan dosyalar |
| `n` | `<leader>fh` | `Telescope help_tags` | Yardım etiketlerini ara |

---

## 4. 🧠 LSP (Language Server) & Kod Zekası

| Mod | Tuş Kombinasyonu | Eylem | Açıklama |
| :--- | :--- | :--- | :--- |
| `n` | `gd` | `vim.lsp.buf.definition` | Tanıma git (Go to Definition) |
| `n` | `gD` | `vim.lsp.buf.declaration` | Deklarasyona git |
| `n` | `gr` | `vim.lsp.buf.references` | Referansları listele |
| `n` | `gi` | `vim.lsp.buf.implementation` | İmplementasyona git |
| `n` | `K` | `vim.lsp.buf.hover` | Dokümantasyon ve tip bilgisini göster |
| `n` | `<leader>ca` | `vim.lsp.buf.code_action` | Kod eylemleri (Quick Fix / Refactor) |
| `n` | `<leader>rn` | `vim.lsp.buf.rename` | Sembolü tüm projede yeniden adlandır |
| `n` | `<leader>d` | `vim.diagnostic.open_float` | Satırdaki hatayı/uyarıyı pencerede aç |
| `n` | `[d` | `vim.diagnostic.goto_prev` | Önceki hata/uyarıya git |
| `n` | `]d` | `vim.diagnostic.goto_next` | Sonraki hata/uyarıya git |
| `n` | `<leader>fm` | `vim.lsp.buf.format` | Kodu otomatik formatla |

---

## 5. 📂 Dosya Ağacı ve Git Entegrasyonu

| Mod | Tuş Kombinasyonu | Eylem | Açıklama |
| :--- | :--- | :--- | :--- |
| `n` | `<leader>e` / `<C-n>` | `:NvimTreeToggle<CR>` | Dosya gezgini kenar çubuğunu aç/kapat |
| `n` | `<leader>lg` / `<leader>gg`| `lazygit` | Terminalde Lazygit aç |
| `n` | `<leader>gb` | `gitsigns.blame_line` | Satırın git blame kaydını göster |
| `n` | `]c` | `gitsigns.next_hunk` | Sonraki git değişikliğine git |
| `n` | `[c` | `gitsigns.prev_hunk` | Önceki git değişikliğine git |
