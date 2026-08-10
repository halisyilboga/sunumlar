"""Filesystem watcher daemon for real-time config changes."""

import time
from pathlib import Path
from threading import Timer
from typing import Any, Dict, List, Optional

from omnikey.config import get_default_watch_targets
from omnikey.db import Database
from omnikey.parsers import get_parser_for_file
from omnikey.semantic.conflict import ConflictDetector

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    FileSystemEvent = Any  # type: ignore
    FileSystemEventHandler = object  # type: ignore
    Observer = None  # type: ignore



class ConfigChangeHandler(FileSystemEventHandler):
    """Handles file system events and triggers debounced parser runs."""

    def __init__(self, db: Database, debounce_seconds: float = 0.5):
        super().__init__()
        self.db = db
        self.debounce_seconds = debounce_seconds
        self._timers: Dict[str, Timer] = {}

    def _debounce(self, path_str: str, callback):
        if path_str in self._timers:
            self._timers[path_str].cancel()
        timer = Timer(self.debounce_seconds, callback)
        self._timers[path_str] = timer
        timer.start()

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle_path(Path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle_path(Path(event.src_path))

    def _handle_path(self, target_path: Path) -> None:
        resolved = target_path.resolve()
        parser = get_parser_for_file(resolved) or get_parser_for_file(target_path)
        if not parser:
            return

        def process():
            try:
                print(f"[OmniKey Watcher] Change detected in: {target_path}")
                kbs = parser.parse(resolved if resolved.exists() else target_path)
                stats = self.db.sync_file_keybindings(
                    tool=parser.tool_name,
                    source_file=str(resolved),
                    new_kbs=kbs,
                )
                print(
                    f"[OmniKey Watcher] Synced {parser.tool_name}: "
                    f"+{stats['added']} ~{stats['updated']} -{stats['deleted']} ={stats['unchanged']}"
                )

                # Check for conflicts
                all_kbs = self.db.list_keybindings()
                conflicts = ConflictDetector.detect_conflicts(all_kbs)
                if conflicts:
                    print(f"[OmniKey Watcher] Warning: {len(conflicts)} keybinding conflict(s) detected!")
            except Exception as e:
                print(f"[OmniKey Watcher] Error processing {target_path}: {e}")

        self._debounce(str(resolved), process)


class ConfigWatcher:
    """Manages the watchdog observer and target directory monitoring."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.observer = None
        self.handler = ConfigChangeHandler(self.db)

    def start(self, targets: Optional[Dict[str, List[Path]]] = None) -> None:
        """Start watching all configured targets."""
        if not Observer:
            raise RuntimeError("watchdog package is required to run the watcher daemon. Install with: pip install watchdog")

        target_map = targets or get_default_watch_targets()
        self.observer = Observer()

        watched_dirs = set()
        for tool, paths in target_map.items():
            for p in paths:
                resolved = p.resolve() if p.exists() else p
                # Watch parent directory of file, or directory itself
                watch_dir = resolved if resolved.is_dir() else resolved.parent
                if watch_dir.exists() and str(watch_dir) not in watched_dirs:
                    self.observer.schedule(self.handler, str(watch_dir), recursive=True)
                    watched_dirs.add(str(watch_dir))
                    print(f"[OmniKey Watcher] Watching [{tool}] directory: {watch_dir}")

        self.observer.start()
        print(f"[OmniKey Watcher] Daemon active. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop the watchdog observer."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("[OmniKey Watcher] Stopped.")
