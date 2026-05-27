"""Tests for agent_therapy.journal module."""

import tempfile
from pathlib import Path

from agent_therapy.journal import EntryType, JournalEntry, TherapyJournal


class TestJournalLogging:
    def test_log_incident(self):
        j = TherapyJournal()
        entry = j.log_incident("agent-1", "Error spike", "Error rate hit 40%")
        assert entry.entry_type == EntryType.INCIDENT
        assert entry.agent_id == "agent-1"
        assert entry.severity == "warning"

    def test_log_reflection(self):
        j = TherapyJournal()
        entry = j.log_reflection("agent-1", "Post-mortem", "Root cause was X")
        assert entry.entry_type == EntryType.REFLECTION
        assert entry.severity == "info"

    def test_log_recovery_plan(self):
        j = TherapyJournal()
        entry = j.log_recovery_plan("agent-1", "Recovery", "Steps to fix")
        assert entry.entry_type == EntryType.RECOVERY_PLAN

    def test_log_milestone(self):
        j = TherapyJournal()
        entry = j.log_milestone("agent-1", "Burnout averted", "Agent recovered")
        assert entry.entry_type == EntryType.MILESTONE

    def test_tags(self):
        j = TherapyJournal()
        entry = j.log_incident("a1", "t", "b", tags=["errors", "peak"])
        assert entry.tags == ["errors", "peak"]

    def test_metadata(self):
        j = TherapyJournal()
        entry = j.log_incident("a1", "t", "b", metadata={"error_code": "E503"})
        assert entry.metadata["error_code"] == "E503"

    def test_entry_ids_increment(self):
        j = TherapyJournal()
        e1 = j.log_incident("a1", "t", "b")
        e2 = j.log_incident("a1", "t", "b")
        assert e1.entry_id != e2.entry_id


class TestJournalQuery:
    def test_query_by_agent(self):
        j = TherapyJournal()
        j.log_incident("a1", "t", "b")
        j.log_incident("a2", "t", "b")
        j.log_incident("a1", "t2", "b")
        results = j.query(agent_id="a1")
        assert len(results) == 2

    def test_query_by_type(self):
        j = TherapyJournal()
        j.log_incident("a1", "t", "b")
        j.log_reflection("a1", "t", "b")
        results = j.query(entry_type=EntryType.REFLECTION)
        assert len(results) == 1

    def test_query_by_severity(self):
        j = TherapyJournal()
        j.log_incident("a1", "t", "b", severity="critical")
        j.log_incident("a1", "t", "b", severity="warning")
        results = j.query(severity="critical")
        assert len(results) == 1

    def test_query_by_tag(self):
        j = TherapyJournal()
        j.log_incident("a1", "t", "b", tags=["errors"])
        j.log_incident("a1", "t", "b", tags=["latency"])
        results = j.query(tag="errors")
        assert len(results) == 1

    def test_query_limit(self):
        j = TherapyJournal()
        for i in range(10):
            j.log_incident("a1", f"t{i}", "b")
        results = j.query(limit=3)
        assert len(results) == 3

    def test_get_entry(self):
        j = TherapyJournal()
        entry = j.log_incident("a1", "t", "b")
        found = j.get_entry(entry.entry_id)
        assert found is entry

    def test_get_entry_nonexistent(self):
        j = TherapyJournal()
        assert j.get_entry("nope") is None

    def test_agent_summary(self):
        j = TherapyJournal()
        j.log_incident("a1", "t", "b")
        j.log_incident("a1", "t", "b")
        j.log_reflection("a1", "t", "b")
        summary = j.agent_summary("a1")
        assert summary.get("INCIDENT") == 2
        assert summary.get("REFLECTION") == 1

    def test_agent_summary_empty(self):
        j = TherapyJournal()
        assert j.agent_summary("nonexistent") == {}


class TestJournalPersistence:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "journal.jsonl"
            j1 = TherapyJournal(persist_path=str(path))
            j1.log_incident("a1", "Error", "Big error", tags=["ops"])
            j1.log_reflection("a1", "Review", "Fixed it")
            j1.save()

            j2 = TherapyJournal(persist_path=str(path))
            j2.load()
            entries = j2.all_entries()
            assert len(entries) == 2
            assert entries[0].agent_id == "a1"
            assert entries[0].entry_type == EntryType.INCIDENT

    def test_load_continues_counter(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "journal.jsonl"
            j1 = TherapyJournal(persist_path=str(path))
            j1.log_incident("a1", "t", "b")
            j1.save()

            j2 = TherapyJournal(persist_path=str(path))
            j2.load()
            e = j2.log_incident("a1", "t2", "b2")
            assert e.entry_id > "je-000001"

    def test_clear(self):
        j = TherapyJournal()
        j.log_incident("a1", "t", "b")
        j.clear()
        assert len(j.all_entries()) == 0


class TestJournalEntrySerialization:
    def test_round_trip(self):
        from datetime import datetime, timezone

        entry = JournalEntry(
            entry_id="je-000001",
            agent_id="a1",
            entry_type=EntryType.INCIDENT,
            timestamp=datetime.now(timezone.utc),
            title="Test",
            body="Body text",
            tags=["tag1"],
            severity="critical",
            metadata={"key": "value"},
        )
        d = entry.to_dict()
        restored = JournalEntry.from_dict(d)
        assert restored.entry_id == entry.entry_id
        assert restored.entry_type == EntryType.INCIDENT
        assert restored.tags == ["tag1"]
