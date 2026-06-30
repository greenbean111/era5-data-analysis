import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

# 1. Load ALMA published timeseries
pub_path = r"data/exports/alma_published_timeseries.csv"
df_pub = pd.read_csv(pub_path, parse_dates=['datetime'])
df_pub['gust_ms'] = df_pub['gust'] / 3.6

print(f"Loaded {len(df_pub):,} published records.")

# 2. Load ERA5 data for ALMA site
ALMA_LAT = -23.029
ALMA_LON = -67.755

chile_files = sorted(glob.glob(r"data/raw/chile/chile_*.nc"))
print(f"Found {len(chile_files)} ERA5 NetCDF files.")

era5_records = []
for f in chile_files:
    with xr.open_dataset(f) as ds:
        point_ds = ds.sel(latitude=ALMA_LAT, longitude=ALMA_LON, method='nearest')
        df_pt = point_ds['i10fg'].to_dataframe().reset_index()
        era5_records.append(df_pt[['valid_time', 'i10fg']])

df_era5 = pd.concat(era5_records, ignore_index=True)
df_era5 = df_era5.rename(columns={'valid_time': 'datetime'})
print(f"Loaded {len(df_era5):,} ERA5 records.")

# 3. Align data and calculate statistics
merged_df = pd.merge(df_pub, df_era5, on='datetime', how='inner')
merged_df = merged_df.dropna(subset=['gust_ms', 'i10fg'])
merged_df = merged_df.sort_values('datetime').reset_index(drop=True)

print(f"Aligned dataset size: {len(merged_df):,} records.")

diff = merged_df['i10fg'] - merged_df['gust_ms']
rmse = np.sqrt((diff ** 2).mean())
bias = diff.mean()
mae = diff.abs().mean()
corr = merged_df['gust_ms'].corr(merged_df['i10fg'])

print("\n--- Wind Gust Comparison Metrics ---")
print(f"Mean Published Gust : {merged_df['gust_ms'].mean():.2f} m/s")
print(f"Mean ERA5 Gust      : {merged_df['i10fg'].mean():.2f} m/s")
print(f"Root Mean Sq. Error : {rmse:.2f} m/s")
print(f"Mean Bias Error     : {bias:.2f} m/s")
print(f"Mean Absolute Error : {mae:.2f} m/s")
print(f"Pearson Correlation : {corr:.4f}")

# 4. Plot gust comparison
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1, 1.2], hspace=0.35)

ax1 = fig.add_subplot(gs[0])
ax1.plot(merged_df['datetime'], merged_df['gust_ms'], color='#1f77b4', alpha=0.25, label='Hourly Ground-Based (m/s)', linewidth=0.5)
ax1.plot(merged_df['datetime'], merged_df['i10fg'], color='#ff7f0e', alpha=0.25, label='Hourly ERA5 (m/s)', linewidth=0.5)

df_rolled = merged_df.set_index('datetime').rolling('7D')
roll_max_pub = df_rolled['gust_ms'].max()
roll_max_era5 = df_rolled['i10fg'].max()

ax1.plot(roll_max_pub.index, roll_max_pub, color='#1f77b4', label='7-Day Rolling Max Ground-Based', linewidth=2.0)
ax1.plot(roll_max_era5.index, roll_max_era5, color='#ff7f0e', label='7-Day Rolling Max ERA5', linewidth=2.0)

ax1.set_title('ALMA Weather Station Gust Comparison: Full 2-Year Timeseries (2001-2002)', fontsize=14, fontweight='bold', pad=10)
ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Wind Speed (m/s)', fontsize=11)
ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
ax1.set_ylim(0, 45)

ax2 = fig.add_subplot(gs[1])
zoom_start, zoom_end = '2001-12-01', '2001-12-31'
df_zoom = merged_df[(merged_df['datetime'] >= zoom_start) & (merged_df['datetime'] <= zoom_end)].sort_values('datetime')

ax2.plot(df_zoom['datetime'], df_zoom['gust_ms'], color='#1f77b4', marker='o', markersize=3, label='Ground-Based Gust (m/s)', alpha=0.8)
ax2.plot(df_zoom['datetime'], df_zoom['i10fg'], color='#ff7f0e', marker='s', markersize=3, label='ERA5 Gust (m/s)', alpha=0.8)

ax2.set_title(f'Detailed Hourly Alignment Zoom-In: December 2001', fontsize=12, fontweight='bold', pad=10)
ax2.set_xlabel('Date', fontsize=11)
ax2.set_ylabel('Wind Speed (m/s)', fontsize=11)
ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
ax2.set_ylim(0, 35)

sub_gs = gs[2].subgridspec(1, 3, width_ratios=[1, 1.5, 1])
ax3 = fig.add_subplot(sub_gs[1])

ax3.scatter(merged_df['gust_ms'], merged_df['i10fg'], alpha=0.15, s=6, color='#2ca02c', label='Hourly Gust Match')

m_fit, b_fit = np.polyfit(merged_df['gust_ms'], merged_df['i10fg'], 1)
x_vals = np.linspace(0, 35, 100)
ax3.plot(x_vals, m_fit * x_vals + b_fit, color='#d62728', linewidth=2, label=f'Fit Line (slope={m_fit:.2f})')

max_val = max(merged_df['gust_ms'].max(), merged_df['i10fg'].max())
ax3.plot([0, max_val], [0, max_val], 'k--', label='1:1 Line', linewidth=1.5)

ax3.set_title(f'Correlation Scatter Plot (Pearson R = {corr:.3f})', fontsize=12, fontweight='bold', pad=10)
ax3.set_xlabel('Ground-Based Gust (m/s)', fontsize=11)
ax3.set_ylabel('ERA5 Gust (m/s)', fontsize=11)
ax3.legend(loc='upper left', frameon=True, facecolor='white')
ax3.set_xlim(0, 35)
ax3.set_ylim(0, 35)
ax3.set_aspect('equal')

plt.tight_layout()
output_plot_path = r"data/exports/gust_comparison.png"
os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)
plt.savefig(output_plot_path, dpi=150, bbox_inches='tight')
print(f"Plot successfully saved to: {output_plot_path}")
