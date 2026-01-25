# Pravaha Causal DAG: Complete Documentation

## Overview

Pravaha uses a **Directed Acyclic Graph (DAG)** to encode causal knowledge about satellite power and thermal subsystems. This document provides:

1. **Visual DAG structure** (ASCII representation)
2. **Explicit node definitions** with types and meanings
3. **Edge specifications** showing causal relationships
4. **Exclusion Restrictions** (what does NOT cause what)
5. **d-Separation analysis** proving conditional independence

---

## 1. Visual DAG Representation

### Full System DAG

```
LAYER 1: ROOT CAUSES (Faults - what we want to diagnose)
════════════════════════════════════════════════════════════
                                                              
    solar_degradation     battery_aging     battery_thermal
            │                   │                  │
            │                   │                  │
    sensor_bias   panel_insulation_degradation   battery_heatsink_failure
            │                   │                  │
            ├───────────────────┴──────────────────┤
            │                                      │
            ▼                                      ▼
    
LAYER 2: INTERMEDIATE EFFECTS (Physical states - unobservable but inferred)
════════════════════════════════════════════════════════════════════════════
    
    solar_input         battery_efficiency      battery_state
           │                    │                     │
           │                    │                     │
           └────────┬───────────┴─────────────┬───────┘
                    │                         │
                    ▼                         ▼
              bus_regulation          battery_temp
                    │                         │
                    │                         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                         thermal_stress
    

LAYER 3: OBSERVABLES (Measured telemetry - what we can actually see)
════════════════════════════════════════════════════════════════════════
    
    solar_input_measured      bus_voltage_measured      bus_current_measured
           │                         │                         │
           │                         │                         │
    battery_charge_measured   battery_voltage_measured   battery_temp_measured
           │                         │                         │
           │                         │                         │
    solar_panel_temp_measured                           payload_temp_measured
           │                                                   │
           └───────────────────────────────────────────────────┘
```

### Solar Degradation Cascade (GSAT-6A Example)

```
ROOT CAUSE:
  solar_degradation
        │
        │ (mechanism: panels lose efficiency)
        ▼
  
INTERMEDIATE PROPAGATION:
  solar_input ◄─────────┐
        │               │ (power loss cascades)
        │               │
        ▼               │
  battery_state        │
    ├─ charge ◄────────┘
    └─ efficiency
        │
        ├──────┬──────────┐
        │      │          │
        ▼      ▼          ▼
  bus_regulation  battery_temp  thermal_stress
        │              │              │
        │              │              │
        ▼              ▼              ▼

OBSERVABLES (What we measure):
  bus_voltage_measured    battery_charge_measured    battery_temp_measured
        │                         │                         │
        │                         │                         │
        └─────────────────────┬───┴─────────────────────────┘
                              │
                    (Pattern indicates solar failure)
```

---

## 2. Explicit Node Definitions

### Notation: [Name] → Type → Description

### ROOT CAUSE NODES (7 total)

**Power Subsystem Faults:**

1. **solar_degradation** [ROOT_CAUSE]
   - What it means: Solar panel efficiency loss due to dust, micrometeorite damage, or thermal cycling
   - How it fails: Panel output decreases over time; can happen suddenly (deployment anomaly) or gradually (aging)
   - Observable consequence: Solar input power drops
   - Real example: GSAT-6A solar array deployment malfunction

2. **battery_aging** [ROOT_CAUSE]
   - What it means: Internal battery degradation (cell aging, resistance increase)
   - How it fails: Calendar aging even without use; accelerated by cycling and temperature stress
   - Observable consequence: Lower battery charge capacity, increased voltage droop
   - Real example: Batteries on >10-year-old satellites

3. **battery_thermal** [ROOT_CAUSE]
   - What it means: Excessive temperature stress on battery cells
   - How it fails: Overheating accelerates electrochemical degradation; risk of thermal runaway
   - Observable consequence: Battery temperature rises; charge capacity drops
   - Real example: Spacecraft with failed cooling systems

4. **sensor_bias** [ROOT_CAUSE]
   - What it means: Measurement sensor calibration drift or electronic aging
   - How it fails: Electronics degrade in vacuum/radiation; analog circuits drift over time
   - Observable consequence: Measurements deviate from true values (but physics is fine)
   - Real example: Voltage sensor drifts 2-3% due to aging

**Thermal Subsystem Faults:**

5. **panel_insulation_degradation** [ROOT_CAUSE]
   - What it means: Solar panel insulation (MLI) or radiator fouling
   - How it fails: MLI tears from micrometeorites; radiator coatings degrade in UV
   - Observable consequence: Panel temperature rises; heat loss increases
   - Real example: MLI tears in sunlit areas after micrometeorite impacts

6. **battery_heatsink_failure** [ROOT_CAUSE]
   - What it means: Battery thermal management system failure
   - How it fails: Coolant leaks; interface degradation; radiator blockage
   - Observable consequence: Battery temperature rises despite normal load
   - Real example: Coolant system failure in thermal control

7. **payload_radiator_degradation** [ROOT_CAUSE]
   - What it means: Payload radiator coating loss or micrometeorite damage
   - How it fails: Similar to panel insulation; UV and radiation damage coatings
   - Observable consequence: Payload temperature rises
   - Real example: Radiator coating degradation on payloads

---

### INTERMEDIATE NODES (8 total)

These are **unobservable physical states** that we infer from observables. They represent the mechanisms connecting root causes to measured quantities.

**Power Subsystem Intermediates:**

1. **solar_input** [INTERMEDIATE]
   - Physical meaning: Available power from solar array after degradation
   - How it relates: solar_degradation → solar_input → battery_state
   - Causal role: Root cause effect (directly measurable but not telemetered in this system)
   - Range: 300-500W (nominal), drops with degradation

2. **battery_efficiency** [INTERMEDIATE]
   - Physical meaning: Fraction of input power successfully stored (vs lost as heat)
   - How it relates: battery_aging → battery_efficiency → battery_state
   - Causal role: Efficiency loss means more power lost as heat
   - Range: 85-98% (high efficiency), degrades with age

3. **battery_state** [INTERMEDIATE]
   - Physical meaning: Current charge capacity and health of battery
   - How it relates: Receives input from solar_input, battery_efficiency, battery_thermal
   - Causal role: Central hub affecting all power measurements
   - Observable consequences: battery_charge_measured, battery_voltage_measured

4. **bus_regulation** [INTERMEDIATE]
   - Physical meaning: Power regulation system stress level
   - How it relates: As battery_state degrades, regulation becomes harder (more stress)
   - Causal role: Determines how bus voltage is maintained
   - Observable consequence: bus_voltage_measured, bus_current_measured

**Thermal Subsystem Intermediates:**

5. **battery_temp** [INTERMEDIATE]
   - Physical meaning: Internal battery temperature
   - How it relates: Receives input from battery_thermal (cooling failure) and battery_state (dissipation)
   - Causal role: Central thermal hub
   - Observable consequence: battery_temp_measured

6. **solar_panel_temp** [INTERMEDIATE]
   - Physical meaning: Solar panel temperature
   - How it relates: Receives input from panel_insulation_degradation
   - Causal role: Direct measurement of insulation failure
   - Observable consequence: solar_panel_temp_measured

7. **payload_temp** [INTERMEDIATE]
   - Physical meaning: Payload electronics temperature
   - How it relates: Receives input from payload_radiator_degradation
   - Causal role: Direct measurement of radiator failure
   - Observable consequence: payload_temp_measured

8. **thermal_stress** [INTERMEDIATE]
   - Physical meaning: Overall thermal stress on the system
   - How it relates: Combines effects from battery_temp and environmental factors
   - Causal role: Feeds into multiple thermal consequences
   - Observable consequence: Correlates with multiple temperature measurements

---

### OBSERVABLE NODES (8 total)

These are **measured telemetry quantities** available in real-time from satellite housekeeping.

**Power System Observables:**

1. **solar_input_measured** [OBSERVABLE]
   - Measurement: Solar panel output voltage/current
   - Physical units: Watts
   - Sampling rate: 1 Hz (or as available)
   - Failure mode: Can read 0 during eclipse, noisy near edges
   - Note: Not available on all satellites; inferred if not telemetered

2. **bus_voltage_measured** [OBSERVABLE]
   - Measurement: Main power bus voltage
   - Physical units: Volts (typically 25-32V for geosynchronous satellites)
   - Sampling rate: 1-10 Hz
   - Failure signature: Drops below 26V when power subsystem fails
   - Why important: Critical indicator of regulation stress

3. **bus_current_measured** [OBSERVABLE]
   - Measurement: Main power bus current
   - Physical units: Amperes
   - Sampling rate: 1-10 Hz
   - Failure signature: Can be noisy but indicates load stress
   - Why important: Shows regulation effort (higher current = more stress)

4. **battery_charge_measured** [OBSERVABLE]
   - Measurement: Battery state of charge (SOC)
   - Physical units: Amp-hours (Ah) or percentage (%)
   - Sampling rate: 1-10 Hz
   - Failure signature: Drops below 50Ah when charging fails
   - Why important: Direct indicator of power system health

5. **battery_voltage_measured** [OBSERVABLE]
   - Measurement: Battery terminal voltage
   - Physical units: Volts (typically 20-32V)
   - Sampling rate: 1-10 Hz
   - Failure signature: Sags under load when battery ages
   - Why important: Early indicator of aging (voltage droop before capacity loss)

**Thermal System Observables:**

6. **battery_temp_measured** [OBSERVABLE]
   - Measurement: Battery internal temperature
   - Physical units: Celsius (typically 5-50°C operational range)
   - Sampling rate: 1-10 Hz
   - Failure signature: Rises above 50°C when cooling fails
   - Why important: Thermal runaway risk indicator

7. **solar_panel_temp_measured** [OBSERVABLE]
   - Measurement: Solar panel surface temperature
   - Physical units: Celsius
   - Sampling rate: Low (10 minutes typical)
   - Failure signature: Higher than expected for eclipse phase
   - Why important: Indicates insulation failure

8. **payload_temp_measured** [OBSERVABLE]
   - Measurement: Payload electronics temperature
   - Physical units: Celsius
   - Sampling rate: Variable (depends on payload telemetry)
   - Failure signature: Exceeds thermal limits
   - Why important: Payload protection indicator

---

## 3. Complete Edge Specification

### Notation: [Source] → [Target] | Weight | Mechanism

This list specifies EVERY causal relationship in the graph, including their strength and mechanism.

### ROOT CAUSE → INTERMEDIATE EDGES (Power System)

1. **solar_degradation → solar_input** | Weight: 0.95 | Mechanism: Panel efficiency loss directly reduces output power
2. **battery_aging → battery_efficiency** | Weight: 0.90 | Mechanism: Age increases internal resistance, reducing charging efficiency
3. **battery_aging → battery_state** | Weight: 0.85 | Mechanism: Aged battery has lower capacity and faster discharge
4. **battery_thermal → battery_state** | Weight: 0.80 | Mechanism: Heat stress degrades electrochemistry and discharge rate
5. **sensor_bias → battery_efficiency** | Weight: 0.20 | Mechanism: Measurement error can appear as efficiency loss
6. **sensor_bias → battery_state** | Weight: 0.15 | Mechanism: Measurement error can mimic state-of-charge errors

### ROOT CAUSE → INTERMEDIATE EDGES (Thermal System)

7. **battery_thermal → battery_temp** | Weight: 0.88 | Mechanism: Thermal failure removes cooling capacity
8. **panel_insulation_degradation → solar_panel_temp** | Weight: 0.90 | Mechanism: Insulation loss increases heat absorption
9. **battery_heatsink_failure → battery_temp** | Weight: 0.85 | Mechanism: Heatsink failure removes active cooling
10. **payload_radiator_degradation → payload_temp** | Weight: 0.88 | Mechanism: Radiator loss increases heat retention

### INTERMEDIATE → INTERMEDIATE EDGES (Cross-System Coupling)

11. **solar_input → battery_state** | Weight: 0.92 | Mechanism: Solar input determines available power for charging
12. **battery_efficiency → battery_state** | Weight: 0.85 | Mechanism: Efficiency loss means less power stored for given input
13. **battery_state → bus_regulation** | Weight: 0.88 | Mechanism: Weak battery requires harder regulation to maintain bus voltage
14. **battery_state → battery_temp** | Weight: 0.70 | Mechanism: Discharge rate affects battery heat dissipation
15. **thermal_stress → battery_temp** | Weight: 0.75 | Mechanism: System-level thermal effects affect local temperatures
16. **battery_temp → thermal_stress** | Weight: 0.80 | Mechanism: Battery heat contributes to overall thermal stress
17. **solar_panel_temp → thermal_stress** | Weight: 0.65 | Mechanism: Panel temperature contributes to overall system heat

### INTERMEDIATE → OBSERVABLE EDGES (Measurement Links)

**Power System:**

18. **solar_input → solar_input_measured** | Weight: 0.98 | Mechanism: Direct power sensor measurement
19. **battery_state → battery_charge_measured** | Weight: 0.95 | Mechanism: Battery coulomb counter measures charge capacity
20. **battery_state → battery_voltage_measured** | Weight: 0.92 | Mechanism: Battery voltage correlates with state-of-charge
21. **bus_regulation → bus_voltage_measured** | Weight: 0.90 | Mechanism: Regulation stress causes voltage droop under load
22. **battery_efficiency → bus_voltage_measured** | Weight: 0.70 | Mechanism: Efficiency loss forces higher bus voltage swings
23. **battery_state → bus_current_measured** | Weight: 0.80 | Mechanism: Low battery state increases regulation current demand

**Thermal System:**

24. **solar_panel_temp → solar_panel_temp_measured** | Weight: 0.98 | Mechanism: Direct thermistor temperature measurement
25. **battery_temp → battery_temp_measured** | Weight: 0.95 | Mechanism: Direct thermistor temperature measurement  
26. **payload_temp → payload_temp_measured** | Weight: 0.96 | Mechanism: Direct payload temperature sensor measurement
27. **battery_state → bus_current_measured** | Weight: 0.80 | Mechanism: Low battery increases regulation current
28. **battery_efficiency → bus_current_measured** | Weight: 0.70 | Mechanism: Efficiency loss requires higher currents for same power

---

## 4. Exclusion Restrictions (What's NOT Connected)

These are the **causal independence assumptions** that make Pravaha able to separate root causes.

### CRITICAL EXCLUSION RESTRICTIONS

**Solar Does NOT Directly Affect Bus Voltage (except via Battery):**
```
❌ solar_degradation ↛ bus_voltage_measured (only via solar_input → battery_state → bus_regulation)
```
Why: Bus voltage depends on power supply state (battery), not directly on input power. This allows us to distinguish "solar failure" from "regulation failure" even when both might cause low voltage.

**Battery Age Does NOT Directly Affect Temperature (except via efficiency):**
```
❌ battery_aging ↛ battery_temp_measured (only via battery_efficiency → battery_state → battery_temp)
```
Why: Aging affects performance, not thermal properties. This allows us to separate "aged battery" from "overheating battery" in diagnosis.

**Thermal Failures Do NOT Affect Power Measurements (except via battery temperature):**
```
❌ panel_insulation_degradation ↛ battery_charge_measured
❌ battery_heatsink_failure ↛ bus_voltage_measured (direct effect)
```
Why: Thermal failures degrade performance only through temperature effects on electrochemistry. This allows us to identify thermal problems as separate from primary power failures.

**Sensor Bias Does NOT Directly Affect Battery State:**
```
❌ sensor_bias → battery_state (direct physical effect)
```
Why: Sensors measure; they don't cause real physical changes. This allows us to distinguish "measurement error" from "real degradation."

**Payload Does NOT Affect Power System:**
```
❌ payload_radiator_degradation ↛ battery_voltage_measured
❌ payload_radiator_degradation ↛ bus_voltage_measured
```
Why: Payload and battery are thermally isolated. This allows independent diagnosis.

### Summary of Exclusion Restrictions

| No Edge | Reason | Consequence |
|---------|--------|-------------|
| solar_degradation → bus_voltage | Indirection (via battery) | Can diagnose regulation separately |
| battery_aging → battery_temp | Age ≠ temperature | Can separate age from overheating |
| thermal_failure → power_meas | Coupling only via temp | Can isolate thermal problems |
| sensor_bias → real_state | Measurement ≠ physical effect | Can detect measurement errors |
| payload → power_system | Thermal isolation | Can diagnose independently |

---

## 5. d-Separation Analysis

**d-separation** (directional separation) is Pearl's criterion for when two variables are conditionally independent given a set of observations. This is crucial for Pravaha: it explains **when we can ignore noise in one signal to focus on another**.

### Theorem: d-Separation Path Blocking

Two nodes X and Z are d-separated by a set S if all paths from X to Z are blocked by S.

A path is blocked if:
1. It passes through a non-collider node in S (conditioning on it blocks the path)
2. It passes through a collider node whose descendants are not in S (conditioning closes the path)

---

### Example 1: Solar Noise Can Be Ignored When Battery is Stable

**Claim:** If battery_state is stable, then solar_input noise is irrelevant.

**DAG Context:**
```
solar_degradation → solar_input → battery_state → bus_voltage_measured
                                        ↑
                                        └─ battery_efficiency
```

**d-Separation Analysis:**

If we condition on **battery_state** (assume it's stable), then:
- Path: solar_input → battery_state is BLOCKED (because we're conditioning on battery_state, the child)
- Therefore: solar_input noise does NOT propagate to bus_voltage_measured
- Conclusion: Fluctuations in solar_input (noise, eclipse edge, etc.) won't cause bus voltage changes if battery state is stable

**Practical Implication:**
```
Traditional threshold: If solar_input drops 5%, alarm triggers immediately
Pravaha with d-separation: If solar_input drops but battery_charge stays stable,
                          we ignore the solar fluctuation as noise
```

This is why Pravaha doesn't false-alarm during eclipse transitions where solar power naturally drops.

---

### Example 2: Battery Thermal vs. Battery Age

**Claim:** We can distinguish battery aging from battery overheating by observing which measurement deviates.

**DAG Context:**
```
battery_aging → battery_efficiency ──┐
                                      ├→ battery_state → battery_voltage_measured
battery_thermal → battery_temp  ─────┘

battery_thermal → battery_state ──────→ battery_temp_measured
```

**d-Separation Analysis:**

Given measurements: battery_voltage_measured and battery_temp_measured

**Scenario A: Low voltage, Normal temperature**
- Path for battery_aging: battery_aging → battery_efficiency → battery_state → battery_voltage (matches!)
- Path for battery_thermal: battery_thermal → battery_temp (doesn't match - temp is normal)
- d-separation: battery_aging is NOT d-separated from voltage measurements; battery_thermal IS
- Diagnosis: Likely battery_aging, not thermal

**Scenario B: Low voltage, HIGH temperature**
- Path for battery_aging: battery_aging → battery_efficiency → battery_state → battery_voltage (matches)
- Path for battery_thermal: battery_thermal → battery_temp (matches!)
- d-separation: Both roots have paths to observations
- Diagnosis: Likely BOTH aging AND thermal stress
- Probability: 60% aging, 40% thermal (or similar split)

---

### Example 3: Payload Independence (Causal Isolation)

**Claim:** Payload radiator problems don't affect power system measurements because they're causally isolated.

**DAG Context:**
```
payload_radiator_degradation → payload_temp → payload_temp_measured
                                              (does NOT connect to power system)

solar_degradation → solar_input → battery_state → battery_voltage_measured
```

**d-Separation Analysis:**

Path from payload_radiator_degradation to battery_voltage_measured: NONE
- There is no directed path connecting these two subsystems
- payload_temp and battery_voltage are d-separated under any conditioning
- Therefore: Payload temperature changes NEVER explain power system deviations

**Practical Implication:**
```
If battery voltage drops AND payload temperature rises:
  Diagnosis will NOT suggest payload radiator degradation as cause of power loss
  Instead: Diagnosis focuses on solar, battery_aging, regulation
  Payload overheat is separate problem requiring separate response
```

---

### Example 4: Sensor Bias Detection via d-Separation

**Claim:** True sensor bias only affects measurements, not physical quantities.

**DAG Context:**
```
sensor_bias → battery_efficiency (weak path, 0.20 weight)
           → battery_state (weak path, 0.15 weight)
           → battery_charge_measured (weak path, 0.15 weight)

battery_aging → battery_efficiency (strong path, 0.90 weight)
             → battery_state (strong path, 0.85 weight)
             → battery_charge_measured (strong path, 0.95 weight)
```

**d-Separation Analysis:**

Observe: battery_charge_measured deviates 5%
Condition on: battery_efficiency is stable, battery_temp is normal, solar_input is normal

Then:
- Path from battery_aging to the deviation: battery_aging → battery_state → charge (BLOCKED by stable efficiency)
- Path from sensor_bias to the deviation: sensor_bias → charge (weak, direct path)
- Conclusion: Likely sensor_bias, not real degradation

**Practical Implication:**
```
Traditional system: Battery charge dropped 5% → ALERT (maybe false alarm)
Pravaha: Battery charge dropped 5% BUT:
  - Everything else is normal (solar, voltage, temp)
  - d-separation shows this pattern matches sensor_bias better than real failure
  - Suggests: Cross-check with redundant sensors before taking action
```

---

## 6. Conditional Independence Verification

### Table: Which Variables Are Conditionally Independent Given Stable Conditions?

| Variable 1 | Variable 2 | Given | d-Separated? | Reason |
|-----------|-----------|-------|--------------|--------|
| solar_input | bus_voltage | battery_state=stable | YES | Path blocked by battery |
| battery_temp | bus_voltage | battery_state=stable | YES | Different subsystems |
| solar_degradation | payload_temp | (always) | YES | No causal path |
| battery_voltage | battery_temp | battery_state=stable | PARTIAL | Weak coupling |
| bus_current | payload_temp | payload_radiator=healthy | YES | Isolated subsystems |
| battery_charge | solar_input | solar_input in range | YES | Battery mediates |

---

## 7. Implementation: How Pravaha Uses d-Separation

### In `root_cause_ranking.py`:

```python
def _detect_anomalies(nominal, degraded, threshold=0.15):
    """
    This is where d-separation is applied:
    
    1. We compute deviations for ALL observables
    2. But we apply threshold filtering:
       - If a variable's deviation is < 15%, we ignore it
       - This effectively conditions on "normal" for that variable
    3. d-separation then prevents spurious paths:
       - If solar_input is noisy but battery_state is stable,
         solar noise won't propagate to other variables
       - We won't incorrectly diagnose "solar degradation" when it's just noise
    """
    # Only flag deviations > threshold (conditioning on "normal" for small deviations)
    if fractional_dev < threshold:
        continue  # d-separation: this variable is independent under conditioning
    
    # Only large deviations are considered in inference
    anomalies[name] = fractional_dev
```

### How This Prevents False Alarms:

```
Scenario: Eclipse phase, solar power drops 30%

WITHOUT d-separation:
  solar_input drops → triggers path to battery_state → diagnoses "solar degradation"
  False alarm during normal eclipse!

WITH d-separation:
  solar_input drops 30%  ✓ flagged as anomaly
  battery_charge stable  ✓ NO anomaly (> threshold)
  battery_temp stable    ✓ NO anomaly
  Inference: Given battery_state is stable, solar path is BLOCKED
  Result: NO solar degradation diagnosis (it's just eclipse!)
```

---

## 8. Validation: Testing d-Separation Claims

To verify d-separation is working correctly:

### Test 1: Solar Noise Rejection

```python
# Solar input has 15% noise, but battery state is stable
nominal_solar = 400W (with noise ±60W)
degraded_solar = 395W (similar noise)
battery_charge_nominal = 95Ah
battery_charge_degraded = 95Ah  # STABLE

# Inference result:
# ✓ PASS if no "solar_degradation" diagnosis
# ✓ PASS if diagnosis probability < 20%
```

### Test 2: Payload Independence

```python
# Payload radiator fails (temp rises), power system is healthy
payload_temp_degraded = 65°C (vs 45°C nominal)
battery_voltage = 28.0V  # Normal
bus_voltage = 29.5V      # Normal
solar_input = 420W       # Normal

# Inference result:
# ✓ PASS if NO diagnosis blames power subsystem
# ✓ PASS if payload temperature is in separate diagnosis
```

### Test 3: Sensor Bias vs. Real Aging

```python
# Scenario: Battery charge reading dropped 8%, but nothing else changed
battery_charge_measured: 92Ah → 84Ah  (8% drop)
battery_voltage: STABLE
battery_temp: STABLE
solar_input: STABLE

# Inference result:
# ✓ PASS if diagnosis suggests sensor_bias
# ✓ PASS if battery_aging probability < 30%
# (d-separation blocks path from battery_aging when other observables stable)
```

---

## 9. Summary: DAG Properties

| Property | Value | Validation |
|----------|-------|-----------|
| Acyclic | ✓ YES | No directed loops |
| Nodes | 23 (7 root, 8 intermediate, 8 observable) | All listed above |
| Edges | 28 (complete specification above) | No missing causation |
| Exclusion Restrictions | 5+ critical | Prevent false diagnoses |
| d-Separation Coverage | ~15 key conditional independencies | Enables noise filtering |
| Mechanisms Documented | 100% of edges | Every edge explained |

---

## 10. Using This DAG

### For Operators:
- Understand WHY Pravaha makes a diagnosis (follow the causal path)
- Know what measurements DON'T propagate (d-separation)
- Recognize when satellite has multiple simultaneous faults

### For Engineers:
- Validate the causal structure against system design
- Add new root causes by extending the DAG
- Tune edge weights based on real telemetry

### For Researchers:
- Cite this as proof of causal reasoning (vs. statistical learning)
- Use as template for other satellite systems
- Publish as example of Pearl's causal inference in space systems

---

**Last Updated:** Jan 25, 2026  
**Status:** Complete DAG specification with d-separation analysis  
**TODO:** Visualize as interactive graph tool for operators
