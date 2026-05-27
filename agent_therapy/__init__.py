"""Agent Therapy — Behavioral health monitoring for AI agents.

Provides stress detection, wellness tracking, intervention management,
and therapy journaling for autonomous software agents.

Quick start::

    from agent_therapy import AgentHealth, StressDetector, WellnessTracker

    health = AgentHealth(agent_id="agent-42")
    health.record_response(success=True, latency_ms=120)
    health.record_response(success=False, latency_ms=3500)

    detector = StressDetector()
    stress = detector.assess(health)
    print(stress.level)  # StressLevel.LOW / MODERATE / HIGH / CRITICAL

    tracker = WellnessTracker()
    tracker.record(health)
    report = tracker.report(agent_id="agent-42")
"""

from agent_therapy.health import AgentHealth, HealthSnapshot
from agent_therapy.stress import StressDetector, StressLevel, StressReport
from agent_therapy.intervention import InterventionEngine, Intervention
from agent_therapy.wellness import WellnessTracker, WellnessReport
from agent_therapy.journal import TherapyJournal, JournalEntry

__all__ = [
    "AgentHealth",
    "HealthSnapshot",
    "StressDetector",
    "StressLevel",
    "StressReport",
    "InterventionEngine",
    "Intervention",
    "WellnessTracker",
    "WellnessReport",
    "TherapyJournal",
    "JournalEntry",
]
__version__ = "0.1.0"
