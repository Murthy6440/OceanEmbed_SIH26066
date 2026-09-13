"""
Test script for fetching OISST SST and matching to a small Argo subset.

Usage: python test_sst_merge.py

This script loads the first N rows from `argo_X_full_india_clean.npy`,
reconstructs lat/lon in degrees from normalized columns, assigns a test
date (fallback if no dates are available in the Argo arrays), fetches
OISST for the bounding box and date, matches SST to each row and prints
the first 10 results for manual inspection.

Note: NOAA THREDDS/OPeNDAP access is public; no API key should be needed.
If the fetch fails due to network or server issues, update the URL logic in
`satellite_data_loader.fetch_oisst_sst` to point to an ERDDAP/OPeNDAP endpoint
available in your environment.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from satellite_data_loader import fetch_oisst_sst, match_sst_to_argo
from argo_data_loader_full_india import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX


def main():
    # Load the v2 Argo arrays (with per-row dates) produced by fetch_argo_v2_jan2023.py
    X = np.load("argo_X_v2.npy")
    y = np.load("argo_y_v2.npy")
    dates = np.load("argo_dates_v2.npy")

    n = min(5000, len(X))
    if n == 0:
        print("No Argo data found in argo_X_v2.npy")
        return

    X_sub = X[:n]
    dates_sub = dates[:n]

    # columns: [sst, sss, ssh, u_curr, v_curr, u_wind, v_wind, depth, lat_norm, lon_norm]
    lat_norm = X_sub[:, 8]
    lon_norm = X_sub[:, 9]
    lat = lat_norm * (LAT_MAX - LAT_MIN) + LAT_MIN
    lon = lon_norm * (LON_MAX - LON_MIN) + LON_MIN

    df = pd.DataFrame({
        "LATITUDE": lat,
        "LONGITUDE": lon,
        "TIME": [str(t) for t in dates_sub],
        "ARGO_SURF_TEMP": X_sub[:, 0],
    })

    # Fetch OISST for the bounding box and small date window around assigned_date
    date_start = (assigned_date - timedelta(days=1)).date().isoformat()
    date_end = (assigned_date + timedelta(days=2)).date().isoformat()
    print(f"Fetching OISST SST for bbox {lat.min():.2f}:{lat.max():.2f}N, {lon.min():.2f}:{lon.max():.2f}E for {date_start}..{date_end} ...")
    try:
        sst_da = fetch_oisst_sst(lat.min(), lat.max(), lon.min(), lon.max(), date_start, date_end)
    except Exception as e:
        print("Failed to fetch OISST SST:", e)
        return

    print("OISST fetched; matching to Argo subset using real per-row dates...")
    matched = match_sst_to_argo(df, sst_da)

    print("First 10 matches (lat, lon, date, matched_sst, argo_surface_temp):")
    for i in range(min(10, len(df))):
        print(
            f"{i}: {df.LATITUDE.iloc[i]:.3f}, {df.LONGITUDE.iloc[i]:.3f}, {df.TIME.iloc[i]} ->",
            f"matched_sst={matched.iloc[i]:.3f}, argo_surf={df.ARGO_SURF_TEMP.iloc[i]:.3f}",
        )


if __name__ == "__main__":
    main()
