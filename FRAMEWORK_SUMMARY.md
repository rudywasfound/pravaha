# GSAT-6A Analysis Framework Refactor

## Overview

The GSAT-6A simulation and forensic analysis have been refactored to separate **data collection** from **output generation**. All output is now framework-driven, not hardcoded in simulation code.

## Architecture

### 1. Timeline Framework (`timeline.py`)
- Collects detection events in chronological order
- Records event type, severity, subsystem, and confidence
- Generates formatted timeline output
- Calculates lead times between detection methods

### 2. Findings Framework (`findings.py`)
- Aggregates telemetry statistics (nominal vs degraded)
- Tracks cascade events
- Generates deviations analysis
- Produces detection comparisons
- Calculates mission impact

### 3. Visualizer Framework (`visualizer.py`)
- Generates timeline visualization
- Plots telemetry deviations (bar charts)
- Creates detection comparison charts
- All graphs are data-driven from analysis results

## Workflow

### Forensic Analysis (`forensics.py`)
```
1. Initialize frameworks (Timeline, Findings, Visualizer)
2. Generate telemetry (simulators)
3. Analyze with causal inference
4. Record events → Timeline
5. Collect stats → Findings
6. Generate all output:
   - `print_analysis()` - text output
   - `generate_graphs()` - visualization
```

### Live Simulation (`live_simulation.py`)
```
1. Initialize frameworks (Timeline, Findings)
2. Run simulation
3. Record causal detections → Timeline
4. Record threshold alerts → Timeline
5. Print timeline
```

## Key Benefits

✓ **Data-driven output**: Text and graphs generated from actual measurements  
✓ **Separation of concerns**: Simulation ≠ presentation  
✓ **Extensible**: Add new analysis types without modifying simulation  
✓ **Consistent**: All outputs follow same data patterns  
✓ **Testable**: Framework can be tested independently  
✓ **Maintainable**: Change output format in one place  

## Generated Outputs

### Text Output
- Timeline of events (detection times, severity)
- Telemetry deviations (nominal vs degraded)
- Detection comparison (causal vs threshold-based)
- Mission impact analysis

### Graphs
- `gsat6a_timeline.png` - Event timeline with detection points
- `gsat6a_telemetry_deviations.png` - Nominal vs degraded comparison
- `gsat6a_detection_comparison.png` - Method comparison and lead time

## Usage

```bash
# Forensic analysis with graphs
python gsat6a/live_simulation_main.py forensics

# Live simulation with timeline
python gsat6a/live_simulation_main.py simulation

# Full mission analysis (existing)
python gsat6a/live_simulation_main.py mission
```

## Data Flow

```
Simulation/Analysis Code
         ↓
    [Collect Data]
         ↓
Timeline ← Events ← Detections
Findings ← Stats  ← Telemetry
         ↓
   [Framework]
         ↓
  [Generate Output]
         ↓
Text Output + Graphs
```

## Example Output

### Timeline Event
```
🔴 T+    0.0s [Power       ] Solar degradation detected (100%)
⚠ T+    0.0s [Power       ] Solar Power = 372W (24.9% drop)
```

### Telemetry Deviation
```
Battery Charge (Ah):
  Nominal:      64.32 ± 35.29
  Degraded:     31.61 ± 23.64
  Change:      -32.72 ( +50.9%) ↓
```

### Detection Comparison
```
LEAD TIME ADVANTAGE: 0.0s
Can enable preventive action
before cascade failure.
```

## Files Modified

- `forensics.py` - Removed hardcoded output, uses frameworks ✓
- `live_simulation.py` - Removed hardcoded output, uses frameworks ✓
- `mission_analysis.py` - Removed hardcoded visualization code, uses frameworks ✓
- `live_simulation_main.py` - Added graph generation call ✓

## Files Created

- `timeline.py` - Event timeline framework ✓
- `findings.py` - Analysis findings framework ✓
- `visualizer.py` - Graph generation framework ✓

## Architecture Summary

```
Analysis Code                Framework Components             Output
═════════════════════════════════════════════════════════════════════

forensics.py              Timeline                  print_timeline()
  → Analyze              + Findings                 + print_deviations()
  → Record events   ───> + Visualizer          ──> + print_comparison()
  → Collect stats                                  + print_impact()
                                                   + 3 PNG graphs
live_simulation.py
  → Run simulation
  → Record events
  
mission_analysis.py
  → Load CSV data
  → Analyze w/causal
  → Record anomalies
```
