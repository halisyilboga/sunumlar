-- OmniKey Neovim Telescope Custom Picker Extension
-- Place in ~/.config/nvim/lua/plugins/omnikey.lua or source directly

local M = {}

function M.search_keybindings(opts)
  opts = opts or {}
  local pickers = require("telescope.pickers")
  local finders = require("telescope.finders")
  local conf = require("telescope.config").values
  local actions = require("telescope.actions")
  local action_state = require("telescope.actions.state")

  -- Fetch keybindings from omnikey CLI as JSON
  local handle = io.popen("python3 -m omnikey list --json")
  if not handle then
    vim.notify("OmniKey CLI not found or failed to execute", vim.log.levels.ERROR)
    return
  end

  local result = handle:read("*a")
  handle:close()

  local ok, kbs = pcall(vim.json.decode, result)
  if not ok or type(kbs) ~= "table" then
    vim.notify("Failed to parse OmniKey output", vim.log.levels.WARN)
    return
  end

  pickers.new(opts, {
    prompt_title = "OmniKey Keybinding Tracker",
    finder = finders.new_table {
      results = kbs,
      entry_maker = function(entry)
        local tool = string.upper(entry.tool or "CUSTOM")
        local combo = entry.key_combo or ""
        local desc = entry.description or entry.action_raw or ""
        local display = string.format("[%-7s] %-16s ➜ %s", tool, combo, desc)
        return {
          value = entry,
          display = display,
          ordinal = string.format("%s %s %s %s", tool, combo, desc, table.concat(entry.tags or {}, " ")),
        }
      end,
    },
    sorter = conf.generic_sorter(opts),
    attach_mappings = function(prompt_bufnr, map)
      actions.select_default:replace(function()
        actions.close(prompt_bufnr)
        local selection = action_state.get_selected_entry()
        if selection and selection.value then
          local combo = selection.value.key_combo
          vim.fn.setreg("+", combo)
          vim.notify("Copied keybinding to clipboard: " .. combo, vim.log.levels.INFO)
        end
      end)
      return true
    end,
  }):find()
end

-- Keymap helper: vim.keymap.set("n", "<leader>sk", require("omnikey").search_keybindings, { desc = "Search all system keybindings" })

return M
