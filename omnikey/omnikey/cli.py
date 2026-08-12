"""CLI Command Interface for OmniKey."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from omnikey import __version__
from omnikey.config import (
    get_config_dir,
    get_db_path,
    get_default_watch_targets,
    get_export_path,
)
from omnikey.db import Database
from omnikey.models import Keybinding
from omnikey.parsers import ALL_PARSERS, get_parser_for_file
from omnikey.parsers.herdr import HerdrParser
from omnikey.parsers.linux_commands import LinuxCommandsParser
from omnikey.parsers.neovim import NeovimParser
from omnikey.parsers.shell_defaults import ShellDefaultsParser
from omnikey.parsers.tmux import TmuxParser
from omnikey.semantic.conflict import ConflictDetector
from omnikey.semantic.tagger import SemanticTagger
from omnikey.ui.formatter import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    color_tool,
    format_audit_history,
    format_conflicts,
    format_keybinding_detail,
    format_keybinding_row,
)
from omnikey.ui.fzf_search import find_fzf_binary, run_fzf_search
from omnikey.watcher import ConfigWatcher


def resolve_tool_filter(args, db: Database) -> Optional[List[str]]:
    """Return the effective tool restriction for search/list/conflicts.

    Explicit `-t/--tool` wins; otherwise the persisted active tools apply;
    `--all-tools` disables the restriction entirely.
    """
    if getattr(args, "all_tools", False):
        return None
    if getattr(args, "tool", None):
        return [args.tool]
    return db.get_active_tools()


def cmd_tools(args, db: Database) -> None:
    """Manage active tools (which tools appear in results by default)."""
    known_tools = sorted(
        set(["herdr", "tmux", "neovim", "zsh", "builtin", "custom"])
        | {kb.tool for kb in db.list_keybindings()}
    )
    action = getattr(args, "tools_action", None)

    if action == "enable":
        for tool in args.tools:
            if tool not in known_tools:
                print(f"{YELLOW}Warning: '{tool}' is not a known tool.{RESET}")
        current = db.get_active_tools() or known_tools
        db.set_active_tools(sorted(set(current) | set(args.tools)))
        print(f"{GREEN}✓ Active tools:{RESET} {', '.join(db.get_active_tools() or known_tools)}")
        return

    if action == "disable":
        for tool in args.tools:
            if tool not in known_tools:
                print(f"{YELLOW}Warning: '{tool}' is not a known tool.{RESET}")
        current = db.get_active_tools() or known_tools
        db.set_active_tools([t for t in current if t not in args.tools])
        active = db.get_active_tools()
        print(f"{GREEN}✓ Active tools:{RESET} {', '.join(active) if active else '(none — use --all-tools to see everything)'}")
        return

    if action == "reset":
        db.set_active_tools(None)
        print(f"{GREEN}✓ Reset: all tools are active again.{RESET}")
        return

    # Default: show status table
    active_set = set(db.get_active_tools() or known_tools)
    print(f"{BOLD}Tool Status (active tools are shown in results by default):{RESET}\n")
    for tool in known_tools:
        count = len(db.list_keybindings(tool=tool))
        mark = f"{GREEN}● active{RESET}" if tool in active_set else f"{DIM}○ inactive{RESET}"
        print(f"  {mark:<14} {color_tool(tool):<10} {DIM}{count} bindings{RESET}")
    print(
        f"\nUsage: {BOLD}omnikey tools enable <tool...>{RESET} | "
        f"{BOLD}disable <tool...>{RESET} | {BOLD}reset{RESET}"
    )


def cmd_sync(args, db: Database) -> None:
    """Scan and synchronize all configuration files."""
    custom_path = getattr(args, "path", None)
    if custom_path:
        target_path = Path(custom_path).expanduser().resolve()
        if not target_path.exists():
            print(f"{RED}Error: Path '{target_path}' does not exist.{RESET}")
            return
        parser = get_parser_for_file(target_path)
        if not parser:
            print(f"{YELLOW}Warning: No parser found for '{target_path}'. Trying all parsers...{RESET}")
            for p in ALL_PARSERS:
                kbs = p.parse(target_path)
                if kbs:
                    parser = p
                    break
        if not parser:
            print(f"{RED}Could not parse keybindings from '{target_path}'.{RESET}")
            return
        kbs = parser.parse(target_path)
        stats = db.sync_file_keybindings(tool=parser.tool_name, source_file=str(target_path), new_kbs=kbs)
        print(f"{color_tool(parser.tool_name):<18} {DIM}{target_path}{RESET}")
        print(f"  └─ Parsed: {len(kbs)} bindings | {GREEN}+{stats['added']}{RESET} {YELLOW}~{stats['updated']}{RESET} {RED}-{stats['deleted']}{RESET} {DIM}={stats['unchanged']}{RESET}")
        return

    print(f"{BOLD}Scanning and synchronizing configuration files...{RESET}\n")
    targets = get_default_watch_targets()

    total_stats = {"added": 0, "updated": 0, "deleted": 0, "unchanged": 0}
    found_files = 0

    for tool_name, paths in targets.items():
        for path in paths:
            if not path.exists():
                continue

            resolved = path.resolve()
            parser = get_parser_for_file(resolved) or get_parser_for_file(path)
            if not parser:
                continue

            found_files += 1
            kbs = parser.parse(resolved)
            stats = db.sync_file_keybindings(
                tool=parser.tool_name,
                source_file=str(resolved),
                new_kbs=kbs,
            )

            for k in total_stats:
                total_stats[k] += stats[k]

            print(
                f"{color_tool(parser.tool_name):<18} {DIM}{resolved}{RESET}\n"
                f"  └─ Parsed: {len(kbs)} bindings | "
                f"{GREEN}+{stats['added']}{RESET} "
                f"{YELLOW}~{stats['updated']}{RESET} "
                f"{RED}-{stats['deleted']}{RESET} "
                f"{DIM}={stats['unchanged']}{RESET}"
            )

    # Always sync Herdr standard CLI commands and default keybindings
    herdr_kbs = HerdrParser.get_all_herdr_defaults()
    h_stats = db.sync_file_keybindings(
        tool="herdr",
        source_file="builtin://herdr_standards",
        new_kbs=herdr_kbs,
    )
    for k in total_stats:
        total_stats[k] += h_stats[k]
    found_files += 1
    print(
        f"{color_tool('herdr'):<18} {DIM}builtin://herdr_standards (CLI & Defaults){RESET}\n"
        f"  └─ Parsed: {len(herdr_kbs)} bindings | "
        f"{GREEN}+{h_stats['added']}{RESET} "
        f"{YELLOW}~{h_stats['updated']}{RESET} "
        f"{RED}-{h_stats['deleted']}{RESET} "
        f"{DIM}={h_stats['unchanged']}{RESET}"
    )

    # Always sync Tmux standard CLI commands and default keybindings
    tmux_kbs = TmuxParser.get_all_tmux_defaults()
    t_stats = db.sync_file_keybindings(
        tool="tmux",
        source_file="builtin://tmux_standards",
        new_kbs=tmux_kbs,
    )
    for k in total_stats:
        total_stats[k] += t_stats[k]
    found_files += 1
    print(
        f"{color_tool('tmux'):<18} {DIM}builtin://tmux_standards (CLI & Defaults){RESET}\n"
        f"  └─ Parsed: {len(tmux_kbs)} bindings | "
        f"{GREEN}+{t_stats['added']}{RESET} "
        f"{YELLOW}~{t_stats['updated']}{RESET} "
        f"{RED}-{t_stats['deleted']}{RESET} "
        f"{DIM}={t_stats['unchanged']}{RESET}"
    )

    # Always sync built-in standard Shell & Editor keybindings
    builtin_kbs = ShellDefaultsParser.get_all_builtins()
    b_stats = db.sync_file_keybindings(
        tool="builtin",
        source_file="builtin://standards",
        new_kbs=builtin_kbs,
    )
    for k in total_stats:
        total_stats[k] += b_stats[k]
    found_files += 1
    print(
        f"{color_tool('builtin'):<18} {DIM}builtin://standards (Readline, Zsh, Vim){RESET}\n"
        f"  └─ Parsed: {len(builtin_kbs)} bindings | "
        f"{GREEN}+{b_stats['added']}{RESET} "
        f"{YELLOW}~{b_stats['updated']}{RESET} "
        f"{RED}-{b_stats['deleted']}{RESET} "
        f"{DIM}={b_stats['unchanged']}{RESET}"
    )

    # Always sync Linux/Unix terminal recipes and commands
    linux_kbs = LinuxCommandsParser.get_all_linux_commands()
    l_stats = db.sync_file_keybindings(
        tool="linux",
        source_file="builtin://linux_recipes",
        new_kbs=linux_kbs,
    )
    for k in total_stats:
        total_stats[k] += l_stats[k]
    found_files += 1
    print(
        f"{color_tool('linux'):<18} {DIM}builtin://linux_recipes (Find, Ports, Tar, Git){RESET}\n"
        f"  └─ Parsed: {len(linux_kbs)} commands | "
        f"{GREEN}+{l_stats['added']}{RESET} "
        f"{YELLOW}~{l_stats['updated']}{RESET} "
        f"{RED}-{l_stats['deleted']}{RESET} "
        f"{DIM}={l_stats['unchanged']}{RESET}"
    )

    # Always sync NvChad ecosystem standards (Telescope, LSP, Gitsigns, Mason, Lazy, Treesitter, Minty)
    nvchad_kbs = NeovimParser.get_nvchad_builtins()
    nv_stats = db.sync_file_keybindings(
        tool="neovim",
        source_file="builtin://nvchad_standards",
        new_kbs=nvchad_kbs,
    )
    for k in total_stats:
        total_stats[k] += nv_stats[k]
    found_files += 1
    print(
        f"{color_tool('neovim'):<18} {DIM}builtin://nvchad_standards (Telescope, LSP, Git, Mason, Lazy){RESET}\n"
        f"  └─ Parsed: {len(nvchad_kbs)} bindings | "
        f"{GREEN}+{nv_stats['added']}{RESET} "
        f"{YELLOW}~{nv_stats['updated']}{RESET} "
        f"{RED}-{nv_stats['deleted']}{RESET} "
        f"{DIM}={nv_stats['unchanged']}{RESET}"
    )

    print("\n" + "=" * 55)
    print(
        f"{BOLD}Sync Complete!{RESET} ({found_files} files scanned)\n"
        f"Total: {GREEN}{total_stats['added']} added{RESET}, "
        f"{YELLOW}{total_stats['updated']} updated{RESET}, "
        f"{RED}{total_stats['deleted']} removed{RESET}, "
        f"{DIM}{total_stats['unchanged']} unchanged{RESET}"
    )

    # Auto-export snapshot for git backups and disaster recovery
    export_path = get_export_path()
    try:
        data = db.export_data()
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"{GREEN}✓ Auto-exported backup snapshot ({len(data['keybindings'])} bindings) to:{RESET} {export_path}")
    except Exception as e:
        print(f"{YELLOW}Notice: auto-export failed: {e}{RESET}")

    # Check conflicts after sync
    all_kbs = db.list_keybindings()
    conflicts = ConflictDetector.detect_conflicts(all_kbs)
    if conflicts:
        print(f"\n{YELLOW}⚠ Notice: {len(conflicts)} conflict(s) detected. Run 'omnikey conflicts' for details.{RESET}")


def cmd_search(args, db: Database) -> None:
    """Interactive FZF search or text search with @tool tag extraction."""
    raw_query = args.query or ""
    tool_filter = args.tool
    search_query = raw_query
    fzf_query = raw_query

    # Auto-extract @tool from query (e.g. "@linux port", "@nvim buffer", or "@herdr")
    if raw_query.startswith("@"):
        parts = raw_query.split(None, 1)
        tag = parts[0][1:].lower()
        if tag in ("nvim", "neovim"):
            tool_filter = "neovim"
        elif tag in ("linux", "cli"):
            tool_filter = "linux"
        elif tag in ("herdr", "tmux", "zsh", "builtin"):
            tool_filter = tag
        search_query = parts[1] if len(parts) > 1 else ""
        fzf_query = f"'@{tag} {search_query}".strip() if search_query else f"'@{tag} "

    tools = [tool_filter] if tool_filter else resolve_tool_filter(args, db)
    if args.no_fzf:
        kbs = db.list_keybindings(tools=tools, search=search_query)
        if not kbs:
            print(f"{YELLOW}No keybindings found.{RESET}")
            return
        print(f"\n{BOLD}Search results ({len(kbs)} found):{RESET}")
        for kb in kbs:
            print(format_keybinding_row(kb))
    else:
        run_fzf_search(db, query=fzf_query, tool=tool_filter, tools=tools)


def cmd_list(args, db: Database) -> None:
    """List keybindings in table or JSON format."""
    tools = resolve_tool_filter(args, db)
    kbs = db.list_keybindings(tools=tools, search=args.search, limit=args.limit)
    if args.json:
        print(json.dumps([kb.to_dict() for kb in kbs], indent=2, ensure_ascii=False))
        return

    if not kbs:
        print(f"{YELLOW}No keybindings found.{RESET}")
        return

    print(f"\n{BOLD}OmniKey Indexed Keybindings ({len(kbs)} total):{RESET}\n")
    for kb in kbs:
        print(format_keybinding_row(kb))
    print("")


def cmd_conflicts(args, db: Database) -> None:
    """Analyze and display keybinding conflicts."""
    all_kbs = db.list_keybindings(tools=resolve_tool_filter(args, db))
    conflicts = ConflictDetector.detect_conflicts(all_kbs)
    print(format_conflicts(conflicts))


def cmd_history(args, db: Database) -> None:
    """Display audit history (trackability log)."""
    entries = db.get_audit_history(limit=args.limit, change_type=args.type)
    print(format_audit_history(entries))


def cmd_add(args, db: Database) -> None:
    """Manually add an ad-hoc keybinding."""
    tool = args.tool or "custom"
    combo = args.combo.strip()
    desc = args.description.strip()
    action = args.action or desc
    mode = args.mode or "normal"

    tags = SemanticTagger.generate_tags(
        tool=tool,
        key_combo=combo,
        action_raw=action,
        description=desc,
        mode=mode,
    )

    kb = Keybinding(
        tool=tool,
        key_combo=combo,
        action_raw=action,
        description=desc,
        source_file="manual",
        mode=mode,
        is_manual=True,
        tags=tags,
    )

    saved = db.add_manual_keybinding(kb)
    print(f"{GREEN}✓ Added manual keybinding:{RESET} (ID: {saved.id})")
    print(format_keybinding_detail(saved))


def cmd_remove(args, db: Database) -> None:
    """Remove a keybinding by ID."""
    kb = db.get_keybinding(args.id)
    if not kb:
        print(f"{RED}Keybinding with ID {args.id} not found.{RESET}")
        return
    success = db.delete_keybinding(args.id)
    if success:
        print(f"{GREEN}✓ Removed keybinding ID {args.id} ({kb.key_combo} -> {kb.description or kb.action_raw}){RESET}")


def cmd_watch(args, db: Database) -> None:
    """Start real-time background config file watcher."""
    watcher = ConfigWatcher(db)
    watcher.start()


def cmd_export(args, db: Database) -> None:
    """Export database to JSON file for Git versioning and backups."""
    export_path = Path(args.output) if args.output else get_export_path()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    data = db.export_data()

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"{GREEN}✓ Exported {len(data['keybindings'])} keybindings to:{RESET} {export_path}")


def cmd_import(args, db: Database) -> None:
    """Import database from JSON file (Disaster Recovery)."""
    import_path = Path(args.file)
    if not import_path.exists():
        print(f"{RED}Error: File {import_path} does not exist.{RESET}")
        return

    with open(import_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = db.import_data(data, replace=args.replace)
    print(f"{GREEN}✓ Disaster Recovery Import Complete:{RESET} {stats['imported']} keybindings imported.")


def cmd_show(args, db: Database) -> None:
    """Display formatted preview card for a keybinding by ID (used by FZF preview and CLI)."""
    kb = db.get_keybinding(args.id)
    if not kb:
        print(f"{RED}Keybinding ID {args.id} not found.{RESET}")
        return
    print(format_keybinding_detail(kb))


def cmd_doctor(args, db: Database) -> None:
    """Perform health and diagnostics checks on OmniKey."""
    print(f"{BOLD}OmniKey System Doctor v{__version__}{RESET}\n")

    # DB status
    db_path = get_db_path()
    print(f"• Database Path:      {CYAN}{db_path}{RESET} ({'Exists' if db_path.exists() else 'Not initialized'})")
    kbs = db.list_keybindings()
    print(f"• Indexed Keybindings: {GREEN}{len(kbs)}{RESET}")

    # FZF status
    fzf_bin = find_fzf_binary()
    print(f"• FZF Binary:         {GREEN + fzf_bin + RESET if fzf_bin else YELLOW + 'Not Found (falling back to text search)' + RESET}")

    # Configs check
    targets = get_default_watch_targets()
    print(f"\n{BOLD}Watched Config Files Check:{RESET}")
    for tool, paths in targets.items():
        found = [p for p in paths if p.exists()]
        status = f"{GREEN}Found {len(found)} file(s){RESET}" if found else f"{DIM}No files located{RESET}"
        print(f"  [{tool.upper():<6}] {status}")
        for p in found:
            print(f"    - {p}")

    print(f"\n{GREEN}✓ Doctor check completed.{RESET}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnikey",
        description="OmniKey — Dynamic Keybinding & Context Tracker Agent",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # sync
    sync_p = subparsers.add_parser("sync", help="Scan and sync all configuration files into SQLite")
    sync_p.add_argument("-p", "--path", help="Custom file or directory path to parse and sync")


    # search
    search_p = subparsers.add_parser("search", help="Interactive search across keybindings")
    search_p.add_argument("query", nargs="?", default="", help="Initial search query")
    search_p.add_argument("-t", "--tool", help="Filter by tool (herdr, tmux, neovim, zsh)")
    search_p.add_argument("--all-tools", action="store_true", help="Include inactive tools in results")
    search_p.add_argument("--no-fzf", action="store_true", help="Disable fzf and use text output")

    # list
    list_p = subparsers.add_parser("list", help="List indexed keybindings")
    list_p.add_argument("-t", "--tool", help="Filter by tool")
    list_p.add_argument("--all-tools", action="store_true", help="Include inactive tools in results")
    list_p.add_argument("-s", "--search", help="Search filter")
    list_p.add_argument("-l", "--limit", type=int, help="Limit number of results")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # conflicts
    conf_p = subparsers.add_parser("conflicts", help="Detect keybinding collisions across tools")
    conf_p.add_argument("-t", "--tool", help="Filter by tool")
    conf_p.add_argument("--all-tools", action="store_true", help="Include inactive tools in results")

    # tools
    tools_p = subparsers.add_parser("tools", help="Manage active tools shown in results by default")
    tools_sub = tools_p.add_subparsers(dest="tools_action", help="Tools action")
    tools_sub.add_parser("list", help="Show tool status")
    enable_p = tools_sub.add_parser("enable", help="Activate one or more tools")
    enable_p.add_argument("tools", nargs="+", help="Tool names to activate (e.g. herdr tmux)")
    disable_p = tools_sub.add_parser("disable", help="Deactivate one or more tools")
    disable_p.add_argument("tools", nargs="+", help="Tool names to deactivate (e.g. neovim)")
    tools_sub.add_parser("reset", help="Reset: make all tools active again")

    # history
    hist_p = subparsers.add_parser("history", help="Show audit log and changes history")
    hist_p.add_argument("-l", "--limit", type=int, default=30, help="Number of entries to show")
    hist_p.add_argument("--type", help="Filter by change type (ADDED, UPDATED, DELETED, CONFLICT_DETECTED)")

    # add
    add_p = subparsers.add_parser("add", help="Add a manual keybinding entry")
    add_p.add_argument("combo", help="Key combination (e.g. 'prefix+w' or '<leader>sk')")
    add_p.add_argument("description", help="Description of what the keybinding does")
    add_p.add_argument("-t", "--tool", default="custom", help="Tool name (herdr, tmux, nvim, zsh, custom)")
    add_p.add_argument("-a", "--action", help="Raw command/action executed")
    add_p.add_argument("-m", "--mode", default="normal", help="Mode (normal, prefix, insert, visual, alias)")

    # remove
    rem_p = subparsers.add_parser("remove", help="Remove a keybinding by ID")
    rem_p.add_argument("id", type=int, help="ID of keybinding to remove")

    # watch
    subparsers.add_parser("watch", help="Run background file watcher daemon")

    # export
    exp_p = subparsers.add_parser("export", help="Export database to JSON file for Git backups")
    exp_p.add_argument("-o", "--output", help="Output JSON file path")

    # import
    imp_p = subparsers.add_parser("import", help="Import database from JSON file (Disaster Recovery)")
    imp_p.add_argument("file", help="Path to JSON export file")
    imp_p.add_argument("--replace", action="store_true", help="Replace existing database contents")

    # show
    show_p = subparsers.add_parser("show", help="Display details for a keybinding ID (used by FZF preview)")
    show_p.add_argument("id", type=int, help="Keybinding ID")

    # doctor
    subparsers.add_parser("doctor", help="Run health check and diagnostics")

    return parser


def main(args: Optional[List[str]] = None) -> None:
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        # Default action when no command given: search (only active tools)
        db = Database()
        run_fzf_search(db, tools=db.get_active_tools())
        return

    db = Database()

    command_handlers = {
        "sync": cmd_sync,
        "search": cmd_search,
        "list": cmd_list,
        "conflicts": cmd_conflicts,
        "history": cmd_history,
        "add": cmd_add,
        "remove": cmd_remove,
        "watch": cmd_watch,
        "export": cmd_export,
        "import": cmd_import,
        "show": cmd_show,
        "doctor": cmd_doctor,
        "tools": cmd_tools,
    }

    handler = command_handlers.get(parsed_args.command)
    if handler:
        handler(parsed_args, db)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
