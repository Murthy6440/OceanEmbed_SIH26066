"""
OceanEmbed SIH26066 - REAL Argo float data loader (FULL INDIAN OCEAN REGION)
"""
import time
import numpy as np

try:
    from argopy import DataFetcher
except ImportError as e:
    raise ImportError(
        "argopy is required. Install with:\n"
        '    pip install argopy "erddapy<2.2" "numpy<2" "scipy<1.13"'
    ) from e

LAT_MIN, LAT_MAX = -20.0, 30.0
LON_MIN, LON_MAX = 30.0, 100.0
DEPTH_MIN, DEPTH_MAX = 0.0, 1000.0

# New feature set uses satellite-derived surface observations + location/depth
REAL_FEATURE_NAMES = [
    "sst",
    "sss",
    "ssh",
    "u_curr",
    "v_curr",
    "u_wind",
    "v_wind",
    "depth",
    "lat_norm",
    "lon_norm",
]
REAL_TARGET_NAMES = ["temperature", "salinity"]

YEARS = [2023]


def normalize_latlon(lat, lon):
    lat_n = (np.asarray(lat, dtype=float) - LAT_MIN) / (LAT_MAX - LAT_MIN)
    lon_n = (np.asarray(lon, dtype=float) - LON_MIN) / (LON_MAX - LON_MIN)
    return lat_n, lon_n


def _month_ranges(years):
    ranges = []
    for y in years:
        for m in range(1, 13):
            start = f"{y}-{m:02d}-01"
            end_month = m + 1
            end_year = y
            if end_month > 12:
                end_month = 1
                end_year = y + 1
            end = f"{end_year}-{end_month:02d}-01"
            ranges.append((start, end))
    return ranges


def fetch_month(date_start, date_end, pres_range=(0, 1000), retries=2):
    fetcher = DataFetcher(mode="standard", src="erddap")
    last_err = None
    for attempt in range(retries + 1):
        try:
            ds = fetcher.region([
                LON_MIN, LON_MAX, LAT_MIN, LAT_MAX,
                pres_range[0], pres_range[1],
                date_start, date_end,
            ]).load().data
            return ds
        except Exception as e:
            last_err = e
            print(f"    attempt {attempt+1} failed for {date_start}..{date_end}: {e}")
            time.sleep(3)
    print(f"    giving up on {date_start}..{date_end} after {retries+1} attempts (last error: {last_err})")
    return None


from satellite_data_loader import sample_satellite_features


def build_rows_from_dataset(ds, min_levels=3):
    if ds is None:
        return np.empty((0, 5), dtype=np.float32), np.empty((0, 2), dtype=np.float32), np.empty((0,), dtype="datetime64[ns]")

    df = ds.to_dataframe().reset_index()
    df = df.dropna(subset=["TEMP", "PSAL", "PRES", "LATITUDE", "LONGITUDE"])
    df = df[(df["PRES"] >= DEPTH_MIN) & (df["PRES"] <= DEPTH_MAX)]
    if len(df) == 0:
        return np.empty((0, 5), dtype=np.float32), np.empty((0, 2), dtype=np.float32)

    group_cols = ["N_PROF"] if "N_PROF" in df.columns else ["LATITUDE", "LONGITUDE", "TIME"]

    X_rows, y_rows, date_rows = [], [], []
    kept_profiles = 0
    dropped_profiles = 0
    kept_rows = 0
    dropped_rows = 0
    for _, g in df.groupby(group_cols):
        g = g.sort_values("PRES")
        if len(g) < min_levels:
            continue
        surf = g.iloc[0]
        # attempt to sample satellite features at profile location/time
        # capture the profile timestamp (surf["TIME"]) for later satellite matching
        try:
            profile_time = np.datetime64(surf["TIME"])
        except Exception:
            # fall back to string; will be converted when saving
            profile_time = str(surf["TIME"]) if "TIME" in surf else None

        sat = sample_satellite_features(surf["LATITUDE"], surf["LONGITUDE"], surf["TIME"])
        if sat is None:
            dropped_profiles += 1
            dropped_rows += len(g)
            continue
        kept_profiles += 1
        kept_rows += len(g)
        sst, sss, ssh, u_curr, v_curr, u_wind, v_wind = sat
        lat_n, lon_n = normalize_latlon(surf["LATITUDE"], surf["LONGITUDE"])
        for _, row in g.iterrows():
            X_rows.append([
                sst,
                sss,
                ssh,
                u_curr,
                v_curr,
                u_wind,
                v_wind,
                row["PRES"],
                lat_n,
                lon_n,
            ])
            y_rows.append([row["TEMP"], row["PSAL"]])
            date_rows.append(profile_time)

    X = np.array(X_rows, dtype=np.float32) if X_rows else np.empty((0, len(REAL_FEATURE_NAMES)), dtype=np.float32)
    y = np.array(y_rows, dtype=np.float32) if y_rows else np.empty((0, 2), dtype=np.float32)
    dates = np.array(date_rows, dtype="datetime64[ns]") if date_rows else np.empty((0,), dtype="datetime64[ns]")

    print(f"Profiles kept: {kept_profiles}, profiles dropped (no satellite match): {dropped_profiles}")
    print(f"Rows kept: {len(X)}, rows dropped due to missing satellite: {dropped_rows}")
    return X, y, dates


if __name__ == "__main__":
    print(f"Fetching REAL Argo profiles across the Indian Ocean Region "
          f"({LAT_MIN}-{LAT_MAX}N, {LON_MIN}-{LON_MAX}E) in monthly chunks...")

    all_X, all_y, all_dates = [], [], []
    for start, end in _month_ranges(YEARS):
        print(f"  fetching {start} .. {end} ...")
        ds = fetch_month(start, end)
        X, y, dates = build_rows_from_dataset(ds)
        print(f"    -> {len(X)} rows")
        if len(X) > 0:
            all_X.append(X)
            all_y.append(y)
            all_dates.append(dates)
        if all_X:
            np.save("argo_X_full_india.npy", np.concatenate(all_X, axis=0))
            np.save("argo_y_full_india.npy", np.concatenate(all_y, axis=0))
            # save dates in the same row order
            np.save("argo_dates_full_india.npy", np.concatenate(all_dates, axis=0))

    if all_X:
        X_final = np.concatenate(all_X, axis=0)
        y_final = np.concatenate(all_y, axis=0)
        dates_final = np.concatenate(all_dates, axis=0)
        print(f"\nDONE. Built {len(X_final)} REAL training rows from real Argo floats across the Indian Ocean Region.")
        print("Saved to argo_X_full_india.npy / argo_y_full_india.npy / argo_dates_full_india.npy")
    else:
        print("\nNo data was fetched successfully - check errors above.")