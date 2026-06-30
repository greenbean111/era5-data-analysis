import pandas as pd
import numpy as np
import os
import glob

def process_published_alma():
    input_dir = r"data/raw/alma_published"
    output_stats_file = r"data/exports/alma_published_stats.csv"
    output_series_file = r"data/exports/alma_published_timeseries.csv"
    
    all_stats = []
    all_records = []
    
    files = sorted(glob.glob(os.path.join(input_dir, "*.met")))
    
    for file_path in files:
        filename = os.path.basename(file_path)
        # format wsb_YYMM.met
        year_val = 2000 + int(filename[4:6])
        month_val = int(filename[6:8])
        
        try:
            # Column 7: wind speed, Column 10: wind direction, Column 6: wind gust
            # Mapping based on observation:
            # 0: unix_time, 6: gust, 7: speed, 10: direction
            df = pd.read_csv(file_path, sep=r'\s+', header=None, na_values=[-999, -99.9])
            df = df.rename(columns={0: 'unix_time', 6: 'gust', 7: 'speed', 10: 'direction'})
            
            # Convert timestamp (Offset: Epoch is 1980-01-01 for this dataset)
            df['datetime'] = pd.to_datetime(df['unix_time'], unit='s', origin='1980-01-01')
            
            # Calculate components where possible
            # u (eastward), v (northward)
            # rad = np.radians(df['direction'])
            # u = -df['speed'] * np.sin(rad)
            # v = -df['speed'] * np.cos(rad)
            # Better to use mask for direction
            mask = df['direction'].notna() & df['speed'].notna()
            df.loc[mask, 'u'] = -df.loc[mask, 'speed'] * np.sin(np.radians(df.loc[mask, 'direction']))
            df.loc[mask, 'v'] = -df.loc[mask, 'speed'] * np.cos(np.radians(df.loc[mask, 'direction']))
            
            # Valid speeds for stats
            valid_speeds = df['speed'].dropna()
            
            if len(valid_speeds) > 0:
                stats = {
                    'year': year_val,
                    'month': month_val,
                    'mean': valid_speeds.mean(),
                    'std': valid_speeds.std(),
                    'max': valid_speeds.max(),
                    'gust_max': df['gust'].max(),
                    'p50': valid_speeds.quantile(0.5),
                    'p90': valid_speeds.quantile(0.9),
                    'p95': valid_speeds.quantile(0.95),
                    'p99': valid_speeds.quantile(0.99),
                    'count': len(valid_speeds)
                }
                all_stats.append(stats)
                print(f"Processed {filename}: mean={stats['mean']:.2f}")
            else:
                print(f"Skipped {filename}: No valid speed data")
            
            # Collect records for timeseries (subset)
            df_rec = df.dropna(subset=['speed'])
            all_records.append(df_rec[['datetime', 'speed', 'direction', 'gust', 'u', 'v']])
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    if all_stats:
        pd.DataFrame(all_stats).to_csv(output_stats_file, index=False)
        print(f"Saved stats to {output_stats_file}")
        
    if all_records:
        pd.concat(all_records).to_csv(output_series_file, index=False)
        print(f"Saved timeseries to {output_series_file}")
    else:
        print("No data was generated.")

if __name__ == "__main__":
    process_published_alma()
