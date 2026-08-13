# OmniKey Roadmap & Future Features

This document outlines potential features and ideas to turn OmniKey into a robust, community-driven open-source project.

## Design Principles

- **Stay lightweight**: the core must keep working with only the Python standard library + `watchdog` + `sqlite3` (fzf stays optional, as today).
- **No LLM dependency**: all features below are rule-based. No model downloads, no API keys, no network at runtime.
- **Optional heavy dependencies**: features that would pull in big libraries (Textual, reportlab, ...) must be lazy-loaded and gracefully degrade if missing (`omnikey doctor` reports them).
- **No telemetry**: everything stays local; sharing features are explicitly opt-in.

## Shared Core Infrastructure (step 0 for every feature below)

These generic parts will be added anyway and are a single shared step that each feature builds on:

- [ ] Versioned DB schema migrations (simple `schema_version` table; feature branches add migrations instead of editing `init_db`).
- [ ] CLI subcommand registration pattern so new commands drop in without touching `build_parser` too much.
- [ ] Optional-dependency helper: `import_optional("textual")` + uniform error message, wired into `omnikey doctor`.
- [ ] Extension points for the plugin dir (`~/.config/omnikey/plugins/`) that all future modules can reuse.
- [ ] GitHub Actions CI: `python3 -m unittest discover -s tests` on 3.9 / 3.11 / 3.12 + lint.
- [ ] Test fixtures for temp config dirs / DB so features are testable in isolation.

---

## 🛠️ Core & Architecture Improvements

### 1. Plugin Architecture (Custom Parsers)

Make it extremely easy for the community to write custom parsers. Users should be able to drop a simple Python file into a `~/.config/omnikey/plugins/` directory to teach OmniKey how to parse shortcuts for tools like VSCode, Kitty, Alacritty, i3wm/Sway, or Hyprland.

**Development steps:**
- [ ] Step 0 (shared core): plugin loader scanning `~/.config/omnikey/plugins/*.py` (import, `BaseParser` subclass discovery, never crash on a bad plugin).
- [ ] Registry integration: `ALL_PARSERS` becomes builtin parsers + loaded plugins; `get_parser_for_file` also consults plugin `can_handle`.
- [ ] `omnikey plugins list` command (name, path, status) + `--strict` flag to disable broken plugins.
- [ ] Write a Kitty/Alacritty example parser as the community template + `PLUGIN.md` doc with the 10-line minimal example.
- [ ] Unit tests: loader isolation, duplicate parser precedence (user plugin beats builtin), broken-file handling.

### 2. Interactive Conflict Resolver

Upgrade `omnikey conflicts` from a simple reporting tool to an interactive TUI. When a conflict is found, OmniKey should ask the user how to resolve it ("Delete this one or assign a new key?") and automatically edit the underlying configuration file (e.g., `.tmux.conf` or `config.toml`) based on the choice.

**Development steps:**
- [ ] Step 0 (shared core): reuse existing `ConflictDetector`; group conflicts by normalized key with suggested actions (keep / reassign / ignore-forever).
- [ ] "Ignore list" persistence (`settings` table) so already-reviewed conflicts disappear from reports.
- [ ] Config write-back layer: format-aware editors for tmux.conf (`unbind-key` / `bind-key`) and Herdr `config.toml` (`[keys]` line rewrite); other formats = manual hint for v1.
- [ ] `omnikey resolve` interactive prompt loop (plain `input()` first, no TUI dependency; optional Rich later).
- [ ] Every resolution logged to audit + export snapshot re-generated.
- [ ] Unit tests: each format editor round-trip (parse → edit → re-parse), ignore-list behavior.

### 3. Cross-OS Key Translator (Dotfile Migration)

Provide a tool for users migrating between OSes (e.g., macOS to Linux/Windows). OmniKey could automatically detect `Cmd` (Super) based bindings in macOS dotfiles and safely translate them to `Ctrl` or `Alt` equivalents for Linux environments.

**Development steps:**
- [ ] Step 0 (shared core): build on `normalize_key_combo` (extend it to canonicalize `cmd`/`super`).
- [ ] Mapping rules table (`cmd → ctrl` for Linux / `cmd → alt` for Windows) with per-tool exceptions.
- [ ] Safety check: only translate when the target key is **not already bound** in the target config (reuse conflict detector).
- [ ] `omnikey migrate --from macos --to linux [--dry-run]`; dry-run shows a diff before any write.
- [ ] Unit tests: collision avoidance, unknown key passthrough, `--dry-run` writes nothing.

---

## 🎨 UI & Export Capabilities

### 4. Cheat Sheet Generator (PDF / HTML / Markdown Export)

Allow users to generate beautiful cheat sheets specific to their workflow. A command like `omnikey export --tool herdr --format pdf` would use a stylish template to output a ready-to-print or easy-to-reference document of their current bindings.

**Development steps:**
- [ ] Step 0 (shared core): reusable `export_data()` as the single source; add grouping/filtering options (by tool, mode, tag).
- [ ] Markdown template first (zero dependencies, immediate value).
- [ ] HTML template with clean CSS (print-friendly); PDF = optional dependency (`weasyprint`/`reportlab`), lazy-loaded, `doctor`-reported when missing.
- [ ] `omnikey cheat --tool X --format md|html|pdf --out file` command.
- [ ] Unit tests: golden-file comparisons for md/html output; PDF skipped gracefully when dependency absent.

### 5. Usage Statistics & Heatmap

Track which shortcuts the user actually looks up and run, and surface personal usage data: most-used keys per tool, never-used bindings, a simple heatmap. Feeds the TUI dashboard and can optionally re-rank search results.

**Development steps:**
- [ ] Step 0 (shared core): schema migration adding `last_used` + `use_count` columns.
- [ ] Record usage on every selection point: fzf Enter, Neovim picker, action runner (`db.record_usage(kb_id)`).
- [ ] `omnikey stats` command: top used / never used / per-tool breakdown (no new dependencies, plain tables).
- [ ] Heatmap export: reuse cheat-sheet HTML template (feature #4) with frequency highlighting.
- [ ] Optional search ranking boost: `--rank-by-usage` flag on `search`/`list`.
- [ ] Unit tests: usage increments, ordering, ranking flag.

### 6. Rich TUI Dashboard

While `fzf` is fast, adding a fully-featured Text User Interface (TUI) using libraries like [Textual](https://textual.textualize.io/) or [Rich](https://rich.readthedocs.io/en/stable/) would be a game-changer. A command like `omnikey ui` could show visual statistics (most conflicted keys, total shortcuts), allow browsing by tool, and provide an interface for managing files.

**Development steps:**
- [ ] Step 0 (shared core): optional-dependency helper — `omnikey ui` must print a clear install hint if Textual/Rich is missing (fallback: current fzf search).
- [ ] Browse screen: list by tool/mode, live search, detail panel (reuses formatter).
- [ ] Stats view: wired to feature #5 (usage) + conflict count summary (feature #2).
- [ ] Basic actions inside TUI: copy key, mark conflict ignored, run command (feature #8).
- [ ] Unit tests: view-model logic (filtering/grouping) kept dependency-free so it is testable without Textual.

---

## 🧠 Learning & Productivity

### 7. Gamification: "Learn Mode" (Shortcut Tutor)

Help users build muscle memory through spaced repetition. Running `omnikey learn --tool neovim` would launch a flashcard-style game in the terminal, prompting the user with an action (e.g., "Open file explorer") and waiting for them to press the correct key combination.

**Development steps:**
- [ ] Step 0 (shared core): schema migration for learning state (per-kb: box level, next review date, streak).
- [ ] Flashcard engine: pick a binding from the requested tool, show description, wait for key input (plain terminal first; no dependency).
- [ ] Simple 3-box Leitner spaced-repetition; progress persisted and resumable.
- [ ] `omnikey learn --tool X [--mode quiz]`; quiz mode = multiple-choice over 4 options for variety.
- [ ] Unit tests: scheduling logic, answer scoring, per-tool filtering, empty-DB handling.

### 8. Action Runner (Command Palette)

Evolve OmniKey beyond just a reference tool. When a shortcut maps to a CLI command, bash script, or git alias, pressing `Enter` on the search result should directly **execute** that command in the current terminal, turning OmniKey into a powerful Command Palette.

**Development steps:**
- [ ] Step 0 (shared core): safe execution layer — only `cli`/`linux`/`zsh`-tool entries are executable; confirm prompt for anything not flagged `manual`; `--dry-run` prints instead of running.
- [ ] fzf key layout: `Enter` copies (today's behavior), `Alt+Enter` executes; new `omnikey run <query>` non-interactive variant.
- [ ] Shell integration: execute in the current shell context (zsh widget emits the command via `zle`), fallback to `sh -c` subprocess with visible output.
- [ ] Security: per-source allowlist (`omnikey run --allow builtin://git_recipes`), never execute unknown manual entries without explicit confirmation.
- [ ] Unit tests: allowlist logic, dry-run, non-executable entry rejection.

---

## 🌐 Cloud & Community

### 9. OmniKey Hub (Shortcut Packs & Sharing)

Enable a feature like `omnikey publish` to export a user's keybinding layout (JSON/DB) to a Gist or a centralized OmniKey Hub. Other users could run `omnikey install @username/tmux` to instantly import and explore a popular developer's shortcut setup. Shortcut collections ("packs": e.g. vim-cheatsheet, docker-commands) install like plugins.

**Development steps:**
- [ ] Step 0 (shared core): stable pack format = JSON manifest (`tool`, `version`, `bindings[]`) versioned alongside `omnikey_export.json`.
- [ ] `omnikey pack install/uninstall/list` for local packs; `omnikey install @user/name` pulls from a Gist or plain GitHub repo via `curl` (no SDK dependency).
- [ ] Import merge strategy: never overwrite existing user bindings — packs land as new `source_file="pack://..."` entries; conflicts reported through the normal detector.
- [ ] `omnikey publish` (opt-in): push pack to a Gist/private repo with `gh` or a plain git push; token stored only on demand, never telemetry.
- [ ] Unit tests: manifest validation, merge-without-overwrite, pack uninstall cleanup.

### 10. Multi-Machine Sync (Git-Based)

Keep the same shortcut memory on every machine: sync the SQLite state through the existing Git snapshot (`omnikey_export.json`) with real merge semantics, so machines converge instead of overwriting each other.

**Development steps:**
- [ ] Step 0 (shared core): fix `import_data` to preserve `last_updated` and ids instead of resetting timestamps.
- [ ] Merge engine: 3-way merge per `(tool, combo, mode)` key — keep newer `last_updated`, keep manual over file-sourced, never delete the other side silently.
- [ ] `omnikey sync-git push|pull` (or `omnikey backup`) driving git add/commit/pull-rebase/export; no new runtime dependency (uses `git` binary).
- [ ] Conflict report after every merge (`omnikey conflicts`), plus `--dry-run` diff view.
- [ ] Unit tests: same-key-different-value, tombstone handling (deleted on A, kept on B), manual-binding priority.

---

## ❌ Out of Scope (for now)

These were considered and deliberately excluded to keep OmniKey lightweight and dependency-free:

- **LLM-powered natural-language search** ("tell me what you want to do") — needs a model runtime; the rule-based TR/EN tagger covers the core use case.
- **AI/ergonomic key recommendations** — needs analytics and per-user models; revisit only if stats (#5) prove useful.
- **Global hotkey daemon (Spotlight/Raycast-style floating window)** — always-on background process + GUI overlay is a different project; the terminal-first fzf/zsh integration stays the UX.
- **Cloud backend / accounts** — sharing stays Gist/git-based, fully opt-in.
