"""
Fetch Argo-derived training rows for January 2023 and save X/y/dates as v2 files.

This script will fetch Argo profiles for the domain and date range defined in
`argo_data_loader_full_india.py` but only for January 2023. It will build rows
using the existing `build_rows_from_dataset` function (which now returns dates)
and save the outputs as `argo_X_v2.npy`, `argo_y_v2.npy`, `argo_dates_v2.npy`.

This script will NOT overwrite existing original files and is safe to run.
Run from the repository root:

    python oceanembed/backend/fetch_argo_v2_jan2023.py

Note: fetching from ERDDAP/argopy may take several minutes depending on
network speed and remote server rate limits.
"""
from argo_data_loader_full_india import fetch_month, build_rows_from_dataset, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
import numpy as np
from datetime import datetime


def main():
    date_start = "2023-01-01"
    date_end = "2023-02-01"
    print(f"Fetching Argo data for {date_start} .. {date_end} (January 2023) ...")
    ds = fetch_month(date_start, date_end)
    if ds is None:
        print("No dataset returned from fetch_month; aborting.")
        return

    X, y, dates = build_rows_from_dataset(ds)
    print(f"Built {len(X)} rows for January 2023")
    if len(X) == 0:
        print("No rows to save.")
        return

    # Save as v2 files to avoid overwriting originals
    np.save("argo_X_v2.npy", X)
    np.save("argo_y_v2.npy", y)
    np.save("argo_dates_v2.npy", dates)

    # Print sample rows (lat, lon, date, depth, temperature, salinity)
    # reconstruct lat/lon from normalized columns
    lat_norm = X[:, -2]
    lon_norm = X[:, -1]
    lats = lat_norm * (LAT_MAX - LAT_MIN) + LAT_MIN
    lons = lon_norm * (LON_MAX - LON_MIN) + LON_MIN
    depths = X[:, 7]
    temps = y[:, 0]
    sals = y[:, 1]

    print("First 10 sample rows:")
    for i in range(min(10, len(X))):
        print(f"{i}: lat={lats[i]:.4f}, lon={lons[i]:.4f}, date={str(dates[i])}, depth={depths[i]:.1f}, temp={temps[i]:.3f}, sal={sals[i]:.3f}")


if __name__ == "__main__":
    main()
