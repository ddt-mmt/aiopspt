import pandas as pd

for pac in ["PAC1", "PAC2"]:
    df_r = pd.read_csv(f"grafan_aiops/real_data_validation/ME_{pac}_return.temp.c.csv")
    df_r['timestamp'] = pd.to_datetime(df_r['timestamp'])
    df_r['value'] = pd.to_numeric(df_r['value'], errors='coerce')
    
    print(f"\n=== {pac} Return Temp Quantiles ===")
    print(df_r['value'].quantile([0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0]))
    
    # Check values around 30-40C vs > 50C
    normal_range = df_r[(df_r['value'] >= 25) & (df_r['value'] <= 40)]
    high_range = df_r[df_r['value'] > 50]
    print(f"  Values between 25-40°C: {len(normal_range)} rows")
    print(f"  Values > 50°C: {len(high_range)} rows")
    if len(normal_range) > 0:
        print(f"  Normal range stats: min={normal_range['value'].min()}, max={normal_range['value'].max()}, mean={normal_range['value'].mean():.1f}")
