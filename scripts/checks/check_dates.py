import pandas as pd
import glob

for pac in ["PAC1", "PAC2"]:
    path = f"grafan_aiops/real_data_validation/ME_{pac}_return.temp.c.csv"
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"\n{pac} return.temp.c time range in CSV:")
    print("  Min:", df['timestamp'].min())
    print("  Max:", df['timestamp'].max())
    print("  Max values by date:")
    print(df.groupby(df['timestamp'].dt.date)['value'].max())
