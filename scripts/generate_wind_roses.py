import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Create output directories
os.makedirs("data/exports/diurnal_nocturnal_wind_roses/published", exist_ok=True)
os.makedirs("data/exports/diurnal_nocturnal_wind_roses/era5", exist_ok=True)

# Month names for titles
MONTH_NAMES = {
    '01': 'January',  '02': 'February', '03': 'March',
    '04': 'April',    '05': 'May',       '06': 'June',
    '07': 'July',     '08': 'August',    '09': 'September',
    '10': 'October',  '11': 'November',  '12': 'December'
}
YEAR_MAP = {'01': '2001', '02': '2002'}

# ------------------------------------------------------------
# 1. GENERATE ROSES FOR PUBLISHED GROUND DATA
# ------------------------------------------------------------
print("=== Processing Published Ground Data ===")

COL_SPEED     = 7    # wind speed in m/s
COL_DIRECTION = 10   # wind direction in degrees
COL_DIR_STD   = 11   # wind direction standard deviation
MISSING       = -999
DIR_STD_MAX   = 100

def load_met_with_hours(filepath):
    """
    Load an ALMA .met file and return clean arrays with UTC hours.
    """
    spd_col = []
    drn_col = []
    std_col = []
    hour_col = []
    
    with open(filepath, 'r') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) <= max(COL_SPEED, COL_DIRECTION, COL_DIR_STD):
                continue
            try:
                unix_time = float(parts[0])
                spd = float(parts[COL_SPEED])
                drn = float(parts[COL_DIRECTION])
                std = float(parts[COL_DIR_STD])
            except ValueError:
                continue
            
            # Convert timestamp to UTC hour
            dt = pd.to_datetime(unix_time, unit='s', origin='1980-01-01')
            hour = dt.hour
            
            spd_col.append(spd)
            drn_col.append(drn)
            std_col.append(std)
            hour_col.append(hour)

    if not spd_col:
        return np.array([]), np.array([]), np.array([])

    spd_arr = np.array(spd_col, dtype=float)
    drn_arr = np.array(drn_col, dtype=float)
    std_arr = np.array(std_col, dtype=float)
    hour_arr = np.array(hour_col, dtype=int)

    # Filter for valid speed, valid direction, and reliable direction std
    valid_rose = (
        (spd_arr != MISSING) & (spd_arr >= 0) &
        (drn_arr != MISSING) & (drn_arr >= 0) & (drn_arr <= 360) &
        (std_arr < DIR_STD_MAX)
    )
    
    return spd_arr[valid_rose], drn_arr[valid_rose], hour_arr[valid_rose]

# Load files
met_files = sorted(glob.glob("data/raw/alma_published/wsb_*.met"))
print(f"Found {len(met_files)} .met files.")

# Pre-load to find global vmax
all_speeds = []
monthly_data_published = []

for filepath in met_files:
    basename = os.path.basename(filepath)
    code = basename.replace('wsb_', '').replace('.met', '')
    yr_code = code[:2]
    mo_code = code[2:]
    year = YEAR_MAP.get(yr_code, f"20{yr_code}")
    month = MONTH_NAMES.get(mo_code, mo_code)
    
    speed, direction, hour = load_met_with_hours(filepath)
    if len(speed) > 0:
        all_speeds.append(speed)
    
    monthly_data_published.append({
        'basename': basename,
        'year': year,
        'month': month,
        'mo_code': mo_code,
        'speed': speed,
        'direction': direction,
        'hour': hour
    })

global_vmax_pub = np.nanmax(np.concatenate(all_speeds)) if all_speeds else 25.0
print(f"Global max speed in published rose data: {global_vmax_pub:.2f} m/s")

# Plot monthly diurnal & nocturnal comparisons for published data
for mdata in monthly_data_published:
    year = mdata['year']
    month = mdata['month']
    speed = mdata['speed']
    direction = mdata['direction']
    hour = mdata['hour']
    basename = mdata['basename']
    
    if len(speed) == 0:
        print(f"  [SKIP] No data for {month} {year}")
        continue
        
    # Split diurnal (1 AM - 11 AM UTC) and nocturnal (11 AM - 1 AM UTC)
    diurnal_mask = (hour >= 1) & (hour <= 10)
    nocturnal_mask = (hour >= 11) | (hour == 0)
    
    spd_diurnal, dir_diurnal = speed[diurnal_mask], direction[diurnal_mask]
    spd_nocturnal, dir_nocturnal = speed[nocturnal_mask], direction[nocturnal_mask]
    
    # Generate side-by-side plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), subplot_kw={'polar': True})
    
    # Style helper
    def style_ax(ax, title, spd, drn):
        if len(spd) == 0:
            ax.text(0.5, 0.5, "No Data", transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20, fontsize=12, fontweight='bold')
            return None
        
        theta = np.radians(drn)
        sc = ax.scatter(theta, spd, c=spd, cmap='viridis', vmin=0, vmax=global_vmax_pub, s=8, alpha=0.7, linewidths=0)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.set_rlabel_position(45)
        ax.set_title(f"{title}\nn={len(spd):,} | mean={np.mean(spd):.1f} m/s | max={np.max(spd):.1f} m/s", pad=20, fontsize=11, fontweight='bold')
        return sc

    sc1 = style_ax(ax1, "Diurnal (1 AM - 11 AM UTC)", spd_diurnal, dir_diurnal)
    sc2 = style_ax(ax2, "Nocturnal (11 AM - 1 AM UTC)", spd_nocturnal, dir_nocturnal)
    
    fig.suptitle(f"ALMA Ground Station Wind Rose: {month} {year}", fontsize=14, fontweight='bold', y=0.98)
    
    # Common colorbar
    fig.subplots_adjust(bottom=0.15, wspace=0.3)
    cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.03])
    cbar = fig.colorbar(sc2 if sc2 is not None else sc1, cax=cbar_ax, orientation='horizontal')
    cbar.set_label("Wind Speed (m/s)", fontsize=10)
    
    out_filename = basename.replace('.met', '_diurnal_nocturnal.png')
    out_path = os.path.join("data/exports/diurnal_nocturnal_wind_roses/published", out_filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated comparison plot: {out_filename}")

# ------------------------------------------------------------
# 2. GENERATE ROSES FOR ERA5 DATA
# ------------------------------------------------------------
print("\n=== Processing ERA5 Data ===")
ALMA_LAT = -23.029
ALMA_LON = -67.755

chile_files = sorted(glob.glob("data/raw/chile/chile_*.nc"))

all_era5_speeds = []
monthly_data_era5 = []

for f in chile_files:
    basename = os.path.basename(f)
    # chile_2001-01.nc
    parts = basename.replace('chile_', '').replace('.nc', '').split('-')
    year = parts[0]
    month_code = parts[1]
    month_name = MONTH_NAMES.get(month_code, month_code)
    
    with xr.open_dataset(f) as ds:
        # Extract ALMA site coordinates
        point_ds = ds.sel(latitude=ALMA_LAT, longitude=ALMA_LON, method='nearest')
        u10 = point_ds['u10'].values
        v10 = point_ds['v10'].values
        times = pd.to_datetime(point_ds['valid_time'].values)
        
        # Calculate speed and meteorological direction
        speed = np.sqrt(u10**2 + v10**2)
        # met direction: wind from which it blows. atan2(u, v) + 180
        direction = (np.degrees(np.arctan2(u10, v10)) + 180) % 360
        hour = times.hour
        
        # Filter NaNs if any
        mask = ~np.isnan(speed) & ~np.isnan(direction)
        speed = speed[mask]
        direction = direction[mask]
        hour = hour[mask]
        
        if len(speed) > 0:
            all_era5_speeds.append(speed)
            
        monthly_data_era5.append({
            'year': year,
            'month': month_name,
            'mo_code': month_code,
            'speed': speed,
            'direction': direction,
            'hour': hour
        })

global_vmax_era5 = np.nanmax(np.concatenate(all_era5_speeds)) if all_era5_speeds else 25.0
print(f"Global max speed in ERA5 rose data: {global_vmax_era5:.2f} m/s")

# Plot monthly diurnal & nocturnal comparisons for ERA5 data
for mdata in monthly_data_era5:
    year = mdata['year']
    month = mdata['month']
    speed = mdata['speed']
    direction = mdata['direction']
    hour = mdata['hour']
    month_code = mdata['mo_code']
    
    if len(speed) == 0:
        print(f"  [SKIP] No ERA5 data for {month} {year}")
        continue
        
    diurnal_mask = (hour >= 1) & (hour <= 10)
    nocturnal_mask = (hour >= 11) | (hour == 0)
    
    spd_diurnal, dir_diurnal = speed[diurnal_mask], direction[diurnal_mask]
    spd_nocturnal, dir_nocturnal = speed[nocturnal_mask], direction[nocturnal_mask]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), subplot_kw={'polar': True})
    
    def style_ax_era5(ax, title, spd, drn):
        if len(spd) == 0:
            ax.text(0.5, 0.5, "No Data", transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20, fontsize=12, fontweight='bold')
            return None
        
        theta = np.radians(drn)
        sc = ax.scatter(theta, spd, c=spd, cmap='viridis', vmin=0, vmax=global_vmax_era5, s=8, alpha=0.7, linewidths=0)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.set_rlabel_position(45)
        ax.set_title(f"{title}\nn={len(spd):,} | mean={np.mean(spd):.1f} m/s | max={np.max(spd):.1f} m/s", pad=20, fontsize=11, fontweight='bold')
        return sc

    sc1 = style_ax_era5(ax1, "Diurnal (1 AM - 11 AM UTC)", spd_diurnal, dir_diurnal)
    sc2 = style_ax_era5(ax2, "Nocturnal (11 AM - 1 AM UTC)", spd_nocturnal, dir_nocturnal)
    
    fig.suptitle(f"ERA5 Wind Rose (ALMA Site): {month} {year}", fontsize=14, fontweight='bold', y=0.98)
    
    fig.subplots_adjust(bottom=0.15, wspace=0.3)
    cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.03])
    cbar = fig.colorbar(sc2 if sc2 is not None else sc1, cax=cbar_ax, orientation='horizontal')
    cbar.set_label("Wind Speed (m/s)", fontsize=10)
    
    out_filename = f"chile_{year}_{month_code}_diurnal_nocturnal.png"
    out_path = os.path.join("data/exports/diurnal_nocturnal_wind_roses/era5", out_filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated ERA5 comparison plot: {out_filename}")

# ------------------------------------------------------------
# 3. GENERATE COMBINED ROSES FOR ALL YEARS
# ------------------------------------------------------------
print("\n=== Processing Combined Datasets (All Years) ===")

# --- Published Ground Data Combined ---
combined_speed_pub = np.concatenate([m['speed'] for m in monthly_data_published if len(m['speed']) > 0])
combined_dir_pub = np.concatenate([m['direction'] for m in monthly_data_published if len(m['speed']) > 0])
combined_hour_pub = np.concatenate([m['hour'] for m in monthly_data_published if len(m['speed']) > 0])

diurnal_mask_pub = (combined_hour_pub >= 1) & (combined_hour_pub <= 10)
nocturnal_mask_pub = (combined_hour_pub >= 11) | (combined_hour_pub == 0)

spd_diurnal_pub, dir_diurnal_pub = combined_speed_pub[diurnal_mask_pub], combined_dir_pub[diurnal_mask_pub]
spd_nocturnal_pub, dir_nocturnal_pub = combined_speed_pub[nocturnal_mask_pub], combined_dir_pub[nocturnal_mask_pub]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), subplot_kw={'polar': True})

def style_ax_pub_comb(ax, title, spd, drn):
    theta = np.radians(drn)
    sc = ax.scatter(theta, spd, c=spd, cmap='viridis', vmin=0, vmax=global_vmax_pub, s=8, alpha=0.7, linewidths=0)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    ax.set_rlabel_position(45)
    ax.set_title(f"{title}\nn={len(spd):,} | mean={np.mean(spd):.1f} m/s | max={np.max(spd):.1f} m/s", pad=20, fontsize=11, fontweight='bold')
    return sc

sc1 = style_ax_pub_comb(ax1, "Diurnal (1 AM - 11 AM UTC)", spd_diurnal_pub, dir_diurnal_pub)
sc2 = style_ax_pub_comb(ax2, "Nocturnal (11 AM - 1 AM UTC)", spd_nocturnal_pub, dir_nocturnal_pub)

fig.suptitle("ALMA Ground Station Wind Rose: Combined Years (2001-2002)", fontsize=14, fontweight='bold', y=0.98)
fig.subplots_adjust(bottom=0.15, wspace=0.3)
cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.03])
cbar = fig.colorbar(sc2, cax=cbar_ax, orientation='horizontal')
cbar.set_label("Wind Speed (m/s)", fontsize=10)

out_path_pub_comb = os.path.join("data/exports/diurnal_nocturnal_wind_roses/published", "combined_diurnal_nocturnal.png")
plt.savefig(out_path_pub_comb, dpi=150, bbox_inches='tight')
plt.close()
print("  Generated combined published comparison plot: combined_diurnal_nocturnal.png")

# --- ERA5 Combined ---
combined_speed_era5 = np.concatenate([m['speed'] for m in monthly_data_era5 if len(m['speed']) > 0])
combined_dir_era5 = np.concatenate([m['direction'] for m in monthly_data_era5 if len(m['speed']) > 0])
combined_hour_era5 = np.concatenate([m['hour'] for m in monthly_data_era5 if len(m['speed']) > 0])

diurnal_mask_era5 = (combined_hour_era5 >= 1) & (combined_hour_era5 <= 10)
nocturnal_mask_era5 = (combined_hour_era5 >= 11) | (combined_hour_era5 == 0)

spd_diurnal_era5, dir_diurnal_era5 = combined_speed_era5[diurnal_mask_era5], combined_dir_era5[diurnal_mask_era5]
spd_nocturnal_era5, dir_nocturnal_era5 = combined_speed_era5[nocturnal_mask_era5], combined_dir_era5[nocturnal_mask_era5]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), subplot_kw={'polar': True})

def style_ax_era5_comb(ax, title, spd, drn):
    theta = np.radians(drn)
    sc = ax.scatter(theta, spd, c=spd, cmap='viridis', vmin=0, vmax=global_vmax_era5, s=8, alpha=0.7, linewidths=0)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    ax.set_rlabel_position(45)
    ax.set_title(f"{title}\nn={len(spd):,} | mean={np.mean(spd):.1f} m/s | max={np.max(spd):.1f} m/s", pad=20, fontsize=11, fontweight='bold')
    return sc

sc1 = style_ax_era5_comb(ax1, "Diurnal (1 AM - 11 AM UTC)", spd_diurnal_era5, dir_diurnal_era5)
sc2 = style_ax_era5_comb(ax2, "Nocturnal (11 AM - 1 AM UTC)", spd_nocturnal_era5, dir_nocturnal_era5)

fig.suptitle("ERA5 Wind Rose (ALMA Site): Combined Years (2001-2002)", fontsize=14, fontweight='bold', y=0.98)
fig.subplots_adjust(bottom=0.15, wspace=0.3)
cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.03])
cbar = fig.colorbar(sc2, cax=cbar_ax, orientation='horizontal')
cbar.set_label("Wind Speed (m/s)", fontsize=10)

out_path_era5_comb = os.path.join("data/exports/diurnal_nocturnal_wind_roses/era5", "combined_diurnal_nocturnal.png")
plt.savefig(out_path_era5_comb, dpi=150, bbox_inches='tight')
plt.close()
print("  Generated combined ERA5 comparison plot: combined_diurnal_nocturnal.png")

print("\n=== Wind Rose Generation Complete ===")

