"""Intervention engine — manages cooldowns, context simplification, and capability reduction."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, List, Optional


class InterventionType(Enum):
    COOLDOWN = auto()
    CONTEXT_SIMPLIFICATION = auto()
    CAPABILITY_REDUCTION = auto()
    FULL_RESET = auto()


@dataclass
class Intervention:
    """A single intervention action applied to an agent."""

    intervention_id: str
    agent_id: str
    type: InterventionType
    reason: str
    applied_at: datetime
    duration_seconds: int  # 0 = indefinite
    active: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.duration_seconds == 0:
            return False
        elapsed = (datetime.now(timezone.utc) - self.applied_at).total_seconds()
        return elapsed > self.duration_seconds


class InterventionEngine:
    """Determines and tracks interventions for stressed agents.

    Supports cooldown periods, context simplification, capability reduction,
    and full resets with configurable thresholds and cooldown enforcement.

    Usage::

        engine = InterventionEngine()
        result = engine.evaluate("agent-42", stress_report)
        if result:
            print(f"Applied {result.type.name} to agent-42")
            engine.release(result.intervention_id)
    """

    def __init__(
        self,
        moderate_threshold: float = 25.0,
        high_threshold: float = 50.0,
        critical_threshold: float = 75.0,
        cooldown_seconds: int = 300,
        simplification_seconds: int = 600,
        reduction_seconds: int = 900,
        max_active_per_agent: int = 3,
    ) -> None:
        self.moderate_threshold = moderate_threshold
        self.high_threshold = high_threshold
        self.critical_threshold = critical_threshold
        self.cooldown_seconds = cooldown_seconds
        self.simplification_seconds = simplification_seconds
        self.reduction_seconds = reduction_seconds
        self.max_active_per_agent = max_active_per_agent
        self._interventions: Dict[str, Intervention] = {}
        self._counter = 0

    def evaluate(
        self,
        agent_id: str,
        stress_score: float,
        stress_contributors: Optional[List[str]] = None,
    ) -> Optional[Intervention]:
        """Evaluate whether an agent needs intervention.

        Args:
            agent_id: The agent to evaluate.
            stress_score: Raw stress score (0–100).
            stress_contributors: Optional list of contributing factors.

        Returns:
            An Intervention if one was applied, or None.
        """
        # Clean expired
        self._expire_old()

        active = self._active_for(agent_id)
        if len(active) >= self.max_active_per_agent:
            return None

        # Determine intervention type
        if stress_score >= self.critical_threshold:
            return self._apply(agent_id, InterventionType.FULL_RESET, stress_score, stress_contributors)
        if stress_score >= self.high_threshold:
            return self._apply(agent_id, InterventionType.CAPABILITY_REDUCTION, stress_score, stress_contributors)
        if stress_score >= self.moderate_threshold:
            # Choose between cooldown and simplification
            has_latency_issue = stress_contributors and any("latency" in c.lower() for c in stress_contributors)
            if has_latency_issue:
                return self._apply(agent_id, InterventionType.CONTEXT_SIMPLIFICATION, stress_score, stress_contributors)
            return self._apply(agent_id, InterventionType.COOLDOWN, stress_score, stress_contributors)

        return None

    def release(self, intervention_id: str) -> bool:
        """Deactivate an intervention.

        Returns True if the intervention existed (regardless of active state).
        """
        iv = self._interventions.get(intervention_id)
        if iv is None:
            return False
        iv.active = False
        return True

    def active_interventions(self, agent_id: str) -> List[Intervention]:
        """Return all currently active interventions for an agent."""
        self._expire_old()
        return self._active_for(agent_id)

    def all_interventions(self, agent_id: str) -> List[Intervention]:
        """Return all interventions (including released) for an agent."""
        return [iv for iv in self._interventions.values() if iv.agent_id == agent_id]

    def clear_agent(self, agent_id: str) -> int:
        """Release all interventions for an agent. Returns count released."""
        count = 0
        for iv in self._interventions.values():
            if iv.agent_id == agent_id and iv.active:
                iv.active = False
                count += 1
        return count

    def _apply(
        self,
        agent_id: str,
        itype: InterventionType,
        stress_score: float,
        contributors: Optional[List[str]],
    ) -> Intervention:
        self._counter += 1
        duration = {
            InterventionType.COOLDOWN: self.cooldown_seconds,
            InterventionType.CONTEXT_SIMPLIFICATION: self.simplification_seconds,
            InterventionType.CAPABILITY_REDUCTION: self.reduction_seconds,
            InterventionType.FULL_RESET: 0,
        }[itype]

        iv = Intervention(
            intervention_id=f"int-{self._counter:06d}",
            agent_id=agent_id,
            type=itype,
            reason=f"Stress score {stress_score:.1f}" + (f": {'; '.join(contributors or [])}"),
            applied_at=datetime.now(timezone.utc),
            duration_seconds=duration,
            metadata={"stress_score": f"{stress_score:.1f}"},
        )
        self._interventions[iv.intervention_id] = iv
        return iv

    def _active_for(self, agent_id: str) -> List[Intervention]:
        return [
            iv for iv in self._interventions.values()
            if iv.agent_id == agent_id and iv.active and not iv.is_expired
        ]

    def _expire_old(self) -> None:
        for iv in self._interventions.values():
            if iv.active and iv.is_expired:
                iv.active = False
