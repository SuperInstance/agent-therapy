"""Therapy journal — structured logging of incidents, reflections, and recovery plans."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional


class EntryType(Enum):
    INCIDENT = auto()
    REFLECTION = auto()
    RECOVERY_PLAN = auto()
    MILESTONE = auto()


@dataclass
class JournalEntry:
    """A single therapy journal entry."""

    entry_id: str
    agent_id: str
    entry_type: EntryType
    timestamp: datetime
    title: str
    body: str
    tags: List[str] = field(default_factory=list)
    severity: str = "info"  # info, warning, critical
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "agent_id": self.agent_id,
            "entry_type": self.entry_type.name,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "severity": self.severity,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> JournalEntry:
        return cls(
            entry_id=str(data["entry_id"]),
            agent_id=str(data["agent_id"]),
            entry_type=EntryType[str(data["entry_type"])],
            timestamp=datetime.fromisoformat(str(data["timestamp"])),
            title=str(data["title"]),
            body=str(data["body"]),
            tags=list(data.get("tags", [])),  # type: ignore[arg-type]
            severity=str(data.get("severity", "info")),
            metadata=dict(data.get("metadata", {})),  # type: ignore[arg-type]
        )


class TherapyJournal:
    """Structured therapy journal for agents.

    Supports in-memory storage, filtering, and optional file persistence.

    Usage::

        journal = TherapyJournal()
        entry = journal.log_incident(
            agent_id="agent-42",
            title="Elevated error rate",
            body="Error rate spiked to 35% during peak load",
            severity="warning",
            tags=["errors", "peak-load"],
        )
        # Reflect later
        journal.log_reflection(
            agent_id="agent-42",
            title="Post-incident review",
            body="Root cause was context window overflow. Simplification helped.",
        )
    """

    def __init__(self, persist_path: Optional[str] = None) -> None:
        self._entries: List[JournalEntry] = []
        self._counter = 0
        self._persist_path = Path(persist_path) if persist_path else None

    def log_incident(
        self,
        agent_id: str,
        title: str,
        body: str,
        severity: str = "warning",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> JournalEntry:
        """Log an incident entry."""
        return self._add(
            agent_id=agent_id,
            entry_type=EntryType.INCIDENT,
            title=title,
            body=body,
            tags=tags or [],
            severity=severity,
            metadata=metadata or {},
        )

    def log_reflection(
        self,
        agent_id: str,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> JournalEntry:
        """Log a reflection entry."""
        return self._add(
            agent_id=agent_id,
            entry_type=EntryType.REFLECTION,
            title=title,
            body=body,
            tags=tags or [],
            severity="info",
            metadata=metadata or {},
        )

    def log_recovery_plan(
        self,
        agent_id: str,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> JournalEntry:
        """Log a recovery plan entry."""
        return self._add(
            agent_id=agent_id,
            entry_type=EntryType.RECOVERY_PLAN,
            title=title,
            body=body,
            tags=tags or [],
            severity="info",
            metadata=metadata or {},
        )

    def log_milestone(
        self,
        agent_id: str,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> JournalEntry:
        """Log a milestone entry (e.g., recovery complete, burnout averted)."""
        return self._add(
            agent_id=agent_id,
            entry_type=EntryType.MILESTONE,
            title=title,
            body=body,
            tags=tags or [],
            severity="info",
            metadata=metadata or {},
        )

    def query(
        self,
        agent_id: Optional[str] = None,
        entry_type: Optional[EntryType] = None,
        severity: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[JournalEntry]:
        """Query journal entries with optional filters."""
        results = self._entries
        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if entry_type:
            results = [e for e in results if e.entry_type == entry_type]
        if severity:
            results = [e for e in results if e.severity == severity]
        if tag:
            results = [e for e in results if tag in e.tags]
        return results[-limit:]

    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Retrieve a specific entry by ID."""
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def agent_summary(self, agent_id: str) -> Dict[str, int]:
        """Count entries by type for a given agent."""
        counts: Dict[str, int] = {}
        for e in self._entries:
            if e.agent_id == agent_id:
                key = e.entry_type.name
                counts[key] = counts.get(key, 0) + 1
        return counts

    def all_entries(self) -> List[JournalEntry]:
        """Return all entries."""
        return list(self._entries)

    def save(self) -> None:
        """Persist all entries to the configured file (JSONL format)."""
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._persist_path, "w") as f:
            for entry in self._entries:
                f.write(json.dumps(entry.to_dict()) + "\n")

    def load(self) -> None:
        """Load entries from the configured file."""
        if not self._persist_path or not self._persist_path.exists():
            return
        with open(self._persist_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entry = JournalEntry.from_dict(data)
                    self._entries.append(entry)
                    # Advance counter past loaded IDs
                    try:
                        num = int(entry.entry_id.split("-")[1])
                        self._counter = max(self._counter, num)
                    except (IndexError, ValueError):
                        pass

    def clear(self) -> None:
        """Clear all entries from memory."""
        self._entries.clear()

    def _add(
        self,
        agent_id: str,
        entry_type: EntryType,
        title: str,
        body: str,
        tags: List[str],
        severity: str,
        metadata: Dict[str, str],
    ) -> JournalEntry:
        self._counter += 1
        entry = JournalEntry(
            entry_id=f"je-{self._counter:06d}",
            agent_id=agent_id,
            entry_type=entry_type,
            timestamp=datetime.now(timezone.utc),
            title=title,
            body=body,
            tags=tags,
            severity=severity,
            metadata=metadata,
        )
        self._entries.append(entry)
        if self._persist_path:
            self.save()
        return entry
