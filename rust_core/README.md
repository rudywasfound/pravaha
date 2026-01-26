# Satellite Telemetry State Estimation Framework (Rust)

High-performance Rust framework for real-time satellite state estimation, telemetry stream processing, and physics-based inference during communication dropouts.

## Purpose

Standalone Rust framework for real-time satellite state estimation and telemetry processing.

**Capabilities:**
- Physics-based Kalman filtering (state prediction)
- Estimate hidden states during communication dropouts
- Real-time streaming (1+ Hz satellite data)
- Multi-language bindings: Python (PyO3), C (cbindgen), JavaScript (WASM)

## Building

```bash
cd rust_core
cargo build --release
```

## Integration Points

### 1. As Python Extension (Fastest)
```python
import pravaha_core

# Create filter
kf = pravaha_core.KalmanFilter(dt=1.0)

# Process measurements
measurement = pravaha_core.Measurement()
measurement.battery_voltage = 28.5
measurement.battery_charge = 95.0
# ... set other fields

kf.update(measurement)
estimate = kf.get_estimate()  # JSON string
```

### 2. As CLI Tool
```bash
# Process telemetry stream
cat telemetry.jsonl | ./target/release/pravaha_core | jq '.confidence'
```

### 3. As Rust Library (Zero-copy)
```rust
use pravaha_core::{KalmanFilter, Measurement};

let mut kf = KalmanFilter::new(1.0);
let measurement = Measurement::new(Utc::now());
kf.update(&measurement)?;
let estimate = kf.get_estimate();
```

### 4. As JavaScript/WASM (Browser)
```javascript
// Compiled to WASM, runs in browser
const estimate = Module.process_measurement(measurement);
```

## Components

| Module | Purpose |
|--------|---------|
| `kalman.rs` | Linear & Extended Kalman Filters |
| `physics.rs` | Power & thermal physics models |
| `measurement.rs` | Telemetry types & validation |
| `state_estimate.rs` | State output & confidence |
| `dropout_handler.rs` | Detect & predict through gaps |
| `python_bindings.rs` | PyO3 bindings for Python |
| `bin/main.rs` | CLI tool |

## Running

### As CLI Tool
```bash
# Process JSON telemetry line-by-line
echo '{"battery_voltage": 28.5, "battery_charge": 95.0, "battery_temp": 35.0, ...}' | \
  ./target/release/pravaha_core

# Real-time stream
cat satellite_telemetry.jsonl | ./target/release/pravaha_core > estimates.jsonl
```

### As Python Module
```python
from operational.telemetry_simulator import TelemetrySimulator
import pravaha_core

sim = TelemetrySimulator("solar_degradation")
kf = pravaha_core.KalmanFilter(dt=1.0)

for measurement in sim.generate_series(3600):
    # Convert to PyMeasurement
    py_meas = pravaha_core.Measurement()
    py_meas.set_battery_voltage(measurement.battery_voltage_measured)
    # ... set all fields
    
    kf.update(py_meas)
    estimate_json = kf.get_estimate()
    print(estimate_json)
```

## Physics Implementation

**Power System Dynamics:**
```
dSOC/dt = (I_charge - I_discharge) / capacity
V(t) = V_nominal * (0.8 + 0.2 * SOC(t))
I_discharge(t) = P_load(t) / V(t)
```

**Thermal System:**
```
Q_rad = σ * A * ε * (T^4 - T_space^4)
dT/dt = (Q_in - Q_rad) / (m * c)
```

## Type Safety & Validation

✓ All measurements validated against ranges
✓ Matrix operations use `nalgebra` (numerical stability)
✓ Covariance matrices stay positive-definite
✓ Confidence scores prevent divergence
✓ Zero-copy Rust for performance

## Testing

```bash
cd rust_core

# Run all tests
cargo test

# Run with logging
RUST_LOG=debug cargo test -- --nocapture

# Benchmark
cargo bench
```

## Status

**Completed:**
- [x] Kalman Filter
- [x] Physics models (power + thermal)
- [x] Dropout handling
- [x] Python bindings (PyO3)
- [x] CLI tool

**Planned:**
- [ ] Async tokio support
- [ ] Particle filters
- [ ] Custom physics models
- [ ] Extended Kalman Filter (nonlinear)
- [ ] WASM compilation