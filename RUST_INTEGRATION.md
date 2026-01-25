# Rust Integration with Pravaha Framework

## Architecture

```
Python Framework (causal_graph, gsat6a)
         ↓
    Detects dropout in telemetry
         ↓
    Calls Rust binary (pravaha_core)
         ↓
Rust: Kalman Filter + Hidden State Inference
         ↓
    Returns JSON: hidden state estimates
         ↓
    Python updates causal inference
         ↓
    Diagnosis with confidence adjustment
```

## When Rust is Invoked

1. **Telemetry Gap Detected**: Consecutive samples missing for 5+ seconds
2. **Call Rust Core**: With gap duration and load power
3. **Get Predictions**: Kalman Filter fills missing samples
4. **Update Graph**: Hidden states constrain causal inference
5. **Resume Inference**: When telemetry resumes, Kalman update corrects predictions

## Usage Example

In `gsat6a/live_simulation.py`:

```python
from causal_graph.kalman_integration import DropoutHandler

# Initialize once
dropout_handler = DropoutHandler()

# In analysis loop
def analyze_telemetry_window(telemetry, sample_indices):
    # Detect gaps
    gaps = dropout_handler.detect_gaps(sample_indices)
    
    if gaps:
        # Get Rust predictions for missing samples
        hidden_states = dropout_handler.fill_gaps(
            gaps=gaps,
            load_power=300.0
        )
        
        # Use in causal inference
        ranker = RootCauseRanker()
        diagnosis = ranker.analyze_with_hidden_states(
            telemetry_dict=telemetry,
            hidden_state_estimates=hidden_states,
            confidence_adjustment=dropout_handler.confidence_degradation
        )
        
        return diagnosis
```

## Building the Rust Core

From project root:

```bash
# Build debug
cd rust_core && cargo build

# Build optimized release
cd rust_core && cargo build --release

# Run tests
cd rust_core && cargo test

# Run demo
./rust_core/target/release/pravaha_core
```

## Output Format

Rust binary outputs JSON on stdout:

```json
{
  "gap_duration_samples": 5,
  "confidence_factor": 0.78,
  "hidden_states": {
    "battery_state": {
      "estimated_value": 0.919,
      "lower_bound": 0.875,
      "upper_bound": 0.963,
      "confidence": 0.78
    },
    "solar_input": {
      "estimated_value": 361.568,
      "lower_bound": 335.866,
      "upper_bound": 387.270,
      "confidence": 0.23
    },
    "battery_efficiency": {
      "estimated_value": 1.0,
      "lower_bound": 0.95,
      "upper_bound": 1.0,
      "confidence": 0.23
    }
  },
  "filled_samples": [
    {"sample": 50, "charge": 80.6, "voltage": 26.91, "solar": 350.0},
    {"sample": 51, "charge": 81.1, "voltage": 26.94, "solar": 350.0},
    ...
  ]
}
```

## FFI Future Work

For tighter integration without subprocess calls:

```python
# PyO3 bindings (future)
from pravaha_core import PowerSystemKalmanFilter, infer_hidden_states

kf = PowerSystemKalmanFilter(nominal_voltage=28.0, nominal_capacity=50.0)
predictions = infer_hidden_states(kf, gap_duration=5, load_power=300.0)
```

## Performance

- Kalman prediction: ~1ms per sample (negligible)
- Subprocess overhead: ~50ms startup
- Total for 5-sample dropout: <100ms

For real-time use with frequent dropouts, FFI bindings recommended.

## Safety & Correctness

✓ Type-safe matrix operations (nalgebra)
✓ Bounds checking on all physical quantities
✓ Covariance matrices guaranteed positive-definite
✓ Numerical stability through symmetric updates
✓ Deterministic (seeded) for reproducible tests
