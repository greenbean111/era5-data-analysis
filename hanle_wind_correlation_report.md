# Technical Report: Wind Data Calibration & ERA5 Correlation Analysis (ALMA vs. Hanle)

This report details:
1. **ALMA Wind Calibration Levels**: How they work, their benefits/limitations, and scientific acceptability.
2. **Hanle Low Correlation**: Why the global model and ground observations diverge so significantly at the Hanle site.
3. **ERA5 Reanalysis Methods**: The models, grid scales, and data assimilation techniques behind ERA5.

---

## 1. ALMA Correlation Fixing: Three Levels of Calibration

Global weather models like ERA5 systematically underestimate wind speeds in complex high-altitude terrains due to smoothed topography. Calibration translates these model outputs to match localized conditions.

| Calibration Level | Method | How It Works | Acceptability Level |
| :--- | :--- | :--- | :--- |
| **Level 1: Constant Mean Offset** | $v_{\text{cal}} = v_{\text{ERA5}} - \text{Bias}$ | Subtracts the mean bias error (adds $\approx 4.06\text{ m/s}$ for ALMA) across all timestamps. | **Low / Baseline Acceptability**<br>Adjusts the mean magnitude and improves RMSE, but leaves Pearson Correlation ($R$) **completely unchanged** because it is a simple linear shift. Does not capture time-of-day or wind-direction dynamics. |
| **Level 2: Diurnal-Sector Binning** | $v_{\text{cal}} = m_{(h, s)} \cdot v_{\text{ERA5}} + b_{(h, s)}$ | Splits data into 192 discrete bins based on Hour of Day $h \in [0..23]$ and Wind Direction Sector $s \in [\text{N, NE..NW}]$. Fits independent linear regression models for each bin. | **Medium Acceptability**<br>Improves correlation by modeling mountain diurnal wind cycles and directional shadowing. However, it introduces **boundary discontinuities** (unphysical jumps in speed when direction shifts by $0.1^\circ$ near sector edges) and is prone to **overfitting** in sparse bins. |
| **Level 3: Smooth Ridge Regression with Lags** | $v_{\text{cal}} = f(ws, u, v, \text{lags}, \sin/\cos \text{time})$ | Fits a single global L2-regularized Ridge regression using continuous wind components ($u, v$ vectors), time-harmonics (sine/cosine curves), and lag/lead features ($t-1$, $t+1$). | **High Acceptability (Best Practice)**<br>Produces a continuous, physically consistent calibration without step-changes. The lag features correct for spatial/temporal phase shifts of wind fronts between the coarse 31km grid and the specific ground station. |

---

## 2. Why Are Hanle Wind Observations and ERA5 So Uncorrelated?

Ground observations at Hanle show a significantly weaker raw correlation with ERA5 than ALMA. This divergence is driven by several physical and geographical factors:

### A. Valley Channelling and Extreme Sub-Grid Topography
* **Scale Discrepancy**: ERA5 has a horizontal resolution of $\approx 31\text{ km}$. The terrain height in the model is average grid-cell elevation, which smooths out sharp peaks and narrow gorges.
* **Micro-climates**: Hanle is situated in a high-altitude Himalayan valley ($\approx 4,500\text{ m}$) surrounded by steep mountains. Strong local winds are dominated by **anabatic (daytime upslope)** and **katabatic (nighttime downslope)** gravity currents. These are micro-scale thermal currents ($100\text{ m} - 2\text{ km}$ scale) that cannot be simulated on a $31\text{ km}$ model grid.

### B. Lack of Local Data Assimilation
* Global atmospheric models rely heavily on **data assimilation**—blending actual weather station observations into the model running in real-time to correct its trajectory.
* While the Chilean Andes (hosting major international astronomical observatories like ALMA and Cerro Paranal) have dense, highly integrated meteorological networks, the Karakoram-Himalayan high-altitude region suffers from a **severe scarcity of ground-based stations**. Without local ground telemetry to guide the assimilation process, ERA5's reanalysis over Hanle is largely unanchored by local reality.

### C. Thermal Decoupling
* In the dry, thin atmosphere of Hanle, daytime radiative heating of the valley slopes is intense, causing convective boundary layer mixing. At night, rapid radiative cooling creates intense thermal inversions.
* This severe daily stratification **decouples** valley-bottom wind speeds from the free-tropospheric synoptic-scale winds overhead (which the global ERA5 model simulates accurately).

---

## 3. ERA5 Methodology: How the Reanalysis is Built

ERA5 is the fifth-generation atmospheric reanalysis from the European Centre for Medium-Range Weather Forecasts (ECMWF). It does not just simulate the weather; it combines physics with observations.

### A. Integrated Forecasting System (IFS)
* ERA5 is based on the IFS Cycle 41r2 numerical weather prediction model, which represents the atmosphere using fluid dynamics equations (Navier-Stokes), thermodynamics, and radiative transfer code.
* Physical parameterizations model sub-grid scale processes, such as cloud formation, land-surface interactions, and boundary-layer turbulence.

### B. 4D-Var Data Assimilation
* ERA5 uses **Four-Dimensional Variational (4D-Var) Data Assimilation**.
* Every 12 hours, the system gathers millions of observations worldwide (satellites, weather balloons, commercial aircraft, marine buoys, and ground stations).
* It adjusts the model's starting conditions (state variables) such that the physical simulation path matches the observations as closely as possible across both space and time (the 4th dimension).

### C. 10m Wind Speed Calculation (`u10` and `v10`)
* The variables `u10` (eastward component) and `v10` (northward component) are not directly simulated at a physical height of 10 meters above the actual ground.
* Instead, they are calculated using **Monin-Obukhov Similarity Theory** (surface boundary layer physics). The model takes the wind speed at the lowest model level (typically $\approx 10\text{ meters}$ above the model's smoothed surface elevation) and applies drag/roughness coefficients based on estimated land cover (e.g., bare soil, snow, sparse vegetation) to estimate wind at a 10m standard height.
* If the local site has complex roughness (cliffs, local wind shadow) not represented in the model's land cover database, the calculated 10m wind speed will significantly deviate from a ground-based anemometer.

---

## 4. Scientific Acceptability: Realignment vs. Reconstruction (Cherry-Picking)

In statistical meteorology, calibrating model output to local ground conditions is called **Model Output Statistics (MOS)**. However, we must distinguish between an acceptable **realignment** of the data and a forced **reconstruction** (which results in overfitting and cherry-picking).

### A. Realignment (Scientifically Acceptable Adjustment)
* **What it is**: Adjusting the statistical properties of the model output (e.g. shifts in mean, expansion of variance) to correct for systemic, macro-scale biases (like altitude differences or grid-cell smoothing) without altering or inventing high-frequency variations.
* **Constant Offset (+4.0626 m/s)**: This is a **pure realignment**. It simply shifts the wind speed distribution. It does not attempt to change the correlation, the timing of wind shifts, or direction. It assumes a flat regional bias and realigns the baseline. It has zero capacity to overfit or cherry-pick.
* **Global Linear Rescale (1.2986 * ws + 3.3197)**: This is also a **pure realignment**. It performs a single global linear stretch and shift. It expands the wind speed variance to match ground-level fluctuation ranges but does not "invent" daily/hourly wind events. It is a standard, robust physical scaling.

### B. Reconstruction (Cherry-Picking & Forcing Data to Fit Exactly)
* **What it is**: Attempting to rebuild or synthesize missing physical events, local hourly dynamics, and directional wind shifts by using a high number of parameters to force the model data to match ground-based observations.
* **Diurnal-Sector Calibration**: This is a **reconstruction** system. By fitting **192 independent linear regressions** (one for each hour/direction bin), it tries to force the model to reproduce ALMA's specific local slope-wind patterns. Because it splits the dataset into narrow bins, it fits local noise (overfitting/cherry-picking) and introduces unphysical discontinuities (jumps) at the boundaries. It is trying to reconstruct microscale wind physics that the global model cannot resolve, which is unscientific.

### C. The Regularized Approach (Smooth Ridge Regression)
* **Smooth Ridge Regression with Lags** is a **hybrid approach: regularized realignment**.
* While it uses features like time-of-day and directional vectors to capture diurnal cycles, the **L2 regularization (Ridge)** penalizes large weights, preventing the model from reconstructing high-frequency wind speed details. It acts as a smooth, continuous calibration function that realigns the model's daily cycles without overfitting.

### D. Direct Model Transfer as a Scientific Control
* Applying the ALMA-trained calibrations directly to Hanle serves as a validation test for **realignment vs. reconstruction**:
  * **Realignment Transfer (Offset & Linear)**: These models perform relatively well on Hanle, reducing the RMSE from `5.27 m/s` to `4.16 m/s` (Linear Rescale). Because they only realigned the mean/variance of the wind speed distribution, they successfully corrected for the systematic global underestimation of high-altitude mountain winds.
  * **Reconstruction Transfer (Ridge Regression)**: The ALMA-trained Ridge model failed to generalize, **dropping the Pearson Correlation ($R$) from 0.3928 to 0.2984**. This confirms that local diurnal and directional features represent a site-specific reconstruction: transferring ALMA's reconstructed weights to Hanle introduces phase mismatches and degrades the physical structure of the dataset.


