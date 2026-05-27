"""Tests for agent_therapy.wellness module."""

from agent_therapy.health import AgentHealth
from agent_therapy.wellness import BurnoutRisk, WellnessTracker


class TestWellnessTrackerBasic:
    def test_record_returns_snapshot(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        snap = tracker.record(h)
        assert snap.total_requests == 1

    def test_report_no_data(self):
        tracker = WellnessTracker()
        report = tracker.report("nonexistent")
        assert report is None

    def test_report_basic(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        tracker.record(h)
        report = tracker.report("test")
        assert report is not None
        assert report.total_snapshots == 1
        assert report.avg_error_rate == 0.0

    def test_history(self):
        h = AgentHealth(agent_id="test")
        tracker = WellnessTracker()
        for i in range(5):
            h.record_response(success=True, latency_ms=float(100 + i * 50))
            tracker.record(h)
        hist = tracker.history("test")
        assert len(hist) == 5

    def test_agents_tracked(self):
        h1 = AgentHealth(agent_id="a1")
        h2 = AgentHealth(agent_id="a2")
        h1.record_response(success=True, latency_ms=100)
        h2.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        tracker.record(h1)
        tracker.record(h2)
        assert set(tracker.agents_tracked()) == {"a1", "a2"}


class TestBurnoutPrediction:
    def test_healthy_no_burnout(self):
        h = AgentHealth(agent_id="test")
        tracker = WellnessTracker()
        for _ in range(10):
            h.record_response(success=True, latency_ms=100)
            tracker.record(h)
        report = tracker.report("test")
        assert report is not None
        assert report.burnout_risk in (BurnoutRisk.NONE, BurnoutRisk.LOW)

    def test_stressed_high_burnout(self):
        h = AgentHealth(agent_id="test")
        tracker = WellnessTracker()
        for _ in range(10):
            h.record_response(success=False, latency_ms=5000)
            tracker.record(h)
        report = tracker.report("test")
        assert report is not None
        assert report.burnout_risk in (BurnoutRisk.HIGH, BurnoutRisk.IMMINENT)

    def test_escalating_trend(self):
        tracker = WellnessTracker()
        # Phase 1: healthy
        h1 = AgentHealth(agent_id="test")
        for _ in range(5):
            h1.record_response(success=True, latency_ms=100)
        tracker.record(h1)
        # Phase 2: degrading
        h2 = AgentHealth(agent_id="test")
        for _ in range(5):
            h2.record_response(success=False, latency_ms=3000)
        tracker.record(h2)
        # Phase 3: critical
        h3 = AgentHealth(agent_id="test")
        for _ in range(5):
            h3.record_response(success=False, latency_ms=5000)
        tracker.record(h3)
        report = tracker.report("test")
        assert report is not None
        assert report.stress_trend > 0  # worsening

    def test_improving_trend(self):
        tracker = WellnessTracker()
        # Phase 1: stressed (6 snapshots)
        for _ in range(6):
            h1 = AgentHealth(agent_id="test")
            for _ in range(5):
                h1.record_response(success=False, latency_ms=5000)
            tracker.record(h1)
        # Phase 2: recovering (6 snapshots)
        for _ in range(6):
            h2 = AgentHealth(agent_id="test")
            for _ in range(5):
                h2.record_response(success=True, latency_ms=100)
            tracker.record(h2)
        report = tracker.report("test")
        assert report is not None
        assert report.stress_trend < 0  # improving


class TestWellnessReport:
    def test_report_has_current_health(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        tracker.record(h)
        report = tracker.report("test")
        assert report is not None
        assert report.current_health is not None

    def test_clear_agent(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        tracker.record(h)
        tracker.clear("test")
        assert tracker.report("test") is None

    def test_clear_all(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        tracker.record(h)
        tracker.clear()
        assert tracker.report("test") is None

    def test_max_history(self):
        h = AgentHealth(agent_id="test")
        tracker = WellnessTracker(max_history=5)
        for _ in range(10):
            h.record_response(success=True, latency_ms=100)
            tracker.record(h)
        hist = tracker.history("test")
        assert len(hist) <= 5


class TestWellnessRecommendation:
    def test_healthy_recommendation(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=True, latency_ms=100)
        tracker = WellnessTracker()
        tracker.record(h)
        report = tracker.report("test")
        assert "excellent" in report.recommendation.lower() or "maintain" in report.recommendation.lower()

    def test_stressed_recommendation(self):
        h = AgentHealth(agent_id="test")
        for _ in range(10):
            h.record_response(success=False, latency_ms=5000)
        tracker = WellnessTracker()
        tracker.record(h)
        report = tracker.report("test")
        assert len(report.recommendation) > 0
