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

    print("\n" + "=" * 55)
    print(
        f"{BOLD}Sync Complete!{RESET} ({found_files} files scanned)\n"
        f"Total: {GREEN}{total_stats['added']} added{RESET}, "
        f"{YELLOW}{total_stats['updated']} updated{RESET}, "
        f"{RED}{total_stats['deleted']} removed{RESET}, "
        f"{DIM}{total_stats['unchanged']} unchanged{RESET}"
    )

    # Check conflicts after sync
    all_kbs = db.list_keybindings()
    conflicts = ConflictDetector.detect_conflicts(all_kbs)
    if conflicts:
        print(f"\n{YELLOW}⚠ Notice: {len(conflicts)} conflict(s) detected. Run 'omnikey conflicts' for details.{RESET}")


def cmd_search(args, db: Database) -> None:
    """Interactive FZF search or text search."""
    if args.no_fzf:
        kbs = db.list_keybindings(tool=args.tool, search=args.query)
        if not kbs:
            print(f"{YELLOW}No keybindings found.{RESET}")
            return
        print(f"\n{BOLD}Search results ({len(kbs)} found):{RESET}")
        for kb in kbs:
            print(format_keybinding_row(kb))
    else:
        run_fzf_search(db, query=args.query, tool=args.tool)


def cmd_list(args, db: Database) -> None:
    """List keybindings in table or JSON format."""
    kbs = db.list_keybindings(tool=args.tool, search=args.search, limit=args.limit)
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
    all_kbs = db.list_keybindings(tool=args.tool)
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
    search_p.add_argument("--no-fzf", action="store_true", help="Disable fzf and use text output")

    # list
    list_p = subparsers.add_parser("list", help="List indexed keybindings")
    list_p.add_argument("-t", "--tool", help="Filter by tool")
    list_p.add_argument("-s", "--search", help="Search filter")
    list_p.add_argument("-l", "--limit", type=int, help="Limit number of results")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # conflicts
    conf_p = subparsers.add_parser("conflicts", help="Detect keybinding collisions across tools")
    conf_p.add_argument("-t", "--tool", help="Filter by tool")

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

    # doctor
    subparsers.add_parser("doctor", help="Run health check and diagnostics")

    return parser


def main(args: Optional[List[str]] = None) -> None:
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        # Default action when no command given: search
        db = Database()
        run_fzf_search(db)
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
        "doctor": cmd_doctor,
    }

    handler = command_handlers.get(parsed_args.command)
    if handler:
        handler(parsed_args, db)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
