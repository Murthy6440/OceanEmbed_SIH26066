// Thermal color scale for subsurface temperature (deg C), tuned to the
// range this demo model actually produces in the North Indian Ocean box:
// ~4 degC asymptotic deep water up to ~30 degC warm surface water.
const STOPS = [
  { t: 2, c: [8, 29, 88] },
  { t: 6, c: [37, 82, 158] },
  { t: 10, c: [65, 145, 197] },
  { t: 15, c: [120, 198, 189] },
  { t: 20, c: [204, 230, 150] },
  { t: 24, c: [254, 209, 118] },
  { t: 27, c: [253, 141, 60] },
  { t: 30, c: [204, 33, 33] },
];

export const SCALE_MIN = STOPS[0].t;
export const SCALE_MAX = STOPS[STOPS.length - 1].t;

export function tempToColor(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "#9aa5b1";
  }
  const v = Math.max(SCALE_MIN, Math.min(SCALE_MAX, value));
  for (let i = 0; i < STOPS.length - 1; i++) {
    const a = STOPS[i];
    const b = STOPS[i + 1];
    if (v >= a.t && v <= b.t) {
      const f = (v - a.t) / (b.t - a.t);
      const r = Math.round(a.c[0] + f * (b.c[0] - a.c[0]));
      const g = Math.round(a.c[1] + f * (b.c[1] - a.c[1]));
      const bch = Math.round(a.c[2] + f * (b.c[2] - a.c[2]));
      return `rgb(${r}, ${g}, ${bch})`;
    }
  }
  return "#9aa5b1";
}

export const LEGEND_STOPS = STOPS;
