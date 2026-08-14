-- ==============================================================================
-- Neovim Complete Keybindings Template
-- Target: ~/.config/nvim/lua/mappings.lua
-- ==============================================================================

local map = vim.keymap.set

-- 1. Genel ve Navigasyon
map("n", ";", ":", { desc = "CMD komut moduna gir" })
map("i", "jk", "<ESC>", { desc = "Insert modundan hızlı çıkış" })
map("n", "<leader>w", "<cmd>w<cr>", { desc = "Dosyayı kaydet (Save)" })
map("n", "<leader>q", "<cmd>q<cr>", { desc = "Pencereyi kapat / Çıkış" })
map("n", "<leader>x", "<cmd>bdelete<cr>", { desc = "Aktif tamponu kapat (Buffer close)" })
map("n", "<ESC>", "<cmd>nohlsearch<cr>", { desc = "Arama vurgularını temizle" })

-- 2. Pencere Navigasyonu & Bölmeler (Splits)
map("n", "<C-h>", "<C-w>h", { desc = "Soldaki pencereye geç" })
map("n", "<C-l>", "<C-w>l", { desc = "Sağdaki pencereye geç" })
map("n", "<C-j>", "<C-w>j", { desc = "Aşağıdaki pencereye geç" })
map("n", "<C-k>", "<C-w>k", { desc = "Yukarıdaki pencereye geç" })
map("n", "<leader>sv", "<cmd>vsplit<cr>", { desc = "Pencereyi dikey böl (vsplit)" })
map("n", "<leader>sh", "<cmd>split<cr>", { desc = "Pencereyi yatay böl (split)" })
map("n", "<leader>se", "<C-w>=", { desc = "Pencereleri eşit boyuta getir" })

-- 3. Telescope Dosya ve Metin Arama
map("n", "<leader>ff", "<cmd>Telescope find_files<cr>", { desc = "Projede dosya ara (Find files)" })
map("n", "<leader>fg", "<cmd>Telescope live_grep<cr>", { desc = "Projede metin ara (Live grep)" })
map("n", "<leader>fb", "<cmd>Telescope buffers<cr>", { desc = "Açık tamponları listele (Buffers)" })
map("n", "<leader>fh", "<cmd>Telescope help_tags<cr>", { desc = "Yardım etiketlerini ara" })
map("n", "<leader>fo", "<cmd>Telescope oldfiles<cr>", { desc = "Son açılan dosyaları listele" })

-- 5. Dosya Gezgini (NvimTree) & Lazygit
map("n", "<C-n>", "<cmd>NvimTreeToggle<cr>", { desc = "Dosya ağacını aç/kapat (NvimTree)" })
map("n", "<leader>e", "<cmd>NvimTreeToggle<cr>", { desc = "Dosya ağacını aç/kapat" })
map("n", "<leader>lg", "<cmd>LazyGit<cr>", { desc = "Lazygit terminalini aç" })
