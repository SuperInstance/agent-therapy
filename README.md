# agent-therapy — Behavioral Health Monitoring for AI Agents

**Stress detection, wellness tracking, and intervention management for autonomous agents.**

## What This Gives You

- **Stress detection** — assess agent stress from error rates, latency spikes, and response patterns
- **Wellness tracking** — ongoing health scores based on performance metrics
- **Intervention management** — trigger cooldowns, retries, or escalation when agents are struggling
- **Therapy journaling** — record behavioral events for post-incident analysis
- **Configurable thresholds** — set stress and wellness thresholds per agent or fleet-wide

## Quick Start

```bash
pip install agent-therapy
```

```python
from agent_therapy import AgentHealth, StressDetector, WellnessTracker

# Track agent health
health = AgentHealth(agent_id="agent-42")
health.record_response(success=True, latency_ms=120)
health.record_response(success=False, latency_ms=3500)

# Detect stress
detector = StressDetector()
stress = detector.assess(health)
print(f"Stress level: {stress.level}")  # LOW, MODERATE, HIGH, CRITICAL
print(f"Indicators: {stress.indicators}")

# Track wellness over time
tracker = WellnessTracker()
tracker.update(health)
score = tracker.score("agent-42")
print(f"Wellness: {score}/100")

# Intervene if needed
from agent_therapy import InterventionManager
manager = InterventionManager()
if stress.level == "CRITICAL":
    intervention = manager.intervene(health, stress)
    print(f"Action: {intervention.action}")  # COOLDOWN, RETRY, ESCALATE, RESTART
```

## API Reference

### `AgentHealth(agent_id)` — `record_response(success, latency_ms)`
### `StressDetector` — `assess(health) → StressReport(level, indicators, recommendation)`
### `WellnessTracker` — `update(health)`, `score(agent_id) → float`
### `InterventionManager` — `intervene(health, stress) → Intervention`

## How It Fits

Behavioral health layer for the [SuperInstance fleet](https://github.com/SuperInstance). Works alongside [cocapn-explain](https://github.com/SuperInstance/cocapn-explain) to give full visibility into agent state.

- **[fleet-health-monitor](https://github.com/SuperInstance/fleet-health-monitor)** — System-level health daemon
- **[cocapn-explain](https://github.com/SuperInstance/cocapn-explain)** — Decision explainability
- **[agent-personal-space](https://github.com/SuperInstance/agent-personal-space)** — Boundary management

## Testing

```bash
pytest tests/
```

## Installation

```bash
pip install agent-therapy
```

Python 3.10+. MIT license.
