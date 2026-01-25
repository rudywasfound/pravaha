# Operational Integration: From Lab to Real Satellites

This module transforms Pravaha from a research tool into an operational diagnostic system for real satellites.

## Current Status

**Phase:** 1 (Telemetry Simulator) ✓ COMPLETE  
**Next:** Phase 2 (Inference Service) — I will do this later
**Timeline:** 2-4 weeks to operational MVP

## What's Here

### 1. telemetry_simulator.py ✓
Generates realistic satellite telemetry for testing without real data.

**Features:**
- Nominal operation (healthy satellite)
- Solar degradation (GSAT-6A scenario)
- Battery aging (capacity loss)
- Thermal stress (overheating)
- Sensor bias (measurement drift)
- Multi-fault scenarios
- Configurable sensor noise
- Time-series generation

**Quick Start:**
```python
from operational.telemetry_simulator import TelemetrySimulator

# Create simulator
sim = TelemetrySimulator(scenario="solar_degradation")

# Generate 1 hour of telemetry
for measurement in sim.generate_series(duration_seconds=3600):
    print(measurement.battery_voltage_measured)
    # Feed to Pravaha inference
```

**Test It:**
```bash
python operational/telemetry_simulator.py
```

Shows sample data for each scenario.

## Architecture Overview

```
REAL SATELLITE OPERATIONS:

Satellite (orbit)
    ↓ telemetry downlink
    
Ground Station
    ├─ Antenna
    ├─ Demodulator  
    └─ Frame Parser
         ↓
Data Ingestion
    ├─ Telemetry Decoder (CCSDS, custom format, etc.)
    ├─ Measurement Buffer (rolling 10 min window)
    └─ Validation/QC
         ↓
Pravaha Inference Service (runs every 10 sec)
    ├─ Read measurements
    ├─ Detect anomalies
    ├─ Rank root causes
    └─ Generate diagnosis
         ↓
Alert System
    ├─ Email operators
    ├─ Slack/Teams
    ├─ Log to incident DB
    └─ Update dashboard
         ↓
Mission Control Dashboard
    ├─ Live telemetry plots
    ├─ Current diagnosis
    ├─ Interactive DAG visualization
    └─ Confidence/probability
         ↓
Operators
    ├─ Review diagnosis
    ├─ Check against patterns
    ├─ Decide corrective action
    └─ Command satellite
```

## Why We're Building This

Currently, Pravaha lives in code. Real operators need:

1. **Continuous Monitoring** — Not just on-demand analysis
2. **Real Data Integration** — Must connect to actual satellite feeds
3. **Live Dashboard** — See diagnoses as they happen
4. **Historical Analysis** — Learn from past incidents
5. **Validation** — Prove it works before going live

This module bridges that gap.

## The Four Phases

### Phase 1: Telemetry Simulator ✓ DONE
- Generate synthetic measurements
- Test inference on known scenarios
- Validate diagnoses are correct

**Deliverable:** telemetry_simulator.py

### Phase 2: Inference Service (NEXT)
- Continuous monitoring engine
- Rolling window of measurements
- Real-time diagnosis ranking
- Alert generation

**Files to Create:**
- telemetry_buffer.py
- inference_service.py
- alert_system.py

### Phase 3: API & Dashboard
- REST API for diagnosis queries
- Web dashboard with live plots
- Embed interactive DAG
- Confidence visualization

**Files to Create:**
- api.py
- dashboard.html
- static/ (CSS, JS)

### Phase 4: Data Persistence
- Time-series database
- Store all measurements
- Store all diagnoses
- Query historical data

**Files to Create:**
- database.py
- queries.py
- migrations/

## How It Works

### 1. Telemetry Ingestion

```python
# Real satellite or simulator
telemetry = TelemetrySimulator(scenario="solar_degradation")

# Generate measurement
measurement = telemetry.generate()

# Add to buffer (rolling window)
buffer.add(measurement)
```

### 2. Inference

```python
# Run every 10 seconds (or continuously)
diagnosis = ranker.analyze(buffer.get_window())

print(f"Root cause: {diagnosis[0].cause}")
print(f"Probability: {diagnosis[0].probability:.1%}")
print(f"Confidence: {diagnosis[0].confidence:.1%}")
```

### 3. Alerts

```python
# If significant change detected
if diagnosis[0].cause != previous_diagnosis[0].cause:
    alert = Alert(
        type="new_diagnosis",
        from_cause=previous_diagnosis[0].cause,
        to_cause=diagnosis[0].cause,
        confidence=diagnosis[0].confidence
    )
    send_alert(alert)  # Email, Slack, SMS
```

### 4. Dashboard

Operators see:
- Live telemetry plots (battery voltage, temp, etc.)
- Current diagnosis with probability bar
- Interactive DAG showing causal paths
- Alert history
- Recommendation for next action

## Integration with Existing Code

### Inference Engine
```python
from causal_graph.root_cause_ranking import RootCauseRanker
from causal_graph.graph_definition import CausalGraph

graph = CausalGraph()
ranker = RootCauseRanker(graph)

# Analyze measurements from telemetry buffer
diagnoses = ranker.analyze(measurements)
```

### Visualization
```python
# Interactive DAG already exists!
# Dashboard embeds: causal_graph/dag_visualization.html
```

### Historical Analysis
```python
# Once Phase 4 is done:
from operational.queries import analyze_incident

result = analyze_incident(
    start_time='2026-01-25 10:00:00',
    end_time='2026-01-25 11:00:00'
)

print(result['diagnosis_evolution'])
print(result['alerts'])
```

## Success Criteria

| Goal | Metric | Status |
|------|--------|--------|
| Generate synthetic telemetry | Works for 6 scenarios | ✓ DONE |
| Inference on synthetic data | Diagnoses < 2 min | PHASE 2 |
| Real-time monitoring | Process 1+ Hz data | PHASE 2 |
| Dashboard | Live plots + diagnosis | PHASE 3 |
| Data persistence | 30-day history | PHASE 4 |
| Operator training | 1 hour to proficiency | PHASE 3 |
| Lead time vs threshold | Detect 2+ min earlier | VALIDATION |

## Testing Strategy

### Unit Tests
```bash
python -m pytest operational/tests/test_telemetry_simulator.py
```

### Integration Test
```bash
# Run simulator + inference + alerts
python operational/test_e2e.py
```

### Scenario Testing
```python
# Test each failure mode
for scenario in ['solar_degradation', 'battery_aging', ...]:
    sim = TelemetrySimulator(scenario)
    for meas in sim.generate_series(3600):
        diagnosis = ranker.analyze([meas])
        assert diagnosis[0].cause == expected_cause
```

## Real-World Deployment

When ready for actual satellite:

1. **Data Format Adapter**
   - Parse ISRO/customer telemetry format
   - Map to node names
   - Handle compression, encryption

2. **Deployment Container**
   ```bash
   docker build -t pravaha-service .
   docker run -e TELEMETRY_HOST=ground-station pravaha-service
   ```

3. **Integration Testing**
   - Historical replay on past missions
   - Parallel run with current system
   - Validation of diagnoses vs. real events

4. **Operator Handoff**
   - 1-hour briefing on causal framework
   - 30-min hands-on with dashboard
   - 1 week observation
   - Go-live decision

## Files to Create (Roadmap)

```
operational/
├─ __init__.py                    ✓
├─ README.md                      ✓ (this file)
├─ telemetry_simulator.py         ✓
├─ telemetry_buffer.py            (Phase 2)
├─ inference_service.py           (Phase 2)
├─ alert_system.py                (Phase 2)
├─ api.py                         (Phase 3)
├─ dashboard.html                 (Phase 3)
├─ static/
│  ├─ style.css                   (Phase 3)
│  └─ dashboard.js                (Phase 3)
├─ database.py                    (Phase 4)
├─ queries.py                     (Phase 4)
├─ models.py                      (Phase 4)
├─ migrations/                    (Phase 4)
├─ tests/
│  ├─ test_telemetry_simulator.py ✓
│  ├─ test_inference_service.py   (Phase 2)
│  ├─ test_api.py                 (Phase 3)
│  └─ test_e2e.py                 (Integration test)
├─ docker/
│  ├─ Dockerfile                  (Phase 3)
│  └─ docker-compose.yml          (Phase 3)
└─ examples/
   ├─ basic_monitoring.py         (Phase 2)
   └─ dashboard_integration.py     (Phase 3)
```

## Dependencies

**Already installed:**
- numpy (telemetry generation)
- pandas (data manipulation)
- causal_graph module

**Coming later:**
- flask/fastapi (Phase 3, API)
- plotly (Phase 3, dashboard)
- sqlalchemy (Phase 4, database)
- psycopg2 (Phase 4, PostgreSQL)

## Quick Links

- **Roadmap:** `../OPERATIONAL_INTEGRATION_ROADMAP.md`
- **Causal DAG:** `../causal_graph/DAG_DOCUMENTATION.md`
- **Visualization:** `../VISUALIZATION_COMPLETE.md`
- **Inference Engine:** `../causal_graph/root_cause_ranking.py`

## Next Steps

**Now:**
1. ✓ Telemetry simulator complete
2. Run simulator on all scenarios
3. Verify reasonable data generation

**This Week:**
4. Build telemetry_buffer.py
5. Build inference_service.py
6. Run end-to-end: sim → buffer → service
7. Verify diagnoses are correct

**Next Week:**
8. Add alert system
9. Build REST API
10. Create basic dashboard

**Following Week:**
11. Integrate with visualization
12. Add database persistence
13. Historical analysis tools

---

**Status:** Ready for Phase 2  
**Owner:** [Your team]  
**Timeline:** 2-4 weeks to operational MVP  
**Goal:** Get Pravaha running on real satellite by Q1 2026
