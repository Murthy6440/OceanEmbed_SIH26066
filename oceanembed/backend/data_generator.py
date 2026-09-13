"""
OceanEmbed SIH26066 - Synthetic Ocean Data Generator
=====================================================
*** EVERYTHING PRODUCED BY THIS MODULE IS 100% SYNTHETIC / DEMO DATA ***

Values are generated from simple parametric formulas chosen to *resemble*
plausible ocean fields (a thermocline-like shape with depth, monsoon-like
wind patterns, smooth eddy-like current fields, etc.) purely so that the
OceanEmbed prototype has something to train against and demo end-to-end.

This is NOT derived from satellite, Argo float, or any other real
observational dataset, and it carries NO real predictive skill. Do not
present anything produced from this module as real oceanographic data.
"""

import numpy as np
from datetime import datetime

# ---------------------------------------------------------------------------
# Domain definition (matches the SIH26066 problem-statement region: North
# Indian Ocean, Arabian Sea + Bay of Bengal box)
# ---------------------------------------------------------------------------
LAT_MIN, LAT_MAX = 5.0, 30.0        # deg N
LON_MIN, LON_MAX = 45.0, 105.0      # deg E
DEPTH_MIN, DEPTH_MAX = 0.0, 1000.0  # m

DEPTH_LEVELS = [0, 10, 20, 30, 50, 75, 100, 125, 150, 200,
                250, 300, 400, 500, 600, 700, 800, 900, 1000]

FEATURE_NAMES = ["sst", "sss", "ssh", "u_curr", "v_curr",
                  "u_wind", "v_wind", "depth", "lat_norm", "lon_norm"]
TARGET_NAMES = ["temperature", "salinity"]

_DEFAULT_SEED = 42


def normalize_latlon(lat, lon):
    """Map lat/lon into [0, 1] over the domain box."""
    lat_n = (np.asarray(lat, dtype=float) - LAT_MIN) / (LAT_MAX - LAT_MIN)
    lon_n = (np.asarray(lon, dtype=float) - LON_MIN) / (LON_MAX - LON_MIN)
    return lat_n, lon_n


def surface_fields(lat, lon, rng=None, noise=True, date=None):
    """
    Generate SYNTHETIC surface fields at given lat/lon (scalars or arrays
    of matching shape). Returns a dict of numpy arrays / scalars for:
      sst (deg C), sss (psu), ssh/sla (m),
      u_curr, v_curr (m/s surface currents), u_wind, v_wind (m/s winds)

    When a datetime is supplied, the synthetic surface field includes a small
    seasonal and diurnal signal so the prototype visibly changes with date/time.
    """
    if rng is None:
        rng = np.random.default_rng(_DEFAULT_SEED)

    lat_n, lon_n = normalize_latlon(lat, lon)
    shape = np.shape(lat_n)

    if date is None:
        date = datetime.utcnow()

    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace("Z", "+00:00"))

    doy = date.timetuple().tm_yday
    hour = date.hour + date.minute / 60.0 + date.second / 3600.0
    season_cycle = np.sin(2 * np.pi * (doy - 80) / 365.0)
    diurnal_cycle = np.sin(2 * np.pi * (hour - 12) / 24.0)

    def eps(scale):
        return rng.normal(0, scale, size=shape) if noise else 0.0

    sst = 29.5 - 3.0 * lat_n + 0.8 * np.sin(2 * np.pi * lon_n) + 0.9 * season_cycle + 0.25 * diurnal_cycle + eps(0.3)
    sss = 35.3 - 1.8 * lon_n + 0.4 * np.sin(2 * np.pi * lat_n) - 0.15 * season_cycle + eps(0.15)
    ssh = 0.30 * np.sin(4 * np.pi * lat_n) * np.cos(3 * np.pi * lon_n) + 0.05 * diurnal_cycle + eps(0.05)
    u_curr = 0.30 * np.cos(2 * np.pi * lat_n) * np.sin(2 * np.pi * lon_n) + 0.08 * np.cos(2 * np.pi * (hour / 24.0)) + eps(0.05)
    v_curr = -0.30 * np.sin(2 * np.pi * lat_n) * np.cos(2 * np.pi * lon_n) + 0.08 * np.sin(2 * np.pi * (hour / 24.0)) + eps(0.05)
    u_wind = 5.0 + 3.0 * np.sin(2 * np.pi * lon_n) + 1.4 * season_cycle + 0.8 * diurnal_cycle + eps(1.0)
    v_wind = 2.0 * np.cos(2 * np.pi * lat_n) - 0.6 * diurnal_cycle + eps(1.0)

    return {
        "sst": sst, "sss": sss, "ssh": ssh,
        "u_curr": u_curr, "v_curr": v_curr,
        "u_wind": u_wind, "v_wind": v_wind,
    }


def subsurface_profile(lat, lon, depth, sfields=None, rng=None, noise=True):
    """
    Generate SYNTHETIC subsurface temperature & salinity at given depth(s)
    using a thermocline-like exponential relaxation from the surface value
    toward a deep-ocean asymptote. This is an illustrative parametric shape,
    not an ocean physics model.
    """
    if rng is None:
        rng = np.random.default_rng(_DEFAULT_SEED)
    if sfields is None:
        sfields = surface_fields(lat, lon, rng=rng, noise=noise)

    lat_n, _ = normalize_latlon(lat, lon)
    depth = np.asarray(depth, dtype=float)
    shape = np.shape(depth)

    deep_T = 4.0     # deg C, asymptotic deep temperature
    deep_S = 34.75   # psu, asymptotic deep salinity
    mld = 40.0 + 40.0 * (1.0 - lat_n)   # synthetic "mixed layer" depth scale
    t_scale = mld + 120.0
    s_scale = mld + 220.0

    def eps(scale):
        return rng.normal(0, scale, size=shape) if noise else 0.0

    temperature = deep_T + (sfields["sst"] - deep_T) * np.exp(-depth / t_scale) + eps(0.15)
    salinity = deep_S + (sfields["sss"] - deep_S) * np.exp(-depth / s_scale) + eps(0.05)

    return temperature, salinity


def sample_training_set(n_samples, seed=_DEFAULT_SEED):
    """
    Draw n_samples random (lat, lon, depth) points across the domain and
    compute SYNTHETIC feature vectors + targets for supervised training.
    Returns (X, y) as float32 numpy arrays.
    """
    rng = np.random.default_rng(seed)
    lat = rng.uniform(LAT_MIN, LAT_MAX, n_samples)
    lon = rng.uniform(LON_MIN, LON_MAX, n_samples)
    depth = rng.uniform(DEPTH_MIN, DEPTH_MAX, n_samples)

    sfields = surface_fields(lat, lon, rng=rng, noise=True)
    temperature, salinity = subsurface_profile(lat, lon, depth, sfields=sfields, rng=rng, noise=True)

    lat_n, lon_n = normalize_latlon(lat, lon)
    X = np.column_stack([
        sfields["sst"], sfields["sss"], sfields["ssh"],
        sfields["u_curr"], sfields["v_curr"],
        sfields["u_wind"], sfields["v_wind"],
        depth, lat_n, lon_n,
    ]).astype(np.float32)
    y = np.column_stack([temperature, salinity]).astype(np.float32)
    return X, y


# A handful of fixed demo "virtual float" locations spread across the domain,
# loosely named after real North Indian Ocean regions for demo flavor only.
DEMO_LOCATIONS = [
    {"location_id": "ARB-01", "name": "Central Arabian Sea", "lat": 15.0, "lon": 65.0},
    {"location_id": "ARB-02", "name": "Off Mumbai Coast", "lat": 19.0, "lon": 68.0},
    {"location_id": "ARB-03", "name": "Lakshadweep Sea", "lat": 11.5, "lon": 72.5},
    {"location_id": "BOB-01", "name": "Central Bay of Bengal", "lat": 15.0, "lon": 88.0},
    {"location_id": "BOB-02", "name": "Off Chennai Coast", "lat": 13.0, "lon": 82.0},
    {"location_id": "BOB-03", "name": "Andaman Sea", "lat": 11.0, "lon": 95.0},
    {"location_id": "EQ-01", "name": "Equatorial Indian Ocean", "lat": 5.5, "lon": 80.0},
    {"location_id": "NIO-01", "name": "Northern Arabian Sea", "lat": 22.0, "lon": 63.0},
    {"location_id": "NIO-02", "name": "Northern Bay of Bengal", "lat": 21.0, "lon": 90.0},
    {"location_id": "SRI-01", "name": "South of Sri Lanka", "lat": 6.5, "lon": 81.0},
]
