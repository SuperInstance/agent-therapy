"""Wellness tracker — health history, trend analysis, and burnout prediction."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from agent_therapy.health import AgentHealth, HealthSnapshot
from agent_therapy.stress import StressLevel


class BurnoutRisk(Enum):
    NONE = auto()
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    IMMINENT = auto()


@dataclass(frozen=True)
class WellnessReport:
    """Summary of an agent's wellness over a tracking period."""

    agent_id: str
    generated_at: datetime
    total_snapshots: int
    avg_error_rate: float
    avg_latency_ms: float
    avg_quality: float
    avg_stress_score: float
    peak_stress_score: float
    stress_trend: float  # positive = worsening, negative = improving
    burnout_risk: BurnoutRisk
    current_health: Optional[HealthSnapshot]
    recommendation: str


class WellnessTracker:
    """Records health snapshots and analyzes trends for burnout prediction.

    Usage::

        tracker = WellnessTracker()
        tracker.record(health)
        # ... after more recordings ...
        report = tracker.report("agent-42")
        if report.burnout_risk >= BurnoutRisk.HIGH:
            print("Burnout warning!")
    """

    def __init__(self, max_history: int = 1000) -> None:
        self.max_history = max_history
        self._history: Dict[str, List[Tuple[datetime, HealthSnapshot]]] = {}

    def record(self, health: AgentHealth) -> HealthSnapshot:
        """Record a health snapshot for the agent. Returns the snapshot."""
        snap = health.snapshot()
        agent_id = health.agent_id

        if agent_id not in self._history:
            self._history[agent_id] = []

        self._history[agent_id].append((datetime.now(timezone.utc), snap))

        # Trim
        if len(self._history[agent_id]) > self.max_history:
            self._history[agent_id] = self._history[agent_id][-self.max_history :]

        return snap

    def record_snapshot(self, agent_id: str, snapshot: HealthSnapshot) -> None:
        """Record a pre-built snapshot."""
        if agent_id not in self._history:
            self._history[agent_id] = []
        self._history[agent_id].append((datetime.now(timezone.utc), snapshot))
        if len(self._history[agent_id]) > self.max_history:
            self._history[agent_id] = self._history[agent_id][-self.max_history :]

    def history(self, agent_id: str, limit: int = 50) -> List[HealthSnapshot]:
        """Return recent snapshots for an agent (most recent last)."""
        entries = self._history.get(agent_id, [])
        return [snap for _, snap in entries[-limit:]]

    def report(self, agent_id: str) -> Optional[WellnessReport]:
        """Generate a wellness report. Returns None if no data exists."""
        entries = self._history.get(agent_id, [])
        if not entries:
            return None

        snapshots = [snap for _, snap in entries]
        n = len(snapshots)

        avg_error = sum(s.error_rate for s in snapshots) / n
        avg_latency = sum(s.avg_latency_ms for s in snapshots) / n
        avg_quality = sum(s.response_quality for s in snapshots) / n
        avg_stress = sum(s.stress_level_raw for s in snapshots) / n
        peak_stress = max(s.stress_level_raw for s in snapshots)

        # Trend: compare last third to first third
        trend = self._compute_trend(snapshots)
        burnout = self._predict_burnout(snapshots, trend)
        recommendation = self._wellness_recommendation(burnout, avg_stress, trend)

        return WellnessReport(
            agent_id=agent_id,
            generated_at=datetime.now(timezone.utc),
            total_snapshots=n,
            avg_error_rate=avg_error,
            avg_latency_ms=avg_latency,
            avg_quality=avg_quality,
            avg_stress_score=avg_stress,
            peak_stress_score=peak_stress,
            stress_trend=trend,
            burnout_risk=burnout,
            current_health=snapshots[-1],
            recommendation=recommendation,
        )

    def agents_tracked(self) -> List[str]:
        """Return all agent IDs with recorded data."""
        return list(self._history.keys())

    def clear(self, agent_id: Optional[str] = None) -> None:
        """Clear history. If agent_id given, clears only that agent."""
        if agent_id:
            self._history.pop(agent_id, None)
        else:
            self._history.clear()

    def _compute_trend(self, snapshots: List[HealthSnapshot]) -> float:
        """Compute stress trend. Positive = worsening, negative = improving."""
        if len(snapshots) < 3:
            return 0.0
        third = max(1, len(snapshots) // 3)
        first = [s.stress_level_raw for s in snapshots[:third]]
        last = [s.stress_level_raw for s in snapshots[-third:]]
        avg_first = sum(first) / len(first)
        avg_last = sum(last) / len(last)
        return avg_last - avg_first

    def _predict_burnout(self, snapshots: List[HealthSnapshot], trend: float) -> BurnoutRisk:
        """Predict burnout risk from history and trend."""
        recent = snapshots[-5:] if len(snapshots) >= 5 else snapshots
        recent_stress = sum(s.stress_level_raw for s in recent) / len(recent)

        # Escalation factor: is stress accelerating?
        if len(snapshots) >= 6:
            half = len(snapshots) // 2
            first_half_trend = self._compute_trend(snapshots[:half])
            second_half_trend = self._compute_trend(snapshots[half:])
            accelerating = second_half_trend > first_half_trend and second_half_trend > 5
        else:
            accelerating = trend > 5

        if recent_stress > 70 and accelerating:
            return BurnoutRisk.IMMINENT
        if recent_stress > 60 or (recent_stress > 40 and trend > 15):
            return BurnoutRisk.HIGH
        if recent_stress > 35 or trend > 5:
            return BurnoutRisk.MODERATE
        if recent_stress > 15 or trend > 0:
            return BurnoutRisk.LOW
        return BurnoutRisk.NONE

    def _wellness_recommendation(
        self, burnout: BurnoutRisk, avg_stress: float, trend: float
    ) -> str:
        if burnout == BurnoutRisk.IMMINENT:
            return "Burnout imminent. Halt all non-critical tasks. Schedule immediate intervention."
        if burnout == BurnoutRisk.HIGH:
            return "High burnout risk. Reduce task complexity and increase monitoring frequency."
        if burnout == BurnoutRisk.MODERATE:
            return "Moderate burnout risk. Pre-emptive cooldown recommended."
        if burnout == BurnoutRisk.LOW:
            return "Low burnout risk. Continue monitoring at normal intervals."
        return "Agent wellness is excellent. Maintain current operational tempo."
