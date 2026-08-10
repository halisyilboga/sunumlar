"""Data models for OmniKey."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Keybinding:
    tool: str
    key_combo: str
    action_raw: str
    description: str
    source_file: str
    id: Optional[int] = None
    mode: str = "normal"  # normal, insert, visual, prefix, global, etc.
    is_manual: bool = False
    last_updated: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tool": self.tool,
            "key_combo": self.key_combo,
            "action_raw": self.action_raw,
            "description": self.description,
            "source_file": self.source_file,
            "mode": self.mode,
            "is_manual": self.is_manual,
            "last_updated": self.last_updated,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Keybinding":
        return cls(
            id=data.get("id"),
            tool=data.get("tool", "custom"),
            key_combo=data.get("key_combo", ""),
            action_raw=data.get("action_raw", ""),
            description=data.get("description", ""),
            source_file=data.get("source_file", "manual"),
            mode=data.get("mode", "normal"),
            is_manual=data.get("is_manual", False),
            last_updated=data.get("last_updated"),
            tags=data.get("tags", []),
        )


@dataclass
class AuditEntry:
    change_type: str  # ADDED, UPDATED, DELETED, CONFLICT_DETECTED
    keybinding_id: Optional[int] = None
    previous_value: Optional[str] = None
    details: Optional[str] = None
    id: Optional[int] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "keybinding_id": self.keybinding_id,
            "change_type": self.change_type,
            "previous_value": self.previous_value,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class Conflict:
    key_combo: str
    bindings: List[Keybinding]
    tools: List[str]
    severity: str  # HIGH, MEDIUM, LOW
    message: str
