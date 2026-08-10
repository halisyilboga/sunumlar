"""SQLite database and audit tracking layer for OmniKey."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from omnikey.config import get_db_path
from omnikey.models import AuditEntry, Keybinding


class Database:
    """Manages SQLite operations, tag indexing, and audit logging."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self.init_db()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Provide a transactional connection scope."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initialize tables and indexes if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS keybindings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool TEXT NOT NULL,
                    key_combo TEXT NOT NULL,
                    action_raw TEXT NOT NULL,
                    description TEXT,
                    source_file TEXT NOT NULL,
                    mode TEXT DEFAULT 'normal',
                    is_manual INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tool, source_file, key_combo, mode)
                );

                CREATE TABLE IF NOT EXISTS tags (
                    keybinding_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (keybinding_id, tag),
                    FOREIGN KEY (keybinding_id) REFERENCES keybindings(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keybinding_id INTEGER,
                    change_type TEXT NOT NULL,
                    previous_value TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_keybindings_tool ON keybindings(tool);
                CREATE INDEX IF NOT EXISTS idx_keybindings_combo ON keybindings(key_combo);
                CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
            """)

    def _row_to_keybinding(self, row: sqlite3.Row, tags: List[str]) -> Keybinding:
        return Keybinding(
            id=row["id"],
            tool=row["tool"],
            key_combo=row["key_combo"],
            action_raw=row["action_raw"],
            description=row["description"] or "",
            source_file=row["source_file"],
            mode=row["mode"] or "normal",
            is_manual=bool(row["is_manual"]),
            last_updated=str(row["last_updated"]),
            tags=tags,
        )

    def log_audit(self, entry: AuditEntry, conn: Optional[sqlite3.Connection] = None) -> int:
        """Record an entry in the audit log."""
        query = """
            INSERT INTO audit_log (keybinding_id, change_type, previous_value, details, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (entry.keybinding_id, entry.change_type, entry.previous_value, entry.details)
        if conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid
        with self.get_connection() as c:
            cursor = c.execute(query, params)
            return cursor.lastrowid

    def set_tags(self, kb_id: int, tags: List[str], conn: sqlite3.Connection) -> None:
        """Replace all tags for a keybinding."""
        conn.execute("DELETE FROM tags WHERE keybinding_id = ?", (kb_id,))
        for tag in set(tags):
            clean_tag = tag.strip().lower()
            if clean_tag:
                conn.execute(
                    "INSERT OR IGNORE INTO tags (keybinding_id, tag) VALUES (?, ?)",
                    (kb_id, clean_tag),
                )

    def get_tags(self, kb_id: int, conn: sqlite3.Connection) -> List[str]:
        """Fetch all tags for a keybinding."""
        rows = conn.execute("SELECT tag FROM tags WHERE keybinding_id = ?", (kb_id,)).fetchall()
        return [r["tag"] for r in rows]

    def add_manual_keybinding(self, kb: Keybinding) -> Keybinding:
        """Add a manually entered keybinding."""
        kb.is_manual = True
        kb.source_file = kb.source_file or "manual"
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO keybindings (tool, key_combo, action_raw, description, source_file, mode, is_manual, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(tool, source_file, key_combo, mode) DO UPDATE SET
                    action_raw = excluded.action_raw,
                    description = excluded.description,
                    last_updated = CURRENT_TIMESTAMP
                """,
                (kb.tool, kb.key_combo, kb.action_raw, kb.description, kb.source_file, kb.mode),
            )
            kb_id = cursor.lastrowid or kb.id
            if not kb_id:
                row = conn.execute(
                    "SELECT id FROM keybindings WHERE tool=? AND source_file=? AND key_combo=? AND mode=?",
                    (kb.tool, kb.source_file, kb.key_combo, kb.mode),
                ).fetchone()
                kb_id = row["id"]
            kb.id = kb_id
            self.set_tags(kb_id, kb.tags, conn)

            self.log_audit(
                AuditEntry(
                    keybinding_id=kb_id,
                    change_type="ADDED" if not kb.id else "UPDATED",
                    details=f"Manual keybinding: [{kb.tool}] {kb.key_combo} -> {kb.description or kb.action_raw}",
                ),
                conn=conn,
            )
            return kb

    def delete_keybinding(self, kb_id: int) -> bool:
        """Delete a keybinding and record audit entry."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM keybindings WHERE id = ?", (kb_id,)).fetchone()
            if not row:
                return False
            tags = self.get_tags(kb_id, conn)
            old_kb = self._row_to_keybinding(row, tags)

            conn.execute("DELETE FROM keybindings WHERE id = ?", (kb_id,))
            self.log_audit(
                AuditEntry(
                    keybinding_id=kb_id,
                    change_type="DELETED",
                    previous_value=json.dumps(old_kb.to_dict()),
                    details=f"Deleted [{old_kb.tool}] {old_kb.key_combo} ({old_kb.action_raw})",
                ),
                conn=conn,
            )
            return True

    def sync_file_keybindings(
        self, tool: str, source_file: str, new_kbs: List[Keybinding]
    ) -> Dict[str, int]:
        """Synchronize keybindings parsed from a file with the DB and track diffs in audit_log."""
        stats = {"added": 0, "updated": 0, "deleted": 0, "unchanged": 0}

        with self.get_connection() as conn:
            # Group new keybindings by their actual source_file (handles directory recursive parsing)
            by_source: Dict[str, List[Keybinding]] = {}
            for kb in new_kbs:
                sf = kb.source_file or source_file
                by_source.setdefault(sf, []).append(kb)

            # If new_kbs is empty for a single file source_file
            if not by_source and source_file:
                by_source[source_file] = []

            for actual_source, file_kbs in by_source.items():
                existing_rows = conn.execute(
                    "SELECT * FROM keybindings WHERE tool = ? AND source_file = ? AND is_manual = 0",
                    (tool, actual_source),
                ).fetchall()

                existing_map: Dict[Tuple[str, str], sqlite3.Row] = {
                    (r["key_combo"], r["mode"]): r for r in existing_rows
                }
                new_map: Dict[Tuple[str, str], Keybinding] = {
                    (kb.key_combo, kb.mode): kb for kb in file_kbs
                }

                # Handle updates and additions
                for key_tuple, new_kb in new_map.items():
                    if key_tuple in existing_map:
                        row = existing_map[key_tuple]
                        kb_id = row["id"]
                        changed = (
                            row["action_raw"] != new_kb.action_raw
                            or (row["description"] or "") != (new_kb.description or "")
                        )
                        existing_tags = set(self.get_tags(kb_id, conn))
                        new_tags = set(t.strip().lower() for t in new_kb.tags if t.strip())
                        tags_changed = existing_tags != new_tags

                        if changed or tags_changed:
                            old_kb = self._row_to_keybinding(row, list(existing_tags))
                            conn.execute(
                                """
                                UPDATE keybindings
                                SET action_raw = ?, description = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE id = ?
                                """,
                                (new_kb.action_raw, new_kb.description, kb_id),
                            )
                            self.set_tags(kb_id, list(new_tags), conn)
                            self.log_audit(
                                AuditEntry(
                                    keybinding_id=kb_id,
                                    change_type="UPDATED",
                                    previous_value=json.dumps(old_kb.to_dict()),
                                    details=f"Updated [{tool}] {new_kb.key_combo} in {actual_source}",
                                ),
                                conn=conn,
                            )
                            stats["updated"] += 1
                        else:
                            stats["unchanged"] += 1
                    else:
                        cursor = conn.execute(
                            """
                            INSERT INTO keybindings (tool, key_combo, action_raw, description, source_file, mode, is_manual, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                            ON CONFLICT(tool, source_file, key_combo, mode) DO UPDATE SET
                                action_raw = excluded.action_raw,
                                description = excluded.description,
                                last_updated = CURRENT_TIMESTAMP
                            """,
                            (
                                new_kb.tool,
                                new_kb.key_combo,
                                new_kb.action_raw,
                                new_kb.description,
                                actual_source,
                                new_kb.mode,
                            ),
                        )
                        kb_id = cursor.lastrowid
                        if not kb_id:
                            r = conn.execute(
                                "SELECT id FROM keybindings WHERE tool=? AND source_file=? AND key_combo=? AND mode=?",
                                (new_kb.tool, actual_source, new_kb.key_combo, new_kb.mode),
                            ).fetchone()
                            kb_id = r["id"]
                        self.set_tags(kb_id, new_kb.tags, conn)
                        self.log_audit(
                            AuditEntry(
                                keybinding_id=kb_id,
                                change_type="ADDED",
                                details=f"Added [{tool}] {new_kb.key_combo} -> {new_kb.description or new_kb.action_raw} ({actual_source})",
                            ),
                            conn=conn,
                        )
                        stats["added"] += 1

                # Handle deletions for bindings no longer present in file
                for key_tuple, row in existing_map.items():
                    if key_tuple not in new_map:
                        kb_id = row["id"]
                        old_tags = self.get_tags(kb_id, conn)
                        old_kb = self._row_to_keybinding(row, old_tags)
                        conn.execute("DELETE FROM keybindings WHERE id = ?", (kb_id,))
                        self.log_audit(
                            AuditEntry(
                                keybinding_id=kb_id,
                                change_type="DELETED",
                                previous_value=json.dumps(old_kb.to_dict()),
                                details=f"Removed [{tool}] {old_kb.key_combo} (no longer in {actual_source})",
                            ),
                            conn=conn,
                        )
                        stats["deleted"] += 1

        return stats


    def get_keybinding(self, kb_id: int) -> Optional[Keybinding]:
        """Fetch a single keybinding by ID."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM keybindings WHERE id = ?", (kb_id,)).fetchone()
            if not row:
                return None
            tags = self.get_tags(kb_id, conn)
            return self._row_to_keybinding(row, tags)

    def list_keybindings(
        self,
        tool: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Keybinding]:
        """List keybindings filtered by tool or search string (matches combo, action, desc, or tags)."""
        with self.get_connection() as conn:
            query = """
                SELECT DISTINCT k.*
                FROM keybindings k
                LEFT JOIN tags t ON k.id = t.keybinding_id
                WHERE 1=1
            """
            params: List[object] = []

            if tool:
                query += " AND LOWER(k.tool) = LOWER(?)"
                params.append(tool)

            if search:
                tokens = [t.strip().lower() for t in search.split() if t.strip()]
                for token in tokens:
                    query += """
                        AND (
                            LOWER(k.key_combo) LIKE ?
                            OR LOWER(k.action_raw) LIKE ?
                            OR LOWER(k.description) LIKE ?
                            OR LOWER(k.tool) LIKE ?
                            OR LOWER(t.tag) LIKE ?
                        )
                    """
                    pat = f"%{token}%"
                    params.extend([pat, pat, pat, pat, pat])

            query += " ORDER BY k.tool ASC, k.key_combo ASC"
            if limit:
                query += f" LIMIT {int(limit)}"

            rows = conn.execute(query, params).fetchall()
            results: List[Keybinding] = []
            for row in rows:
                tags = self.get_tags(row["id"], conn)
                results.append(self._row_to_keybinding(row, tags))
            return results

    def get_audit_history(
        self, limit: int = 50, change_type: Optional[str] = None
    ) -> List[AuditEntry]:
        """Fetch recent audit log entries."""
        with self.get_connection() as conn:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params: List[object] = []
            if change_type:
                query += " AND change_type = ?"
                params.append(change_type)
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [
                AuditEntry(
                    id=r["id"],
                    keybinding_id=r["keybinding_id"],
                    change_type=r["change_type"],
                    previous_value=r["previous_value"],
                    details=r["details"],
                    timestamp=str(r["timestamp"]),
                )
                for r in rows
            ]

    def export_data(self) -> dict:
        """Export full database state into a portable dictionary for git backups."""
        all_kbs = self.list_keybindings()
        audits = self.get_audit_history(limit=500)
        return {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "keybindings": [kb.to_dict() for kb in all_kbs],
            "audit_log": [a.to_dict() for a in audits],
        }

    def import_data(self, data: dict, replace: bool = False) -> Dict[str, int]:
        """Import database state from an export dictionary."""
        stats = {"imported": 0, "skipped": 0}
        kbs_data = data.get("keybindings", [])

        with self.get_connection() as conn:
            if replace:
                conn.execute("DELETE FROM keybindings")
                conn.execute("DELETE FROM tags")
                conn.execute("DELETE FROM audit_log")

            for item in kbs_data:
                kb = Keybinding.from_dict(item)
                try:
                    cursor = conn.execute(
                        """
                        INSERT INTO keybindings (tool, key_combo, action_raw, description, source_file, mode, is_manual, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(tool, source_file, key_combo, mode) DO UPDATE SET
                            action_raw = excluded.action_raw,
                            description = excluded.description,
                            is_manual = excluded.is_manual,
                            last_updated = CURRENT_TIMESTAMP
                        """,
                        (
                            kb.tool,
                            kb.key_combo,
                            kb.action_raw,
                            kb.description,
                            kb.source_file,
                            kb.mode,
                            1 if kb.is_manual else 0,
                        ),
                    )
                    kb_id = cursor.lastrowid
                    if not kb_id:
                        r = conn.execute(
                            "SELECT id FROM keybindings WHERE tool=? AND source_file=? AND key_combo=? AND mode=?",
                            (kb.tool, kb.source_file, kb.key_combo, kb.mode),
                        ).fetchone()
                        kb_id = r["id"]
                    self.set_tags(kb_id, kb.tags, conn)
                    stats["imported"] += 1
                except Exception:
                    stats["skipped"] += 1

            self.log_audit(
                AuditEntry(
                    change_type="IMPORT",
                    details=f"Imported {stats['imported']} keybindings (replace={replace})",
                ),
                conn=conn,
            )

        return stats
