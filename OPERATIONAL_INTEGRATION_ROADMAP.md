# Operational Integration Roadmap

**Focus:** Connect Pravaha to real satellite operations  
**Timeline:** 2-4 weeks for MVP  
**Status:** Ready to begin

---

## Current State vs. Operational Reality

### What We Have ✓
- Causal DAG (23 nodes, 29 edges)
- Inference engine (root_cause_ranking.py)
- Interactive visualization (dag_visualization.html)
- D-separation validation
- GSAT-6A historical case study

### What's Missing ❌
- Real-time telemetry ingestion
- Continuous monitoring service
- Operational alerts
- Mission control integration
- Data persistence (history)
- Automated response coordination

---

## Phase 1: Telemetry Simulator (Week 1)

**Goal:** Test the full pipeline WITHOUT real satellite  
**Output:** Synthetic telemetry generator that mimics real data

### 1.1 Create Telemetry Generator
```python
# pravaha/telemetry_simulator.py

class TelemetrySimulator:
    """Generate realistic satellite measurements for testing."""
    
    def __init__(self, scenario="nominal"):
        self.scenario = scenario  # "nominal", "solar_degradation", etc.
    
    def generate_measurements(self, timestamp):
        """Return dict matching observable node names."""
        return {
            'battery_voltage_measured': 28.5,
            'battery_charge_measured': 95.2,
            'battery_temp_measured': 35.0,
            'bus_voltage_measured': 29.1,
            'bus_current_measured': 12.3,
            'solar_input_measured': 420.0,
            'solar_panel_temp_measured': 45.0,
            'payload_temp_measured': 38.0,
        }
```

### 1.2 Scenario Library
```
scenarios/
├─ nominal.py              (healthy satellite)
├─ solar_degradation.py    (GSAT-6A scenario)
├─ battery_aging.py        (gradual capacity loss)
├─ thermal_stress.py       (overheating)
├─ sensor_drift.py         (measurement bias)
└─ multi_fault.py          (simultaneous failures)
```

### 1.3 Validation
- Generate data for each scenario
- Feed to Pravaha inference
- Verify correct diagnosis
- Plot telemetry over time

---

## Phase 2: Inference Service (Week 2)

**Goal:** Run continuous monitoring on a time series  
**Output:** Service that produces diagnoses every N seconds

### 2.1 Telemetry Buffer
```python
# pravaha/telemetry_buffer.py

class MeasurementBuffer:
    """Rolling window of recent measurements."""
    
    def __init__(self, window_size=600):  # 10 min @ 1 Hz
        self.window = deque(maxlen=window_size)
    
    def add(self, measurement_dict, timestamp):
        """Add new measurement."""
        self.window.append({'timestamp': timestamp, **measurement_dict})
    
    def get_latest(self):
        """Return most recent measurement."""
        return self.window[-1] if self.window else None
    
    def get_window(self):
        """Return entire rolling window."""
        return list(self.window)
```

### 2.2 Diagnosis Service
```python
# pravaha/inference_service.py

class PravahaDiagnosisService:
    """Continuous monitoring and root cause ranking."""
    
    def __init__(self, graph, buffer):
        self.ranker = RootCauseRanker(graph)
        self.buffer = buffer
        self.diagnosis_history = []
    
    def step(self):
        """Analyze current measurements."""
        measurements = self.buffer.get_window()
        if len(measurements) < 2:
            return None
        
        # Compute diagnosis
        diagnosis = self.ranker.analyze(measurements)
        
        # Store in history
        self.diagnosis_history.append({
            'timestamp': datetime.now(),
            'top_cause': diagnosis[0],
            'probability': diagnosis[0].probability,
            'confidence': diagnosis[0].confidence,
        })
        
        return diagnosis
```

### 2.3 Alert System
```python
# pravaha/alert_system.py

class AlertManager:
    """Generate alerts when diagnosis changes."""
    
    def check_for_alerts(self, previous, current):
        """Compare diagnoses, emit alerts if significant change."""
        if not previous:
            return []
        
        alerts = []
        
        # Alert on new root cause detection
        if current[0].cause != previous[0].cause:
            alerts.append({
                'type': 'new_diagnosis',
                'from': previous[0].cause,
                'to': current[0].cause,
                'confidence': current[0].confidence,
            })
        
        # Alert on high confidence
        if current[0].confidence > 0.85:
            alerts.append({
                'type': 'high_confidence',
                'cause': current[0].cause,
                'confidence': current[0].confidence,
            })
        
        return alerts
```

---

## Phase 3: API & Dashboard Integration (Week 3)

**Goal:** Real operators can query diagnoses and see visualization  
**Output:** REST API + simple web dashboard

### 3.1 REST API
```python
# pravaha/api.py

from flask import Flask, jsonify

app = Flask(__name__)
service = PravahaDiagnosisService(graph, buffer)

@app.route('/api/current-diagnosis')
def get_current_diagnosis():
    """Latest diagnosis."""
    diagnosis = service.diagnosis_history[-1]
    return jsonify({
        'timestamp': diagnosis['timestamp'].isoformat(),
        'root_cause': diagnosis['top_cause'],
        'probability': diagnosis['probability'],
        'confidence': diagnosis['confidence'],
    })

@app.route('/api/diagnosis-history')
def get_history(limit=100):
    """Last N diagnoses."""
    return jsonify(service.diagnosis_history[-limit:])

@app.route('/api/dag')
def get_dag():
    """DAG structure for visualization."""
    return jsonify({
        'nodes': [
            {'id': n.name, 'type': n.node_type.value}
            for n in graph.nodes.values()
        ],
        'edges': [
            {'source': e.source, 'target': e.target, 'weight': e.weight}
            for e in graph.edges
        ],
    })

@app.route('/api/measurements')
def get_measurements(lookback_seconds=3600):
    """Time series of measurements."""
    now = datetime.now()
    cutoff = now - timedelta(seconds=lookback_seconds)
    
    filtered = [
        m for m in buffer.get_window()
        if m['timestamp'] > cutoff
    ]
    return jsonify(filtered)
```

### 3.2 Dashboard
```html
<!-- pravaha/dashboard.html -->

<html>
<body>
  <div class="header">
    <h1>Satellite Health Dashboard</h1>
  </div>
  
  <div class="main-grid">
    <!-- LEFT: Measurements -->
    <div class="measurements">
      <h2>Live Telemetry</h2>
      <canvas id="telemetry-plot"></canvas>
    </div>
    
    <!-- CENTER: Diagnosis -->
    <div class="diagnosis-panel">
      <h2>Current Diagnosis</h2>
      <div id="diagnosis-display">
        <p><b>Root Cause:</b> <span id="cause"></span></p>
        <p><b>Probability:</b> <span id="prob"></span></p>
        <p><b>Confidence:</b> <span id="conf"></span></p>
      </div>
    </div>
    
    <!-- RIGHT: DAG -->
    <div class="dag-panel">
      <h2>Causal Structure</h2>
      <div id="dag-container"></div>
    </div>
  </div>
  
  <script>
    // Fetch current diagnosis every 10 seconds
    setInterval(() => {
      fetch('/api/current-diagnosis')
        .then(r => r.json())
        .then(data => {
          document.getElementById('cause').textContent = data.root_cause;
          document.getElementById('prob').textContent = 
            (data.probability * 100).toFixed(1) + '%';
          document.getElementById('conf').textContent = 
            (data.confidence * 100).toFixed(1) + '%';
        });
    }, 10000);
    
    // Load and display interactive DAG
    fetch('/api/dag')
      .then(r => r.json())
      .then(data => {
        // Render with Plotly (reuse dag_visualization.html logic)
        renderDAG(data);
      });
  </script>
</body>
</html>
```

---

## Phase 4: Data Persistence (Week 4)

**Goal:** Store all diagnoses and telemetry for analysis  
**Output:** Time-series database with query API

### 4.1 Database Schema
```sql
-- Measurements table (write once per second)
CREATE TABLE measurements (
    timestamp TIMESTAMP PRIMARY KEY,
    battery_voltage_measured FLOAT,
    battery_charge_measured FLOAT,
    battery_temp_measured FLOAT,
    bus_voltage_measured FLOAT,
    bus_current_measured FLOAT,
    solar_input_measured FLOAT,
    solar_panel_temp_measured FLOAT,
    payload_temp_measured FLOAT
);

-- Diagnoses table (write when significant change)
CREATE TABLE diagnoses (
    timestamp TIMESTAMP PRIMARY KEY,
    root_cause VARCHAR(255),
    probability FLOAT,
    confidence FLOAT,
    supporting_measurements JSON
);

-- Alerts table (triggered events)
CREATE TABLE alerts (
    timestamp TIMESTAMP PRIMARY KEY,
    alert_type VARCHAR(255),
    root_cause VARCHAR(255),
    severity VARCHAR(50),  -- INFO, WARNING, CRITICAL
    message TEXT
);
```

### 4.2 Query Examples
```python
# Post-incident analysis
def analyze_incident(start_time, end_time):
    """Reconstruct what Pravaha saw during incident."""
    telemetry = query_measurements(start_time, end_time)
    diagnoses = query_diagnoses(start_time, end_time)
    
    return {
        'telemetry_time_series': telemetry,
        'diagnosis_evolution': diagnoses,
        'alerts': query_alerts(start_time, end_time),
    }
```

---

## Implementation Sequence

```
WEEK 1: Telemetry Simulator
├─ Create synthetic data generator
├─ Build scenario library (nominal, degradation, etc.)
├─ Test inference on synthetic data
└─ Validate diagnoses are correct

WEEK 2: Inference Service
├─ Build measurement buffer
├─ Implement continuous diagnosis
├─ Add alert system
└─ Integration test (sim → service → alerts)

WEEK 3: API & Dashboard
├─ REST API for diagnosis/measurements
├─ Web dashboard with live plots
├─ Embed interactive DAG visualization
└─ User testing with operators

WEEK 4: Data Persistence
├─ Set up time-series database
├─ Store measurements and diagnoses
├─ Build historical query API
└─ Incident analysis tools
```

---

## MVP Feature Set

### What's Included
✓ Real-time diagnosis (every 10 seconds)  
✓ Root cause identification with confidence  
✓ Alert on new faults detected  
✓ Interactive DAG visualization  
✓ Live telemetry plots  
✓ Diagnosis history (rolling 7 days)  

### What's NOT Included (Yet)
✗ Automated corrective actions  
✗ Multi-satellite support  
✗ Predictive alerts (degradation trending)  
✗ Integration with command system  
✗ ML-based edge weight tuning  

---

## Success Criteria

| Goal | Metric |
|------|--------|
| **Correct diagnosis** | Identifies solar_degradation in synthetic scenario within 2 minutes |
| **No false alarms** | < 5% false positive rate on nominal operation |
| **Fast alerts** | Operators notified within 30 seconds of fault detection |
| **Understandable** | Operators can explain diagnosis using DAG visualization |
| **Reliable** | 99.9% uptime on service (handles restarts gracefully) |
| **Scalable** | Can handle 1+ Hz telemetry sampling rate |

---

## Integration with Real Mission Control

### When Ready for Real Satellite
1. **Data Format Adaptation Layer**
   - Parse actual ISRO/customer telemetry format
   - Map measurements to node names
   - Handle compression/encryption if needed

2. **Deployment Architecture**
   - Docker container for inference service
   - Kubernetes deployment (if scaling needed)
   - Fallback to SSH/manual if container unavailable

3. **Operator Training**
   - 1-hour briefing on causal framework
   - 30-minute hands-on with visualization
   - 1 week of observation (parallel with current system)
   - Go-live decision by mission lead

4. **Integration Testing**
   - Historical replay: run Pravaha on past telemetry
   - Compare: Pravaha diagnosis vs. what actually happened
   - Quantify: lead time advantage vs. threshold-based alerts

---

## Tools & Technologies

| Component | Stack |
|-----------|-------|
| Telemetry Sim | Python (numpy, pandas) |
| Inference | Python (existing) |
| API | Flask or FastAPI |
| Dashboard | HTML/CSS/JS + Plotly |
| Database | PostgreSQL or InfluxDB |
| Deployment | Docker + Docker Compose |

---

## Files to Create

```
pravaha/
├─ operational/
│  ├─ telemetry_simulator.py      (Phase 1)
│  ├─ scenarios/
│  │  ├─ nominal.py
│  │  ├─ solar_degradation.py
│  │  └─ ...
│  ├─ telemetry_buffer.py         (Phase 2)
│  ├─ inference_service.py        (Phase 2)
│  ├─ alert_system.py             (Phase 2)
│  ├─ api.py                      (Phase 3)
│  ├─ dashboard.html              (Phase 3)
│  ├─ database.py                 (Phase 4)
│  └─ queries.py                  (Phase 4)
├─ docker-compose.yml              (deployment)
└─ deployment/
   ├─ Dockerfile
   ├─ requirements.txt
   └─ startup.sh
```

---

## Next Steps

**Immediate:**
1. Create telemetry simulator with solar degradation scenario
2. Verify Pravaha diagnoses it correctly (should find 100% solar_degradation)
3. Create measurement buffer and inference service
4. Run 1-hour simulation end-to-end

**By End of Week 1:**
- Working telemetry simulator
- Inference service running continuously
- Alerts being generated
- Data flowing correctly

---

## Rust Integration (Deferred)

Once this operational pipeline is working:
- Replace Python inference with Rust via FFI (10x speedup)
- Add EKF for better state estimation
- Compile to WASM for browser diagnostics

But this is **optimization**, not **required** for operations.

---

**Status:** Ready to begin Phase 1  
**Owner:** [Your team]  
**Timeline:** 2-4 weeks to MVP  
**Goal:** Get Pravaha running on real satellite by Q1 2026
