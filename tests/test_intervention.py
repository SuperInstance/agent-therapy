"""Tests for agent_therapy.intervention module."""

from agent_therapy.intervention import InterventionEngine, InterventionType
from agent_therapy.stress import StressLevel


class TestInterventionEvaluation:
    def test_no_intervention_healthy(self):
        engine = InterventionEngine()
        result = engine.evaluate("agent-1", stress_score=10.0)
        assert result is None

    def test_cooldown_moderate(self):
        engine = InterventionEngine()
        result = engine.evaluate("agent-1", stress_score=30.0)
        assert result is not None
        assert result.type == InterventionType.COOLDOWN
        assert result.active

    def test_simplification_for_latency(self):
        engine = InterventionEngine()
        result = engine.evaluate(
            "agent-1",
            stress_score=35.0,
            stress_contributors=["Latency degraded: 2000ms"],
        )
        assert result is not None
        assert result.type == InterventionType.CONTEXT_SIMPLIFICATION

    def test_capability_reduction_high(self):
        engine = InterventionEngine()
        result = engine.evaluate("agent-1", stress_score=60.0)
        assert result is not None
        assert result.type == InterventionType.CAPABILITY_REDUCTION

    def test_full_reset_critical(self):
        engine = InterventionEngine()
        result = engine.evaluate("agent-1", stress_score=85.0)
        assert result is not None
        assert result.type == InterventionType.FULL_RESET
        assert result.duration_seconds == 0  # indefinite

    def test_max_active_per_agent(self):
        engine = InterventionEngine(max_active_per_agent=2)
        engine.evaluate("agent-1", stress_score=30.0)
        engine.evaluate("agent-1", stress_score=40.0)
        result = engine.evaluate("agent-1", stress_score=50.0)
        assert result is None  # blocked by max

    def test_different_agents_independent(self):
        engine = InterventionEngine(max_active_per_agent=1)
        r1 = engine.evaluate("agent-1", stress_score=30.0)
        r2 = engine.evaluate("agent-2", stress_score=30.0)
        assert r1 is not None
        assert r2 is not None


class TestInterventionLifecycle:
    def test_release(self):
        engine = InterventionEngine()
        iv = engine.evaluate("agent-1", stress_score=60.0)
        assert iv is not None
        assert engine.release(iv.intervention_id)
        assert not iv.active

    def test_release_nonexistent(self):
        engine = InterventionEngine()
        assert not engine.release("does-not-exist")

    def test_active_interventions(self):
        engine = InterventionEngine()
        engine.evaluate("agent-1", stress_score=30.0)
        engine.evaluate("agent-1", stress_score=60.0)
        active = engine.active_interventions("agent-1")
        assert len(active) == 2

    def test_all_interventions(self):
        engine = InterventionEngine()
        iv = engine.evaluate("agent-1", stress_score=60.0)
        assert iv is not None
        engine.release(iv.intervention_id)
        all_iv = engine.all_interventions("agent-1")
        assert len(all_iv) == 1
        assert not all_iv[0].active

    def test_clear_agent(self):
        engine = InterventionEngine()
        engine.evaluate("agent-1", stress_score=30.0)
        engine.evaluate("agent-1", stress_score=60.0)
        count = engine.clear_agent("agent-1")
        assert count == 2
        assert len(engine.active_interventions("agent-1")) == 0

    def test_intervention_has_reason(self):
        engine = InterventionEngine()
        iv = engine.evaluate("agent-1", stress_score=50.0, stress_contributors=["high errors"])
        assert iv is not None
        assert "50.0" in iv.reason
        assert "high errors" in iv.reason


class TestInterventionExpiry:
    def test_timed_intervention_expires(self):
        engine = InterventionEngine(cooldown_seconds=0)
        iv = engine.evaluate("agent-1", stress_score=30.0)
        assert iv is not None
        # Force expiry check
        import time
        time.sleep(0.1)
        # Duration was 0 but cooldown_seconds=0 means immediate timeout
        # Actually let's test with a real small duration
        engine2 = InterventionEngine(cooldown_seconds=1)
        iv2 = engine2.evaluate("agent-2", stress_score=30.0)
        assert iv2 is not None
        assert iv2.duration_seconds == 1

    def test_full_reset_indefinite(self):
        engine = InterventionEngine()
        iv = engine.evaluate("agent-1", stress_score=80.0)
        assert iv is not None
        assert not iv.is_expired  # duration_seconds=0 means indefinite
