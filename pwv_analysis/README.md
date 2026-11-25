# PWV Analysis: ERA5 vs. Hanle Ground Measurements (2012)

**Active Stage:** February 13 – April 4, 2026 *(renamed/cleaned June 24, 2026)*  
**Location:** IAO Hanle, Ladakh, India (`32.78°N, 78.96°E`; nearest ERA5 grid point `32.75°N, 79.00°E`)

---

## 1. Goal & Big Question

* **Big Question:** How accurately does ERA5 reanalysis Total Column Water (`tcw`) represent actual ground-measured Precipitable Water Vapor (PWV) at a high-altitude site like Hanle, and what is the systematic bias between them?
* **Main Goal:** Compare 2012 hourly ERA5 `tcw` against ground-based Hanle PWV observations (`pwv_hanle.dat`) to quantify agreement and bias.

---

## 2. Data Sources

| Dataset | File | Coverage | Notes |
| :--- | :--- | :--- | :--- |
| **ERA5 Reanalysis (`tcw`)** | `data/raw/Individual Data Segments (Scratch)/data_stream-oper_stepType-instant.nc` | 2012-01-01 to 2012-12-31 (8,784 hourly steps) | Pre-cut `7 × 5` grid (`32.0°–33.5°N`, `78.5°–79.5°E`, `0.25°` spacing); converted from GRIB on `2026-02-23`. Pixel `[3, 2]` (`32.75°N, 79.00°E`) used for Hanle. |
| **Hanle Ground PWV** | `data/raw/pwv_hanle.dat` | 2008 (DOY 65) – 2024 (DOY 181) (20,967 records total; **1,525** in 2012) | Columns: `YR DOY HOUR MIN SEC PWV(mm)`. Independent from the 2020–2021 AWS (`MetsSerServr`) wind/weather logs. |

---

## 3. Methodology

Implemented in `Initial_pwv_analysis.ipynb` and reproduced cleanly in `run_pwv_analysis.py`:
1. Extract hourly `tcw` from ERA5 at grid pixel `[3, 2]` (`32.75°N, 79.00°E`) and floor `valid_time` to the hour.
2. Parse `pwv_hanle.dat` timestamps (`year + doy + hour`) and filter to calendar year `2012`.
3. Align Hanle observations onto the 8,784-hour ERA5 time grid in two ways:
   * **Raw (uninterpolated):** Direct reindex (`how="left"`, keeping missing hours as `NaN`).
   * **Time-interpolated:** Linear time interpolation (`interpolate("time")`) across gaps between Hanle observations.
4. Compute residuals (`difference = pwv_era5 - pwv_hanle`) and summary statistics.

---

## 4. Key Results (2012)

Saved to `pwv_2012_summary_stats.csv`:

| Alignment | Paired Points | Mean Bias (`ERA5 - Hanle`) | Std Dev | RMSE | Min Diff | Max Diff | Pearson $r$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw (uninterpolated)** | 1,525 | `-2.14 mm` | `1.33 mm` | `2.52 mm` | `-8.09 mm` | `+1.21 mm` | `0.937` |
| **Time-interpolated** | 8,782 | `-1.45 mm` | `2.04 mm` | `2.50 mm` | `-8.09 mm` | `+7.28 mm` | `0.717` |

**Takeaway:** ERA5 tracks the seasonal PWV cycle strongly ($r = 0.937$ on direct paired points) but **systematically underestimates** Hanle ground PWV by `-2.14 mm` on average (up to `-8.09 mm`).

---

## 5. Folder Contents & Graphs

* `Initial_pwv_analysis.ipynb` — Original exploratory notebook (originally `IAO_Hanle_MSR_reanalysis_test_download_read.ipynb`).
* `run_pwv_analysis.py` — Standalone reproducible script that computes all metrics and exports labeled figures.
* `pwv_2012_summary_stats.csv` — Summary metrics table.
* `graphs/` — Generated, labeled figures:
  1. `01_era5_vs_hanle_pwv_2012_raw.png` — ERA5 `tcw` vs. raw Hanle PWV scatter points (2012).
  2. `02_pwv_difference_era5_minus_hanle_raw.png` — Non-interpolated `ERA5 - Hanle` residual time series with mean bias line.
  3. `03_era5_vs_hanle_pwv_2012_interpolated.png` — ERA5 `tcw` vs. time-interpolated Hanle PWV (2012).
  4. `04_pwv_difference_era5_minus_hanle_interpolated.png` — Interpolated `ERA5 - Hanle` residual time series with mean bias line.
  5. `05_era5_vs_hanle_pwv_2012_interpolated_with_points.png` — Interpolated comparison overlaid with original 1,525 Hanle points.

---

## 6. Reproducing

From the repository root:

```bash
.\.venv\Scripts\python.exe pwv_analysis\run_pwv_analysis.py
```
