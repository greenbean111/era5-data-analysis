"""
ERA5 vs. Hanle Precipitable Water Vapor (PWV) Comparison (2012)
Compiled from the initial PWV stage (Feb 13 - Apr 4, 2026).

Reproduces and extends `Initial_pwv_analysis.ipynb`:
- Loads 2012 hourly ERA5 Total Column Water (`tcw`, in mm / kg m^-2) at the nearest
  grid point to IAO Hanle (32.75 N, 79.00 E; pixel [3, 2]).
- Loads ground-based Hanle PWV measurements (`pwv_hanle.dat`, 2008-2024) filtered to 2012.
- Aligns Hanle observations to the ERA5 hourly grid (both raw/uninterpolated and
  time-interpolated).
- Computes summary statistics and saves 5 labeled figures to `pwv_analysis/graphs/`.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Paths (relative to repo root)
REPO_ROOT = Path(__file__).resolve().parent.parent
ERA5_NC = REPO_ROOT / "data" / "raw" / "Individual Data Segments (Scratch)" / "data_stream-oper_stepType-instant.nc"
HANLE_DAT = REPO_ROOT / "data" / "raw" / "pwv_hanle.dat"

OUT_DIR = Path(__file__).resolve().parent
GRAPHS_DIR = OUT_DIR / "graphs"
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)


def load_era5_pwv(nc_path: Path) -> tuple[pd.DataFrame, float, float]:
    """Load 2012 hourly ERA5 tcw at the closest Hanle grid pixel [3, 2]."""
    ds = xr.open_dataset(nc_path)
    pwv_era5 = ds["tcw"]
    time_era5 = ds["valid_time"]

    lat = float(ds["latitude"].values[3])
    lon = float(ds["longitude"].values[2])
    pwv_pixel = pwv_era5[:, 3, 2]

    era5_df = pd.DataFrame({
        "time": pd.to_datetime(time_era5.values).floor("h"),
        "pwv_era5": pwv_pixel.values.astype(float),
    })
    return era5_df, lat, lon


def load_hanle_pwv_2012(dat_path: Path) -> pd.DataFrame:
    """Load Hanle PWV measurements and filter to calendar year 2012."""
    hanle = pd.read_csv(
        dat_path,
        sep=r"\s+",
        comment="#",
        names=["year", "doy", "hour", "minute", "second", "pwv"],
    )
    hanle["time"] = (
        pd.to_datetime(hanle["year"].astype(str) + "-" + hanle["doy"].astype(str), format="%Y-%j")
        + pd.to_timedelta(hanle["hour"], unit="h")
    )
    hanle_2012 = hanle.loc[hanle["time"].dt.year == 2012, ["time", "pwv"]].rename(
        columns={"pwv": "pwv_hanle"}
    )
    return hanle_2012.sort_values("time").reset_index(drop=True)


def compute_stats(df: pd.DataFrame, label: str) -> dict:
    """Compute comparison metrics for valid paired timestamps."""
    valid = df.dropna(subset=["pwv_era5", "pwv_hanle"]).copy()
    diff = valid["pwv_era5"] - valid["pwv_hanle"]
    return {
        "series": label,
        "n_era5_timestamps": int(len(df)),
        "n_paired_points": int(len(valid)),
        "mean_diff_era5_minus_hanle_mm": float(diff.mean()),
        "std_diff_mm": float(diff.std()),
        "rmse_mm": float(np.sqrt((diff ** 2).mean())),
        "min_diff_mm": float(diff.min()),
        "max_diff_mm": float(diff.max()),
        "pearson_r": float(valid["pwv_era5"].corr(valid["pwv_hanle"])),
    }


def format_date_axis(ax):
    """Format x-axis cleanly by month for 2012."""
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.grid(True, linestyle="--", alpha=0.35)


def main():
    era5_df, lat, lon = load_era5_pwv(ERA5_NC)
    hanle_2012 = load_hanle_pwv_2012(HANLE_DAT)

    # 1. Raw (uninterpolated) alignment on ERA5 hourly grid
    hanle_raw_grid = (
        hanle_2012.set_index("time")
        .reindex(era5_df["time"])
        .reset_index()
        .rename(columns={"index": "time"})
    )
    merged_raw = pd.merge(era5_df, hanle_raw_grid, on="time", how="left")
    merged_raw["difference"] = merged_raw["pwv_era5"] - merged_raw["pwv_hanle"]

    # 2. Time-interpolated alignment on ERA5 hourly grid
    hanle_interp_grid = (
        hanle_2012.set_index("time")
        .reindex(era5_df["time"])
        .interpolate("time")
        .reset_index()
        .rename(columns={"index": "time"})
    )
    merged_interp = pd.merge(era5_df, hanle_interp_grid, on="time", how="left")
    merged_interp["difference"] = merged_interp["pwv_era5"] - merged_interp["pwv_hanle"]

    # Save summary stats
    raw_stats = compute_stats(merged_raw, "raw_uninterpolated")
    interp_stats = compute_stats(merged_interp, "time_interpolated")
    stats_df = pd.DataFrame([raw_stats, interp_stats])
    stats_df.to_csv(OUT_DIR / "pwv_2012_summary_stats.csv", index=False)

    print(f"ERA5 Grid Point: ({lat:.2f} N, {lon:.2f} E)")
    print(stats_df.to_string(index=False))

    # --- Plot 1: ERA5 vs Hanle (Raw) ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(merged_raw["time"], merged_raw["pwv_era5"], label="ERA5 PWV (tcw)", color="tab:blue", linewidth=1.1)
    ax.plot(
        merged_raw["time"],
        merged_raw["pwv_hanle"],
        "o",
        label=f"Hanle Measured PWV (N={raw_stats['n_paired_points']})",
        color="tab:orange",
        markersize=2.8,
        alpha=0.8,
    )
    ax.set_title(f"ERA5 vs. Hanle Measured PWV (2012) — Grid ({lat:.2f}°N, {lon:.2f}°E)")
    ax.set_xlabel("Date (2012)")
    ax.set_ylabel("Precipitable Water Vapor, PWV (mm)")
    ax.legend(loc="upper right")
    format_date_axis(ax)
    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / "01_era5_vs_hanle_pwv_2012_raw.png", dpi=150)
    plt.close(fig)

    # --- Plot 2: Difference (Raw) ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axhline(0.0, color="black", linestyle="--", linewidth=0.9, label="Zero Bias (0 mm)")
    ax.axhline(
        raw_stats["mean_diff_era5_minus_hanle_mm"],
        color="darkred",
        linestyle=":",
        linewidth=1.3,
        label=f"Mean Bias = {raw_stats['mean_diff_era5_minus_hanle_mm']:.2f} mm",
    )
    ax.plot(
        merged_raw["time"],
        merged_raw["difference"],
        "o-",
        color="tab:red",
        markersize=2.5,
        linewidth=0.8,
        alpha=0.8,
        label="PWV Difference (ERA5 - Hanle)",
    )
    ax.set_title("PWV Difference Over Time (ERA5 - Hanle, 2012 Uninterpolated)")
    ax.set_xlabel("Date (2012)")
    ax.set_ylabel("PWV Difference: ERA5 - Hanle (mm)")
    ax.legend(loc="lower right")
    format_date_axis(ax)
    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / "02_pwv_difference_era5_minus_hanle_raw.png", dpi=150)
    plt.close(fig)

    # --- Plot 3: ERA5 vs Hanle (Time-Interpolated) ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(merged_interp["time"], merged_interp["pwv_era5"], label="ERA5 PWV (tcw)", color="tab:blue", linewidth=1.1)
    ax.plot(
        merged_interp["time"],
        merged_interp["pwv_hanle"],
        label="Hanle PWV (time-interpolated)",
        color="tab:orange",
        linewidth=1.1,
        alpha=0.9,
    )
    ax.set_title("ERA5 vs. Hanle Measured PWV (2012, Time-Interpolated)")
    ax.set_xlabel("Date (2012)")
    ax.set_ylabel("Precipitable Water Vapor, PWV (mm)")
    ax.legend(loc="upper right")
    format_date_axis(ax)
    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / "03_era5_vs_hanle_pwv_2012_interpolated.png", dpi=150)
    plt.close(fig)

    # --- Plot 4: Difference (Time-Interpolated) ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axhline(0.0, color="black", linestyle="--", linewidth=0.9, label="Zero Bias (0 mm)")
    ax.axhline(
        interp_stats["mean_diff_era5_minus_hanle_mm"],
        color="darkred",
        linestyle=":",
        linewidth=1.3,
        label=f"Mean Bias = {interp_stats['mean_diff_era5_minus_hanle_mm']:.2f} mm",
    )
    ax.plot(
        merged_interp["time"],
        merged_interp["difference"],
        color="tab:red",
        linewidth=1.0,
        alpha=0.85,
        label="PWV Difference (ERA5 - Interpolated Hanle)",
    )
    ax.set_title("PWV Difference Over Time (ERA5 - Hanle, 2012 Interpolated)")
    ax.set_xlabel("Date (2012)")
    ax.set_ylabel("PWV Difference: ERA5 - Hanle (mm)")
    ax.legend(loc="lower right")
    format_date_axis(ax)
    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / "04_pwv_difference_era5_minus_hanle_interpolated.png", dpi=150)
    plt.close(fig)

    # --- Plot 5: ERA5 vs Hanle (Interpolated + Original Points Overlay) ---
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(merged_interp["time"], merged_interp["pwv_era5"], label="ERA5 PWV (tcw)", color="tab:blue", linewidth=1.1)
    ax.plot(
        merged_interp["time"],
        merged_interp["pwv_hanle"],
        label="Hanle PWV (time-interpolated)",
        color="tab:orange",
        linewidth=1.1,
    )
    ax.scatter(
        hanle_2012["time"],
        hanle_2012["pwv_hanle"],
        color="tab:red",
        s=10,
        alpha=0.75,
        zorder=5,
        label=f"Hanle Original Measurements (N={len(hanle_2012)})",
    )
    ax.set_title("ERA5 vs. Hanle Measured PWV (2012, Interpolated with Original Points)")
    ax.set_xlabel("Date (2012)")
    ax.set_ylabel("Precipitable Water Vapor, PWV (mm)")
    ax.legend(loc="upper right")
    format_date_axis(ax)
    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / "05_era5_vs_hanle_pwv_2012_interpolated_with_points.png", dpi=150)
    plt.close(fig)

    print(f"Saved 5 graphs to {GRAPHS_DIR}")


if __name__ == "__main__":
    main()
