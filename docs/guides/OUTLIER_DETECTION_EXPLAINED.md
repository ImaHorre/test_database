# Outlier Detection Methodology: Real-World Demonstration

This document demonstrates how the outlier detection system works using **real W13 5ml/hr 200mbar droplet size data** from the database.

## Overview

The dashboard uses the **Modified Z-Score method** (Iglewicz and Hoaglin, 1993) for outlier detection:
- More robust than standard z-score
- Uses median and MAD (Median Absolute Deviation) instead of mean and standard deviation
- Less sensitive to extreme values than traditional methods
- Threshold: |Modified Z-Score| > 3.5 indicates an outlier

## Real Dataset: W13 5ml/hr 200mbar

**Context:** 35 droplet size measurements from 5 W13 devices tested at identical flow parameters (5ml/hr aqueous flowrate, 200mbar oil pressure).

### Raw Data Summary

| Statistic | Value |
|-----------|-------|
| Total measurements | 35 |
| Mean | 25.86 µm |
| Median | 24.73 µm |
| Std deviation | 8.27 µm |
| Range | 19.62 - 71.49 µm |

**Key observation:** Notice the large standard deviation (8.27 µm) and wide range. The maximum value (71.49 µm) is nearly 3x the minimum (19.62 µm), suggesting a potential outlier.

---

## Step-by-Step Outlier Detection

### Step 1: Calculate Median
```
Median = 24.73 µm
```

**Why median?** Unlike the mean, the median is not influenced by extreme values. This makes it a robust "center" for the dataset.

### Step 2: Calculate MAD (Median Absolute Deviation)
```
For each measurement: calculate |x - median|
Then: MAD = median of all those deviations
Result: MAD = 1.80 µm
```

**Why MAD?** Similar to standard deviation but much more robust to outliers. Standard deviation would be heavily influenced by the 71.49 µm value, but MAD remains stable.

### Step 3: Calculate Modified Z-Scores
```
Formula: M_i = 0.6745 * (x_i - median) / MAD

The constant 0.6745 makes MAD comparable to standard deviation
for normally distributed data.
```

### Step 4: Apply Threshold
```
Threshold: |M_i| > 3.5
```

**Why 3.5?** This is the standard threshold in statistical literature for the Modified Z-Score method. It corresponds to roughly 3 standard deviations in normally distributed data but is more appropriate for non-normal distributions.

---

## Results: Top 10 Measurements by |Modified Z-Score|

| Device | DFU Row | Size (µm) | Modified Z-Score | Outlier? |
|--------|---------|-----------|------------------|----------|
| W13_S2_R9 | DFU2 | **71.49** | **17.55** | ✓ **YES** |
| W13_S4_R12 | DFU1 | 19.62 | -1.92 | No |
| W13_S1_R2 | DFU6 | 28.98 | 1.60 | No |
| W13_S4_R12 | DFU2 | 20.52 | -1.58 | No |
| W13_S1_R2 | DFU5 | 28.88 | 1.56 | No |
| W13_S4_R12 | DFU5 | 21.06 | -1.37 | No |
| W13_S1_R2 | DFU1 | 27.57 | 1.07 | No |
| W13_S5_R14 | DFU4 | 21.98 | -1.03 | No |
| W13_S1_R2 | DFU3 | 27.46 | 1.02 | No |
| W13_S5_R14 | DFU2 | 22.07 | -1.00 | No |

---

## Outlier Identified

**Single outlier detected:** W13_S2_R9 DFU2 (71.49 µm)

### Why is this an outlier?

1. **Modified Z-Score = 17.55:** This is **5x higher** than the threshold (3.5), indicating extreme deviation
2. **Visual inspection:** 71.49 µm is nearly 3x the median (24.73 µm)
3. **Physical plausibility:** This value is far outside the expected range for this device and flow parameters
4. **Isolated occurrence:** All other measurements from W13_S2_R9 at this condition are in the normal range (23-27 µm)

**Likely cause:** Measurement error, transient device malfunction, or contamination during that specific DFU row measurement.

---

## Impact of Removal

### Statistics Comparison

| Metric | With Outlier | Without Outlier | Improvement |
|--------|--------------|-----------------|-------------|
| **Mean** | 25.86 µm | **24.51 µm** | -5.2% (closer to median) |
| **Median** | 24.73 µm | 24.43 µm | -1.2% (stable, as expected) |
| **Std Dev** | 8.27 µm | **2.36 µm** | **-71.5%** (much tighter) |
| **Range** | 52.87 µm | 9.36 µm | -82.3% |
| **Measurements** | 35 | 34 | -2.9% |

### Key Takeaways

1. **Standard deviation reduced by 71.5%:** The cleaned dataset is much more consistent
2. **Mean shifted closer to median:** The outlier was inflating the mean
3. **Only 1 measurement removed (2.9%):** Minimal data loss
4. **Range dramatically reduced:** From 52.87 µm to 9.36 µm

---

## Dashboard TUI Output Example

When you run `show w13 at 5mlhr 200mbar` with outlier detection enabled (`-outliers`), you'll see:

```
Data Filtering Summary:
  Original measurements: 35
  Removed by outlier detection: 1 (2.9%)
  Removed measurements:
    • W13_S2_R9 DFU2 (71.49 µm)
  Final measurements: 34

Per-Device Statistics:
  W13_S1_R2:
    • Droplet Size: 27.12 ± 1.34 µm (n=9)
  W13_S2_R6:
    • Droplet Size: 23.62 ± 0.86 µm (n=9)
  W13_S2_R9:
    • Droplet Size: 25.78 ± 1.10 µm (n=7)  ← Outlier removed from this device
  W13_S4_R12:
    • Droplet Size: 21.64 ± 1.46 µm (n=6)
  W13_S5_R14:
    • Droplet Size: 22.23 ± 0.36 µm (n=3)

Overall Average:
  Droplet Size: 24.51 ± 2.36 µm (n=34)
```

---

## When to Use Outlier Detection

### ✅ Use outlier detection when:
- You have multiple measurements (>10) at the same experimental conditions
- You want to identify measurement errors or device malfunctions
- You're comparing devices and want to avoid skewed averages
- You're building a statistical model and need clean data

### ⚠️ Use caution when:
- You have very few measurements (<5)
- Outliers might be scientifically meaningful (e.g., device failure modes)
- You're analyzing edge cases or extreme parameter ranges

### 🔍 Always review:
The dashboard shows exactly which measurements were removed and their values. Always check if the removed data represents:
- **Measurement errors** (remove)
- **Device defects** (flag but consider keeping)
- **Real physical phenomena** (keep)

---

## Method Advantages

1. **Robust:** Not influenced by the outlier itself when calculating the threshold
2. **Interpretable:** Modified Z-Score has clear statistical meaning
3. **Automatic:** No manual threshold tuning required
4. **Conservative:** Only flags extreme outliers (3.5 standard deviations)
5. **Transparent:** Dashboard shows exactly what was removed

---

## References

Iglewicz, B., and Hoaglin, D. (1993). *How to Detect and Handle Outliers*. ASQC Quality Press.

---

## Try It Yourself

```bash
# In the dashboard:
>>> -outliers                      # Enable outlier detection
>>> show w13 at 5mlhr 200mbar      # Run query
>>> -outliers                      # Disable outlier detection
>>> show w13 at 5mlhr 200mbar      # Compare results
```

Notice how the mean and standard deviation change when outlier detection is enabled!
