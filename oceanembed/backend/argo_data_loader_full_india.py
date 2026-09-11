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

REAL_FEATURE_NAMES = ["surface_temp", "surface_sal", "depth", "lat_norm", "lon_norm"]
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


def build_rows_from_dataset(ds, min_levels=3):
    if ds is None:
        return np.empty((0, 5), dtype=np.float32), np.empty((0, 2), dtype=np.float32)

    df = ds.to_dataframe().reset_index()
    df = df.dropna(subset=["TEMP", "PSAL", "PRES", "LATITUDE", "LONGITUDE"])
    df = df[(df["PRES"] >= DEPTH_MIN) & (df["PRES"] <= DEPTH_MAX)]
    if len(df) == 0:
        return np.empty((0, 5), dtype=np.float32), np.empty((0, 2), dtype=np.float32)

    group_cols = ["N_PROF"] if "N_PROF" in df.columns else ["LATITUDE", "LONGITUDE", "TIME"]

    X_rows, y_rows = [], []
    for _, g in df.groupby(group_cols):
        g = g.sort_values("PRES")
        if len(g) < min_levels:
            continue
        surf = g.iloc[0]
        lat_n, lon_n = normalize_latlon(surf["LATITUDE"], surf["LONGITUDE"])
        for _, row in g.iterrows():
            X_rows.append([surf["TEMP"], surf["PSAL"], row["PRES"], lat_n, lon_n])
            y_rows.append([row["TEMP"], row["PSAL"]])

    X = np.array(X_rows, dtype=np.float32) if X_rows else np.empty((0, 5), dtype=np.float32)
    y = np.array(y_rows, dtype=np.float32) if y_rows else np.empty((0, 2), dtype=np.float32)
    return X, y


if __name__ == "__main__":
    print(f"Fetching REAL Argo profiles across the Indian Ocean Region "
          f"({LAT_MIN}-{LAT_MAX}N, {LON_MIN}-{LON_MAX}E) in monthly chunks...")

    all_X, all_y = [], []
    for start, end in _month_ranges(YEARS):
        print(f"  fetching {start} .. {end} ...")
        ds = fetch_month(start, end)
        X, y = build_rows_from_dataset(ds)
        print(f"    -> {len(X)} rows")
        if len(X) > 0:
            all_X.append(X)
            all_y.append(y)
        if all_X:
            np.save("argo_X_full_india.npy", np.concatenate(all_X, axis=0))
            np.save("argo_y_full_india.npy", np.concatenate(all_y, axis=0))

    if all_X:
        X_final = np.concatenate(all_X, axis=0)
        y_final = np.concatenate(all_y, axis=0)
        print(f"\nDONE. Built {len(X_final)} REAL training rows from real Argo floats across the Indian Ocean Region.")
        print("Saved to argo_X_full_india.npy / argo_y_full_india.npy")
    else:
        print("\nNo data was fetched successfully - check errors above.")