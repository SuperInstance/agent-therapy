"""Tests for agent_therapy.stress module."""

from agent_therapy.health import AgentHealth
from agent_therapy.stress import StressDetector, StressLevel


class TestStressClassification:
    def test_low_stress(self):
        h = AgentHealth(agent_id="test")
        for _ in range(10):
            h.record_response(success=True, latency_ms=100)
        detector = StressDetector()
        report = detector.assess(h)
        assert report.level == StressLevel.LOW
        assert report.score < 25

    def test_moderate_stress(self):
        h = AgentHealth(agent_id="test")
        for _ in range(7):
            h.record_response(success=True, latency_ms=200)
        for _ in range(3):
            h.record_response(success=False, latency_ms=2000)
        detector = StressDetector()
        report = detector.assess(h)
        assert report.level in (StressLevel.MODERATE, StressLevel.HIGH)

    def test_critical_stress(self):
        h = AgentHealth(agent_id="test")
        for _ in range(8):
            h.record_response(success=False, latency_ms=5000)
        detector = StressDetector()
        report = detector.assess(h)
        assert report.level == StressLevel.CRITICAL
        assert report.score >= 75

    def test_contributors_on_errors(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=False, latency_ms=500)
        detector = StressDetector(error_threshold=0.1)
        report = detector.assess(h)
        assert any("error rate" in c.lower() for c in report.contributors)

    def test_contributors_on_latency(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=True, latency_ms=10000)
        detector = StressDetector(latency_baseline_ms=500)
        report = detector.assess(h)
        assert any("latency" in c.lower() for c in report.contributors)

    def test_recommendation_critical(self):
        h = AgentHealth(agent_id="test")
        for _ in range(10):
            h.record_response(success=False, latency_ms=5000)
        report = StressDetector().assess(h)
        assert "intervention" in report.recommendation.lower()

    def test_recommendation_low(self):
        h = AgentHealth(agent_id="test")
        for _ in range(10):
            h.record_response(success=True, latency_ms=100)
        report = StressDetector().assess(h)
        assert "healthy" in report.recommendation.lower()


class TestStressLevelComparison:
    def test_ordering(self):
        assert StressLevel.LOW < StressLevel.MODERATE
        assert StressLevel.MODERATE < StressLevel.HIGH
        assert StressLevel.HIGH < StressLevel.CRITICAL
        assert not (StressLevel.CRITICAL < StressLevel.LOW)

    def test_ge_le(self):
        assert StressLevel.HIGH >= StressLevel.MODERATE
        assert StressLevel.LOW <= StressLevel.LOW


class TestStressFromSnapshot:
    def test_assess_snapshot(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=True, latency_ms=100)
        snap = h.snapshot()
        detector = StressDetector()
        report = detector.assess_snapshot(snap)
        assert report.level == StressLevel.LOW
        assert report.error_rate == 0.0

    def test_assess_snapshot_stressed(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=False, latency_ms=5000)
        snap = h.snapshot()
        report = StressDetector().assess_snapshot(snap)
        assert report.level >= StressLevel.HIGH
