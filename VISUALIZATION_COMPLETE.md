# Interactive Causal DAG Visualization - Complete ✓

**Status:** Ready for Operations  
**Generated:** January 25, 2026  
**For:** Operators and analysts

---

## What Was Delivered

An **interactive web-based visualization** of the Pravaha causal DAG that operators can use to:
- Understand failure propagation paths
- Diagnose root causes from symptoms
- Validate Pravaha's recommendations
- Learn the causal structure

---

## Quick Start (2 Minutes)

```bash
cd /path/to/pravaha

# Generate the interactive visualization
python causal_graph/interactive_dag_viz.py

# Open in web browser
open dag_visualization.html           # macOS
xdg-open dag_visualization.html       # Linux
start dag_visualization.html          # Windows
```

That's it! No server needed. Works offline.

---

## What You Get

### 1. **dag_visualization.html** (18 KB)
The interactive visualization itself:
- 23 color-coded nodes (root causes, effects, measurements)
- 29 causal edges with weights and mechanisms
- Three-layer hierarchical layout
- Hover tooltips for exploration
- Zoom, pan, reset controls
- Statistics and legend

### 2. **New Documentation Files**

#### OPERATOR_CHEATSHEET.md (Quick Reference)
- 2-minute quick start
- All 7 root causes listed
- 4 diagnostic patterns with decision trees
- Common gotchas
- Quick commands

**→ Read this FIRST if you're in a hurry**

#### INTERACTIVE_GUIDE.md (Complete User Manual)
- How to generate and open the visualization
- Understanding node types and edge meanings
- 5 step-by-step use cases
- Troubleshooting
- Operator workflows

**→ Read this to master the tool**

#### Updated Documentation
- **DAG_DOCUMENTATION.md:** Now points to interactive tool
- **INDEX.md:** Updated with new files and structure

---

## Visual Guide

### Node Types (Color-Coded)

| Color | Type | Meaning |
|-------|------|---------|
| 🔴 Red Star | Root Cause | Primary faults to diagnose |
| 🟢 Teal Diamond | Intermediate | Propagation mechanisms |
| 🔵 Blue Circle | Observable | Measured telemetry |

### Understanding Edges

- **Thick, bright line** = Strong causal effect (weight > 0.7)
- **Thin, dim line** = Weak effect (weight < 0.5)
- **Hover** to see mechanism description

---

## Usage Scenarios

### Scenario 1: Battery Voltage Drops 2%

1. Open dag_visualization.html
2. Find `battery_voltage_measured` (blue circle)
3. Hover to see description
4. Trace backward on incoming edges
5. Look at source nodes:
   - Solar input normal? → Not solar degradation
   - Battery temp high? → Thermal stress likely
   - Everything else normal? → Maybe sensor error

### Scenario 2: Multiple Deviations

1. Identify all deviating observables (blue circles)
2. Find which intermediate effects they connect to
3. See which root causes (red stars) could explain all of them
4. Read edge mechanisms to understand the cascade

### Scenario 3: Understand Pravaha's Diagnosis

1. Pravaha says: "Solar degradation (98% probability)"
2. Open visualization
3. Find `solar_degradation` (red star, top-left)
4. Follow the paths downward to observables
5. Check if YOUR deviations match this pattern
6. Read mechanisms to understand the reasoning

---

## Feature Highlights

✅ **Interactive**
- Hover over nodes for descriptions and failure modes
- Hover over edges for weights and mechanisms
- Zoom, pan, double-click to reset

✅ **Operator-Focused**
- Color-coded by type (easy to distinguish)
- Mechanism explanations in plain language
- No technical jargon unless necessary

✅ **Self-Contained**
- Works offline (no internet required after generation)
- Single HTML file (18 KB)
- No server or installation needed

✅ **Fully Documented**
- Quick reference card (OPERATOR_CHEATSHEET.md)
- Complete user guide (INTERACTIVE_GUIDE.md)
- Diagnostic patterns with decision trees

✅ **Customizable**
```bash
# Custom title and output file
python causal_graph/interactive_dag_viz.py \
  --title "My Organization's Diagnostics" \
  --output my_dag.html
```

---

## The Three Layers (What You'll See)

```
LAYER 1: ROOT CAUSES (Red Stars) - What we diagnose
  solar_degradation  battery_aging  battery_thermal  ...

        ↓↓↓ Failure cascades ↓↓↓

LAYER 2: INTERMEDIATES (Teal Diamonds) - Mechanisms
  solar_input  battery_state  battery_efficiency  ...

        ↓↓↓ Physical manifestations ↓↓↓

LAYER 3: OBSERVABLES (Blue Circles) - What we measure
  battery_voltage_measured  battery_charge_measured  ...
```

---

## For Different Users

### Operations Staff (Shift Operators)
1. Read: OPERATOR_CHEATSHEET.md (5 min)
2. Use: dag_visualization.html (for diagnosis support)
3. Ask: When unsure, see INTERACTIVE_GUIDE.md

### Supervisors/Managers
1. Read: This file (2 min)
2. Use: dag_visualization.html (for incident reports)
3. Share: Screenshots for documentation

### Engineers/Researchers
1. Read: All documentation
2. Use: dat_visualization.html (for validation)
3. Modify: graph_definition.py (if needed)

---

## The Statistics

The visualization shows you the complete DAG:

| Metric | Value |
|--------|-------|
| Root Causes | 7 |
| Intermediate Effects | 8 |
| Observable Measurements | 8 |
| Total Nodes | 23 |
| Causal Relationships | 29 |

**Key Point:** Every node has a purpose. Every edge has physics behind it.

---

## Integration with Pravaha

This visualization works with:

1. **graph_definition.py** - The underlying DAG structure
2. **root_cause_ranking.py** - The inference engine
3. **d_separation.py** - Validation of causal assumptions
4. **GSAT-6A forensics** - Real-world case study

When Pravaha recommends a diagnosis, you can:
1. Open the visualization
2. Find the recommended root cause
3. Trace the causal paths to your observed deviations
4. Verify Pravaha's reasoning

---

## Documentation Roadmap

### For Quick Use (2-10 minutes)
Start here:
- **OPERATOR_CHEATSHEET.md** - Quick reference
- **This file** - Overview

### For Complete Mastery (30-45 minutes)
Then read:
- **INTERACTIVE_GUIDE.md** - How to use the tool
- **DAG_DOCUMENTATION.md** - Complete specification

### For Scientific Foundation (Optional)
Advanced users:
- **README_CAUSAL_DAG.md** - Pearl's framework
- **INDEX.md** - Navigation guide

---

## Common Questions

**Q: Does it require internet?**  
A: No. Once generated, the HTML works completely offline.

**Q: Do I need Python running?**  
A: Only to generate the visualization. After that, just open the HTML in a browser.

**Q: Can I modify the DAG?**  
A: Yes! Edit `causal_graph/graph_definition.py`, then regenerate the HTML.

**Q: What if I see an edge I don't understand?**  
A: Hover over it to see the mechanism description. It explains the physics.

**Q: Why are some edges thin and others thick?**  
A: Thickness represents causal weight. Thick = stronger effect.

**Q: How do I use this to diagnose a fault?**  
A: Find the deviating measurement (blue circle), trace backward to root causes (red stars). Read OPERATOR_CHEATSHEET.md for examples.

---

## Technical Details

**Technology:** Plotly (JavaScript visualization library)  
**Format:** Standalone HTML (self-contained)  
**Dependency:** Built from `causal_graph/graph_definition.py`  
**Generation Time:** < 1 second  
**File Size:** 18 KB  
**Browser Support:** Any modern browser (Chrome, Firefox, Safari, Edge)

---

## Next Steps

1. **Generate the visualization:**
   ```bash
   python causal_graph/interactive_dag_viz.py
   ```

2. **Open it:**
   ```bash
   open dag_visualization.html
   ```

3. **Explore:**
   - Hover over nodes and edges
   - Zoom and pan
   - Try to trace a failure path

4. **Read the guides:**
   - OPERATOR_CHEATSHEET.md (2 min)
   - INTERACTIVE_GUIDE.md (10 min)

5. **Use it for diagnostics:**
   - When Pravaha gives a diagnosis
   - When you need to understand a failure
   - When training new operators

---

## Support

- **Quick questions:** See OPERATOR_CHEATSHEET.md
- **How-to questions:** See INTERACTIVE_GUIDE.md
- **Technical questions:** See DAG_DOCUMENTATION.md
- **Theory questions:** See README_CAUSAL_DAG.md
- **Navigation:** See INDEX.md

---

## What This Enables

With this visualization, operators can:

✓ **Understand** why Pravaha makes a diagnosis  
✓ **Verify** recommendations against causal logic  
✓ **Educate** themselves on satellite failure modes  
✓ **Train** new operators on system dependencies  
✓ **Document** incident root causes with visual proof  
✓ **Distinguish** between isolated subsystem failures  

**Result:** More informed decision-making, faster troubleshooting, better operator confidence.

---

## Summary

| Item | Location |
|------|----------|
| Interactive Visualization | `dag_visualization.html` |
| Quick Reference | `causal_graph/OPERATOR_CHEATSHEET.md` |
| User Guide | `causal_graph/INTERACTIVE_GUIDE.md` |
| Complete Spec | `causal_graph/DAG_DOCUMENTATION.md` |
| Generator Script | `causal_graph/interactive_dag_viz.py` |
| Navigation | `causal_graph/INDEX.md` |

---

**Status:** ✅ Complete and Ready for Operations  
**Generated:** January 25, 2026  
**For:** Operators, supervisors, analysts  
**Questions?** See the documentation files or contact the Pravaha team
