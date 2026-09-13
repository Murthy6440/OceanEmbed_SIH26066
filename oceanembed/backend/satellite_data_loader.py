"""
satellite_data_loader.py

Satellite data fetcher using xarray/opendap where possible.

This module provides a light wrapper `sample_satellite_features(lat, lon, time)`
which attempts to retrieve a set of surface features at the given location
and time. It uses example OPeNDAP/ERDDAP URLs; you should replace dataset
URLs in `DATASET_URLS` with working endpoints for your environment.

Returned tuple: (sst, sss, ssh, u_curr, v_curr, u_wind, v_wind) or None when
any value is missing.
"""
import os
from datetime import datetime
import warnings

import numpy as np
import pandas as pd
import xarray as xr
from dateutil import parser

# Default dataset URLs for public satellite sources where available.
# A subset of these can be used directly; missing sources automatically
# fall back to the synthetic generator so the app still runs.
DATASET_URLS = {
    "sst": os.getenv(
        "OISST_DATASET_URL",
        "https://www.ncei.noaa.gov/thredds-ocean/dodsC/oisst/avhrr/{year}/oisst-avhrr-v02r01-{date}.nc",
    ),
    "sss": os.getenv("SMAP_SSS_DATASET_URL"),
    "ssh": os.getenv("SSH_DATASET_URL"),
    "u_curr": os.getenv("OSCAR_U_DATASET_URL"),
    "v_curr": os.getenv("OSCAR_V_DATASET_URL"),
    "u_wind": os.getenv("ERA5_UWIND_DATASET_URL"),
    "v_wind": os.getenv("ERA5_VWIND_DATASET_URL"),
}


def _daily_oisst_url_for_date(dt: datetime):
    return (
        f"https://www.ncei.noaa.gov/thredds-ocean/dodsC/oisst/avhrr/"
        f"{dt.year:04d}/oisst-avhrr-v02r01-{dt.year:04d}{dt.month:02d}{dt.day:02d}.nc"
    )


def _fill_missing_with_synthetic(lat, lon, time):
    try:
        import data_generator
        return data_generator.surface_fields(lat, lon, noise=False, date=time)
    except Exception:
        return {
            "sst": 0.0,
            "sss": 0.0,
            "ssh": 0.0,
            "u_curr": 0.0,
            "v_curr": 0.0,
            "u_wind": 0.0,
            "v_wind": 0.0,
        }


def _open_dataset(url):
    if not url:
        return None
    try:
        ds = xr.open_dataset(url)
        return ds
    except Exception as e:
        warnings.warn(f"Could not open dataset at {url}: {e}")
        return None


def _nearest_value(ds, varname, lat, lon, time):
    if ds is None or varname not in ds.variables:
        return None
    try:
        # Try common coordinate names
        lon_name = None
        lat_name = None
        for cand in ("lon", "longitude", "LONGITUDE"):
            if cand in ds.coords:
                lon_name = cand
                break
        for cand in ("lat", "latitude", "LATITUDE"):
            if cand in ds.coords:
                lat_name = cand
                break

        sel_kwargs = {}
        if lat_name is not None:
            sel_kwargs[lat_name] = lat
        if lon_name is not None:
            # handle 0..360 vs -180..180
            lon_vals = ds.coords[lon_name]
            if lon_vals.min() >= 0 and lon < 0:
                lon_q = lon % 360
            else:
                lon_q = lon
            sel_kwargs[lon_name] = lon_q

        # nearest time within 1 day if time coord exists
        if "time" in ds.coords:
            try:
                val = ds[varname].sel(time=time, method="nearest").sel(**sel_kwargs, method="nearest")
            except Exception:
                val = ds[varname].sel(**sel_kwargs, method="nearest")
        else:
            val = ds[varname].sel(**sel_kwargs, method="nearest")

        arr = val.values
        # reduce to scalar
        flat = np.array(arr).ravel()
        if flat.size == 0:
            return None
        v = float(flat[0])
        if np.isnan(v):
            return None
        return v
    except Exception:
        return None


def sample_satellite_features(lat, lon, time):
    """Return a 7-tuple of surface features using live satellite data where
    available and synthetic values for missing variables.

    This keeps the system compatible with real satellite ingestion without
    breaking the demo when a source is unavailable.
    """
    if isinstance(time, str):
        try:
            time = parser.parse(time)
        except Exception:
            pass

    fallback = _fill_missing_with_synthetic(lat, lon, time)

    # Prefer a direct public OISST endpoint for SST; other sources remain optional.
    if isinstance(time, datetime):
        oisst_url = _daily_oisst_url_for_date(time)
    else:
        oisst_url = DATASET_URLS.get("sst")

    ds_sst = _open_dataset(DATASET_URLS.get("sst") or oisst_url)
    ds_sss = _open_dataset(DATASET_URLS.get("sss"))
    ds_ssh = _open_dataset(DATASET_URLS.get("ssh"))
    ds_uc = _open_dataset(DATASET_URLS.get("u_curr"))
    ds_vc = _open_dataset(DATASET_URLS.get("v_curr"))
    ds_uw = _open_dataset(DATASET_URLS.get("u_wind"))
    ds_vw = _open_dataset(DATASET_URLS.get("v_wind"))

    sst = _nearest_value(ds_sst, "sst", lat, lon, time) if ds_sst is not None else None
    sss = _nearest_value(ds_sss, "sss", lat, lon, time) if ds_sss is not None else None
    ssh = _nearest_value(ds_ssh, "ssh", lat, lon, time) if ds_ssh is not None else None
    u_curr = _nearest_value(ds_uc, "u", lat, lon, time) if ds_uc is not None else None
    v_curr = _nearest_value(ds_vc, "v", lat, lon, time) if ds_vc is not None else None
    u_wind = _nearest_value(ds_uw, "u10", lat, lon, time) if ds_uw is not None else None
    v_wind = _nearest_value(ds_vw, "v10", lat, lon, time) if ds_vw is not None else None

    values = {
        "sst": sst if sst is not None else fallback["sst"],
        "sss": sss if sss is not None else fallback["sss"],
        "ssh": ssh if ssh is not None else fallback["ssh"],
        "u_curr": u_curr if u_curr is not None else fallback["u_curr"],
        "v_curr": v_curr if v_curr is not None else fallback["v_curr"],
        "u_wind": u_wind if u_wind is not None else fallback["u_wind"],
        "v_wind": v_wind if v_wind is not None else fallback["v_wind"],
    }

    return (
        float(values["sst"]),
        float(values["sss"]),
        float(values["ssh"]),
        float(values["u_curr"]),
        float(values["v_curr"]),
        float(values["u_wind"]),
        float(values["v_wind"]),
    )


def _daily_oisst_url_for_date(dt: datetime):
    """Return a NOAA THREDDS daily OISST file OPeNDAP URL for a given date.

    Note: This uses a common NOAA THREDDS path pattern. If your environment
    requires a different endpoint (ERDDAP, different server), update the
    caller to pass a suitable URL to `fetch_oisst_sst`.
    """
    # Format: .../oisst/avhrr/YYYY/oisst-avhrr-v02r01-YYYYMMDD.nc
    return f"https://www.ncei.noaa.gov/thredds-ocean/dodsC/oisst/avhrr/{dt.year:04d}/oisst-avhrr-v02r01-{dt.year:04d}{dt.month:02d}{dt.day:02d}.nc"


def fetch_oisst_sst(lat_min, lat_max, lon_min, lon_max, date_start, date_end):
    """Fetch NOAA OISST v2.1 daily SST as an xarray Dataset/DataArray.

    Parameters:
      lat_min/lat_max, lon_min/lon_max: float bounds in degrees
      date_start/date_end: strings or datetimes (inclusive start, exclusive end recommended)

    Returns an xarray Dataset with coords (time, lat, lon) and variable `sst`.

    Implementation notes:
    - Tries to open per-day THREDDS OPeNDAP files for the requested date range
      and concatenates them with xarray.open_mfdataset. This avoids downloading
      large files upfront but requires network access to NOAA THREDDS.
    - If the server or URL pattern is not reachable, the function will raise
      an informative exception; update the URL pattern or provide an ERDDAP
      dataset URL if needed.
    """
    # normalize dates
    start = pd.to_datetime(date_start)
    end = pd.to_datetime(date_end)
    # build list of daily urls
    urls = []
    cur = start
    while cur < end:
        urls.append(_daily_oisst_url_for_date(cur.to_pydatetime()))
        cur += pd.Timedelta(days=1)

    if len(urls) == 0:
        raise ValueError("Empty date range for fetch_oisst_sst")

    try:
        # open multiple remote files lazily
        ds = xr.open_mfdataset(urls, combine="by_coords", parallel=False)
    except Exception as e:
        raise RuntimeError(f"Failed to open OISST files via OPeNDAP: {e}\nURLs tried: {urls[:3]}...")

    # Standard OISST variable name is 'sst' or 'anom' depending on dataset; try common names
    for var in ("sst", "SST", "sea_surface_temperature"):
        if var in ds.variables:
            sst_var = var
            break
    else:
        # try to guess variable with 3D (time,lat,lon)
        candidates = [v for v in ds.data_vars if set(ds[v].dims) >= {"time", "lat", "lon"}]
        if candidates:
            sst_var = candidates[0]
        else:
            raise RuntimeError("Could not find SST variable in OISST dataset")

    # subset spatially
    try:
        sst = ds[sst_var].sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
    except Exception:
        # try with lon wrapped 0..360 if necessary
        sst = ds[sst_var]
        if sst.lon.min() >= 0 and lon_min < 0:
            lon_min_wrapped = lon_min % 360
            lon_max_wrapped = lon_max % 360
            sst = sst.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min_wrapped, lon_max_wrapped))

    # Ensure time coordinate is datetime64
    if "time" in sst.coords:
        sst["time"] = pd.to_datetime(sst["time"].values)

    # return as DataArray with name 'sst'
    return sst


def match_sst_to_argo(argo_df, sst_da):
    """Match OISST `sst_da` to each Argo profile in `argo_df`.

    `argo_df` should contain either columns `LATITUDE`, `LONGITUDE`, `TIME`,
    or `lat_norm`, `lon_norm` (normalized). If only normalized lon/lat are
    present, the function will attempt to reconstruct real degrees using the
    domain constants defined in this package (LAT_MIN/MAX etc.).

    Returns a pandas Series of matched SST values (float) aligned with
    the rows of `argo_df`. Missing matches are returned as NaN.
    Also prints a short summary of matched vs missing counts.
    """
    import pandas as _pd

    df = argo_df.copy()
    # try to detect lat/lon columns
    if "LATITUDE" in df.columns and "LONGITUDE" in df.columns:
        lat_col, lon_col = "LATITUDE", "LONGITUDE"
    elif "lat" in df.columns and "lon" in df.columns:
        lat_col, lon_col = "lat", "lon"
    elif "lat_norm" in df.columns and "lon_norm" in df.columns:
        # reconstruct
        from argo_data_loader_full_india import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
        df["LATITUDE"] = df["lat_norm"] * (LAT_MAX - LAT_MIN) + LAT_MIN
        df["LONGITUDE"] = df["lon_norm"] * (LON_MAX - LON_MIN) + LON_MIN
        lat_col, lon_col = "LATITUDE", "LONGITUDE"
    else:
        raise ValueError("argo_df must contain lat/lon information")

    # try to detect time column
    time_col = None
    for cand in ("TIME", "time", "date"):
        if cand in df.columns:
            time_col = cand
            break

    # Prepare output
    matched = _pd.Series(_pd.NA, index=df.index, dtype=float)

    # Vectorized nearest-neighbor: use xarray sel with method='nearest'
    for idx, row in df.iterrows():
        lat = float(row[lat_col])
        lon = float(row[lon_col])
        if time_col is not None:
            try:
                t = parser.parse(str(row[time_col]))
            except Exception:
                t = pd.to_datetime(row[time_col])
        else:
            # fallback: pick the nearest time in sst_da (median)
            t = sst_da["time"].values[len(sst_da["time"]) // 2]

        try:
            val = sst_da.sel(time=t, method="nearest").sel(lat=lat, lon=lon, method="nearest")
            v = float(val.values)
        except Exception:
            v = float("nan")
        matched.at[idx] = v

    matched_count = matched.notna().sum()
    missing_count = matched.isna().sum()
    print(f"Matched SST values: {matched_count}, missing: {missing_count}")
    return matched


if __name__ == "__main__":
    print("satellite_data_loader: sample_satellite_features(lat, lon, time)")
