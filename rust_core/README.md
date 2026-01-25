# Pravaha Rust Core: Kalman Filter + Hidden State Inference

High-performance Rust implementation of telemetry dropout handling for satellite diagnostics.

## Purpose

When satellites lose connection for 5+ seconds, observable telemetry measurements stop flowing. The Rust core maintains state estimates of hidden (unobservable) satellite conditions using:

1. **Kalman Filter** - Predicts power system state forward with physics-based dynamics
2. **Hidden State Inference** - Maps predictions to causal graph intermediate nodes
3. **Confidence Degradation** - Tracks uncertainty as dropout extends

## Building

```bash
cd rust_core
cargo build --release
```

## Integration

The Rust core is invoked from Python's causal graph inference pipeline:

```python
# From Python (gsat6a/live_simulation.py or causal_graph/root_cause_ranking.py)
import subprocess
import json

# Detect dropout in telemetry
if dropout_detected(sample_indices):
    # Call Rust binary with telemetry gap info
    result = subprocess.run(
        ["./rust_core/target/release/pravaha_core", 
         f"--gap-start={gap_start}",
         f"--gap-end={gap_end}",
         f"--load-power=300.0"],
        capture_output=True,
        text=True
    )
    
    # Parse hidden state estimates from JSON output
    hidden_states = json.loads(result.stdout)
    
    # Use estimates in causal inference
    ranker.update_with_hidden_states(hidden_states)
```

## Module Structure

- **kalman_filter.rs** - Core Kalman Filter implementation
  - `PowerSystemKalmanFilter` - Predicts charge, voltage, solar, efficiency
  - `TelemetryDropoutHandler` - Detects gaps and fills with predictions
  - State transitions use physics model from `simulator/power.py`

- **hidden_state_inference.rs** - Causal graph integration
  - `HiddenStateInferenceEngine` - Maps Kalman outputs to graph nodes
  - `HiddenStateEstimate` - Represents estimated intermediate states
  - `DropoutAwareInference` - Wrapper for complete dropout handling

## Running

Standalone demo:
```bash
cd rust_core
cargo run --release
```

Expected output:
```
✓ Rust core handles 5+ second telemetry dropout with:
  • Kalman Filter state prediction
  • Hidden state inference from causal graph
  • Confidence degradation based on uncertainty
  • Measurement update upon connection resume
```

## Physics Model

The Kalman Filter uses physics equations from the power simulator:

**Power Balance:**
```
dQ/dt = (P_solar * efficiency - P_load) / (capacity * 3600) * 100
```

**Voltage Model:**
```
V = V_nominal * (0.8 + 0.2 * SOC)
```

where SOC (State of Charge) = battery_charge / 100

## Type Safety

- All physical quantities have valid ranges (battery charge 20-100%, voltage 20-32V, etc.)
- Matrix operations use `nalgebra` for numerical stability
- Covariance matrices stay positive-definite through symmetric updates

## Testing

```bash
cd rust_core
cargo test
```

## Future Enhancements

- [ ] FFI bindings for Python (ctypes or PyO3)
- [ ] Real-time telemetry stream processing
- [ ] Extended Kalman Filter (EKF) for nonlinear dynamics
- [ ] WASM compilation for browser-based diagnostics
