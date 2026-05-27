"""Tests for agent_therapy.health module."""

from datetime import datetime, timezone

from agent_therapy.health import AgentHealth


class TestAgentHealthBasic:
    def test_empty_health(self):
        h = AgentHealth(agent_id="test")
        assert h.total_requests == 0
        assert h.error_count == 0
        assert h.success_count == 0
        assert h.error_rate == 0.0
        assert h.avg_latency_ms == 0.0
        assert h.avg_quality == 1.0

    def test_record_success(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        assert h.total_requests == 1
        assert h.success_count == 1
        assert h.error_count == 0
        assert h.error_rate == 0.0
        assert h.avg_latency_ms == 100.0

    def test_record_errors(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        h.record_response(success=False, latency_ms=5000)
        assert h.total_requests == 2
        assert h.error_rate == 0.5

    def test_quality_inference_fast_success(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        assert h.avg_quality == 1.0

    def test_quality_inference_error(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=False, latency_ms=100)
        assert h.avg_quality == 0.0

    def test_quality_inference_slow(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=3000)
        assert 0.2 < h.avg_quality < 1.0

    def test_explicit_quality(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100, quality=0.5)
        assert h.avg_quality == 0.5

    def test_window_trimming(self):
        h = AgentHealth(agent_id="test", window_size=5)
        for i in range(10):
            h.record_response(success=True, latency_ms=float(i * 100))
        assert h.total_requests == 5
        assert h.avg_latency_ms == sum(i * 100 for i in range(5, 10)) / 5

    def test_reset(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        h.reset()
        assert h.total_requests == 0


class TestHealthSnapshot:
    def test_snapshot_healthy(self):
        h = AgentHealth(agent_id="test")
        for _ in range(10):
            h.record_response(success=True, latency_ms=200)
        snap = h.snapshot()
        assert snap.is_healthy
        assert snap.error_rate == 0.0
        assert snap.success_count == 10

    def test_snapshot_unhealthy(self):
        h = AgentHealth(agent_id="test")
        for _ in range(10):
            h.record_response(success=False, latency_ms=5000)
        snap = h.snapshot()
        assert not snap.is_healthy
        assert snap.error_rate == 1.0

    def test_snapshot_fields(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        snap = h.snapshot()
        assert snap.timestamp.tzinfo is not None
        assert snap.error_rate_pct == 0.0
        assert snap.p95_latency_ms == 100.0

    def test_p95_latency(self):
        h = AgentHealth(agent_id="test")
        for i in range(20):
            h.record_response(success=True, latency_ms=float(i * 100))
        snap = h.snapshot()
        assert snap.p95_latency_ms >= 1000  # should be near the top

    def test_stress_score_healthy(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=True, latency_ms=100)
        snap = h.snapshot()
        assert snap.stress_level_raw < 10

    def test_stress_score_stressed(self):
        h = AgentHealth(agent_id="test")
        for _ in range(5):
            h.record_response(success=False, latency_ms=5000)
        snap = h.snapshot()
        assert snap.stress_level_raw > 50

    def test_latency_stdev(self):
        h = AgentHealth(agent_id="test")
        h.record_response(success=True, latency_ms=100)
        assert h.latency_stdev() == 0.0
        h.record_response(success=True, latency_ms=900)
        assert h.latency_stdev() > 0
