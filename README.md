# agent-therapy

Behavioral health monitoring, stress detection, and intervention for AI agents.

Part of the [Cocapn fleet](https://github.com/Lucineer/the-fleet).

---

## Install

```bash
pip install agent-therapy
```

For development:

```bash
git clone https://github.com/SuperInstance/agent-therapy.git
cd agent-therapy
pip install -e ".[dev]"
```

## Quick Start

```python
from agent_therapy import AgentHealth, StressDetector, WellnessTracker, TherapyJournal

# Track an agent's health
health = AgentHealth(agent_id="agent-42")
health.record_response(success=True, latency_ms=120)
health.record_response(success=True, latency_ms=95)
health.record_response(success=False, latency_ms=3500)

# Get a snapshot
snapshot = health.snapshot()
print(f"Error rate: {snapshot.error_rate:.1%}")
print(f"Avg latency: {snapshot.avg_latency_ms:.0f}ms")
print(f"Healthy: {snapshot.is_healthy}")

# Detect stress
detector = StressDetector(error_threshold=0.10, latency_baseline_ms=500)
report = detector.assess(health)
print(f"Stress level: {report.level.name}")  # LOW / MODERATE / HIGH / CRITICAL
print(f"Score: {report.score:.1f}/100")
print(f"Recommendation: {report.recommendation}")

# Track wellness over time
tracker = WellnessTracker()
tracker.record(health)
wellness = tracker.report("agent-42")
print(f"Burnout risk: {wellness.burnout_risk.name}")
print(f"Stress trend: {wellness.stress_trend:+.1f} ({'worsening' if wellness.stress_trend > 0 else 'improving'})")

# Journal incidents and reflections
journal = TherapyJournal()
journal.log_incident(
    "agent-42", "Error spike", "Error rate hit 35% during peak load",
    severity="warning", tags=["errors", "peak-load"],
)
journal.log_reflection(
    "agent-42", "Post-incident review",
    "Root cause was context overflow. Simplification resolved it.",
)
```

## Interventions

```python
from agent_therapy import InterventionEngine

engine = InterventionEngine(
    cooldown_seconds=300,
    simplification_seconds=600,
    reduction_seconds=900,
)

# Evaluate based on stress
intervention = engine.evaluate("agent-42", stress_score=65.0)
if intervention:
    print(f"Applied: {intervention.type.name}")
    print(f"Reason: {intervention.reason}")
    print(f"Duration: {intervention.duration_seconds}s")

    # Later, release the intervention
    engine.release(intervention.intervention_id)

# Check active interventions
active = engine.active_interventions("agent-42")
```

## Module Reference

### `agent_therapy.health`

- **`AgentHealth`** — Tracks response success/failure, latency, and quality metrics with a sliding window.
- **`HealthSnapshot`** — Immutable point-in-time snapshot of agent health.

### `agent_therapy.stress`

- **`StressDetector`** — Analyzes health data to classify stress (LOW / MODERATE / HIGH / CRITICAL).
- **`StressReport`** — Detailed stress assessment with contributors and recommendations.

### `agent_therapy.intervention`

- **`InterventionEngine`** — Manages cooldown, context simplification, capability reduction, and full resets.
- **`Intervention`** — Represents a single intervention action.

### `agent_therapy.wellness`

- **`WellnessTracker`** — Records health history and predicts burnout risk.
- **`WellnessReport`** — Trend analysis with burnout risk classification.

### `agent_therapy.journal`

- **`TherapyJournal`** — Structured logging of incidents, reflections, recovery plans, and milestones.
- **`JournalEntry`** — Single journal entry with optional file persistence (JSONL).

## Running Tests

```bash
python -m pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE).

---
<i>Built with [Cocapn](https://github.com/Lucineer/cocapn-ai).</i>
