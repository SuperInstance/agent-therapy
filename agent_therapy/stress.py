"""Stress detection — analyzes error patterns, response degradation, and resource usage."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from agent_therapy.health import AgentHealth, HealthSnapshot


class StressLevel(Enum):
    """Categorical stress levels."""

    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    CRITICAL = auto()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, StressLevel):
            return NotImplemented
        order = [StressLevel.LOW, StressLevel.MODERATE, StressLevel.HIGH, StressLevel.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: object) -> bool:
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, StressLevel):
            return NotImplemented
        return not (self <= other)

    def __ge__(self, other: object) -> bool:
        return self == other or self > other


@dataclass(frozen=True)
class StressReport:
    """Result of a stress assessment."""

    level: StressLevel
    score: float  # 0–100
    error_rate: float
    latency_degradation: float  # ratio vs baseline or 0
    quality_degradation: float  # ratio vs baseline or 0
    jitter: float  # latency stdev
    contributors: List[str]  # human-readable factors
    recommendation: str


class StressDetector:
    """Analyzes agent health data to detect and classify stress.

    Usage::

        detector = StressDetector(error_threshold=0.15, latency_baseline_ms=500)
        report = detector.assess(health)
        if report.level >= StressLevel.HIGH:
            print("Agent needs intervention!")
    """

    def __init__(
        self,
        error_threshold: float = 0.10,
        latency_baseline_ms: float = 500.0,
        quality_baseline: float = 0.85,
        critical_error_rate: float = 0.30,
        critical_latency_multiplier: float = 5.0,
    ) -> None:
        self.error_threshold = error_threshold
        self.latency_baseline_ms = latency_baseline_ms
        self.quality_baseline = quality_baseline
        self.critical_error_rate = critical_error_rate
        self.critical_latency_multiplier = critical_latency_multiplier

    def assess(self, health: AgentHealth) -> StressReport:
        """Produce a stress report from an agent's current health."""
        snap = health.snapshot()
        contributors: List[str] = []

        # Error analysis
        error_rate = snap.error_rate
        if error_rate > self.critical_error_rate:
            contributors.append(f"Critical error rate: {error_rate:.1%}")
        elif error_rate > self.error_threshold:
            contributors.append(f"Elevated error rate: {error_rate:.1%}")

        # Latency degradation
        latency_deg = 0.0
        if self.latency_baseline_ms > 0:
            latency_deg = max(0.0, (snap.avg_latency_ms - self.latency_baseline_ms) / self.latency_baseline_ms)
        if latency_deg > self.critical_latency_multiplier:
            contributors.append(f"Severe latency spike: {snap.avg_latency_ms:.0f}ms ({latency_deg:.1f}x baseline)")
        elif latency_deg > 1.0:
            contributors.append(f"Latency degraded: {snap.avg_latency_ms:.0f}ms ({latency_deg:.1f}x baseline)")

        # Quality degradation
        quality_deg = max(0.0, self.quality_baseline - snap.response_quality)
        if quality_deg > 0.3:
            contributors.append(f"Quality dropped significantly: {snap.response_quality:.2f}")
        elif quality_deg > 0.1:
            contributors.append(f"Quality degraded: {snap.response_quality:.2f}")

        # Jitter
        jitter = health.latency_stdev()
        if jitter > 1000:
            contributors.append(f"High latency jitter: {jitter:.0f}ms stdev")

        # Score
        score = snap.stress_level_raw
        level = self._classify(score)
        recommendation = self._recommend(level, contributors)

        return StressReport(
            level=level,
            score=score,
            error_rate=error_rate,
            latency_degradation=latency_deg,
            quality_degradation=quality_deg,
            jitter=jitter,
            contributors=contributors,
            recommendation=recommendation,
        )

    def assess_snapshot(self, snapshot: HealthSnapshot) -> StressReport:
        """Assess stress from a snapshot (no jitter available)."""
        contributors: List[str] = []

        if snapshot.error_rate > self.critical_error_rate:
            contributors.append(f"Critical error rate: {snapshot.error_rate:.1%}")
        elif snapshot.error_rate > self.error_threshold:
            contributors.append(f"Elevated error rate: {snapshot.error_rate:.1%}")

        latency_deg = max(0.0, (snapshot.avg_latency_ms - self.latency_baseline_ms) / max(self.latency_baseline_ms, 1))
        quality_deg = max(0.0, self.quality_baseline - snapshot.response_quality)

        score = snapshot.stress_level_raw
        level = self._classify(score)

        return StressReport(
            level=level,
            score=score,
            error_rate=snapshot.error_rate,
            latency_degradation=latency_deg,
            quality_degradation=quality_deg,
            jitter=0.0,
            contributors=contributors or ["All metrics nominal"],
            recommendation=self._recommend(level, contributors),
        )

    def _classify(self, score: float) -> StressLevel:
        if score >= 75:
            return StressLevel.CRITICAL
        if score >= 50:
            return StressLevel.HIGH
        if score >= 25:
            return StressLevel.MODERATE
        return StressLevel.LOW

    def _recommend(self, level: StressLevel, contributors: List[str]) -> str:
        if level == StressLevel.CRITICAL:
            return "Immediate intervention required. Consider full agent reset or reduced task load."
        if level == StressLevel.HIGH:
            return "Intervention recommended. Simplify context and reduce concurrent tasks."
        if level == StressLevel.MODERATE:
            return "Monitor closely. Pre-emptive cooldown may prevent escalation."
        return "Agent is healthy. No action needed."
