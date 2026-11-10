import os
import glob
import pandas as pd
import numpy as np

data_dirs = [
    "grafan_aiops/real_data_validation",
    "grafan_aiops/real_data_validation_365d/run_20261013_143416/exports",
    "grafan_aiops/real_data_validation_365d/run_20261013_143621/exports"
]

print("=== SEARCHING FOR PAC & UPS CSV FILES ===")
found_files = []
for d in data_dirs:
    if os.path.exists(d):
        for f in os.listdir(d):
            if any(k in f for k in ["ME_PAC1", "ME_PAC2", "ME_UPS1"]):
                found_files.append(os.path.join(d, f))

print(f"Found {len(found_files)} files related to PAC1, PAC2, UPS1.")

# Let's group by metric and load data
pac1_supply = []
pac1_return = []
pac2_supply = []
pac2_return = []
ups1_load = []

for fpath in found_files:
    try:
        df = pd.read_csv(fpath)
        if 'timestamp' in df.columns and 'value' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Check last 5 days of data present in dataset
            max_ts = df['timestamp'].max()
            min_ts_5d = max_ts - pd.Timedelta(days=5)
            df_5d = df[df['timestamp'] >= min_ts_5d]
            
            filename = os.path.basename(fpath)
            print(f"\nFile: {filename}")
            print(f"  Total rows: {len(df)}, Last 5d rows: {len(df_5d)}")
            print(f"  Time range: {df['timestamp'].min()} to {max_ts}")
            print(f"  Value stats (last 5d): min={df_5d['value'].min()}, max={df_5d['value'].max()}, mean={df_5d['value'].mean():.2f}")
            
            if 'supply.temp.c' in filename:
                if 'ME_PAC1' in filename:
                    pac1_supply.append(df_5d)
                elif 'ME_PAC2' in filename:
                    pac2_supply.append(df_5d)
            elif 'return.temp.c' in filename:
                if 'ME_PAC1' in filename:
                    pac1_return.append(df_5d)
                elif 'ME_PAC2' in filename:
                    pac2_return.append(df_5d)
            elif 'output.load' in filename:
                if 'ME_UPS1' in filename:
                    ups1_load.append(df_5d)
    except Exception as e:
        print(f"Error reading {fpath}: {e}")

print("\n=== TEMPERATURE DELTA ANALYSIS (PAC1 & PAC2) ===")
def analyze_pac(name, supplies, returns):
    print(f"\n--- {name} ---")
    if not supplies or not returns:
        print("Missing supply or return data.")
        return
    s_df = pd.concat(supplies).sort_values('timestamp').drop_duplicates('timestamp')
    r_df = pd.concat(returns).sort_values('timestamp').drop_duplicates('timestamp')
    
    merged = pd.merge_asof(r_df.sort_values('timestamp'), s_df.sort_values('timestamp'), on='timestamp', suffixes=('_return', '_supply'), tolerance=pd.Timedelta('5min'))
    merged = merged.dropna(subset=['value_return', 'value_supply'])
    
    if len(merged) > 0:
        merged['delta_t'] = merged['value_return'] - merged['value_supply']
        print(f"Merged samples: {len(merged)}")
        print(f"Supply Temp: min={merged['value_supply'].min():.1f}, max={merged['value_supply'].max():.1f}, mean={merged['value_supply'].mean():.1f}")
        print(f"Return Temp: min={merged['value_return'].min():.1f}, max={merged['value_return'].max():.1f}, mean={merged['value_return'].mean():.1f}")
        print(f"Delta T (Return - Supply): min={merged['delta_t'].min():.1f}, max={merged['delta_t'].max():.1f}, mean={merged['delta_t'].mean():.1f}")
        
        # Check condition where supply ~16 and return ~36 (delta >= 18 or similar)
        high_delta = merged[merged['delta_t'] >= 18]
        print(f"Samples with Delta T >= 18°C (e.g. supply ~16°C, return >=34°C): {len(high_delta)}")
        if len(high_delta) > 0:
            print("Sample high delta instances:")
            print(high_delta[['timestamp', 'value_return', 'value_supply', 'delta_t']].head(5))
    else:
        print("No overlapping timestamp data found between supply and return.")

analyze_pac("PAC1", pac1_supply, pac1_return)
analyze_pac("PAC2", pac2_supply, pac2_return)
