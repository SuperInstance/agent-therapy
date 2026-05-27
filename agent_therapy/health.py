"""Agent health metrics — tracks per-agent performance and wellbeing indicators."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import List


@dataclass(frozen=True)
class HealthSnapshot:
    """Immutable point-in-time snapshot of agent health."""

    timestamp: datetime
    success_count: int
    error_count: int
    total_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    error_rate: float  # 0.0 – 1.0
    response_quality: float  # 0.0 – 1.0 heuristic
    stress_level_raw: float  # 0.0 – 100.0

    @property
    def error_rate_pct(self) -> float:
        return self.error_rate * 100

    @property
    def is_healthy(self) -> bool:
        return self.error_rate < 0.1 and self.avg_latency_ms < 2000


@dataclass
class AgentHealth:
    """Tracks real-time health metrics for a single agent.

    Usage::

        health = AgentHealth(agent_id="agent-42")
        health.record_response(success=True, latency_ms=120)
        health.record_response(success=False, latency_ms=3500)
        snapshot = health.snapshot()
    """

    agent_id: str
    window_size: int = 100
    _successes: List[bool] = field(default_factory=list)
    _latencies: List[float] = field(default_factory=list)
    _quality_scores: List[float] = field(default_factory=list)
    _created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record_response(
        self,
        success: bool,
        latency_ms: float,
        quality: float | None = None,
    ) -> None:
        """Record a single response event.

        Args:
            success: Whether the response completed without error.
            latency_ms: Response latency in milliseconds.
            quality: Optional quality score 0.0–1.0. If omitted, inferred
                     from success and latency.
        """
        if quality is None:
            quality = self._infer_quality(success, latency_ms)
        self._successes.append(success)
        self._latencies.append(latency_ms)
        self._quality_scores.append(quality)

        # Trim to window
        if len(self._successes) > self.window_size:
            self._successes = self._successes[-self.window_size :]
            self._latencies = self._latencies[-self.window_size :]
            self._quality_scores = self._quality_scores[-self.window_size :]

    @property
    def total_requests(self) -> int:
        return len(self._successes)

    @property
    def error_count(self) -> int:
        return sum(1 for s in self._successes if not s)

    @property
    def success_count(self) -> int:
        return sum(1 for s in self._successes if s)

    @property
    def error_rate(self) -> float:
        if not self._successes:
            return 0.0
        return self.error_count / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        return mean(self._latencies) if self._latencies else 0.0

    @property
    def p95_latency_ms(self) -> float:
        if len(self._latencies) < 2:
            return self.avg_latency_ms
        sorted_lat = sorted(self._latencies)
        idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        return sorted_lat[idx]

    @property
    def avg_quality(self) -> float:
        return mean(self._quality_scores) if self._quality_scores else 1.0

    def snapshot(self) -> HealthSnapshot:
        """Capture an immutable health snapshot."""
        raw_stress = self._compute_raw_stress()
        return HealthSnapshot(
            timestamp=datetime.now(timezone.utc),
            success_count=self.success_count,
            error_count=self.error_count,
            total_requests=self.total_requests,
            avg_latency_ms=self.avg_latency_ms,
            p95_latency_ms=self.p95_latency_ms,
            error_rate=self.error_rate,
            response_quality=self.avg_quality,
            stress_level_raw=raw_stress,
        )

    def reset(self) -> None:
        """Clear all recorded data."""
        self._successes.clear()
        self._latencies.clear()
        self._quality_scores.clear()

    def _infer_quality(self, success: bool, latency_ms: float) -> float:
        """Heuristic quality from success + latency."""
        if not success:
            return 0.0
        # Latency-based degradation: <500ms → 1.0, >5000ms → 0.2
        if latency_ms <= 500:
            return 1.0
        if latency_ms >= 5000:
            return 0.2
        return 1.0 - 0.8 * ((latency_ms - 500) / 4500)

    def _compute_raw_stress(self) -> float:
        """Raw stress score 0–100 based on current metrics."""
        if not self._successes:
            return 0.0
        # Weighted combo: error_rate (40%), latency factor (30%), quality (30%)
        error_component = self.error_rate * 40
        latency_component = min(self.avg_latency_ms / 5000, 1.0) * 30
        quality_component = (1.0 - self.avg_quality) * 30
        return min(error_component + latency_component + quality_component, 100.0)

    def latency_stdev(self) -> float:
        """Standard deviation of latencies (jitter indicator)."""
        if len(self._latencies) < 2:
            return 0.0
        return stdev(self._latencies)
