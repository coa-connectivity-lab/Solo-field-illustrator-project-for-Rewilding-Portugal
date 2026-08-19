"""
build_resistance_surfaces.py
──────────────────────────────
Convert each group's suitability raster to a resistance raster via
Prima et al. 2024's Eq.1 (p.2389):

    R = 100 - 99 * (1 - exp(-c*H)) / (1 - exp(-c))

H = suitability in [0,1], R in [1,100] (1 = no resistance, 100 = impassable).
Single mid-range c per group (config.Group.resistance_shape_c), not Prima's
c-sweep - this project's "single best-estimate" scoping decision.
"""

import numpy as np
import rioxarray

import config

SUITABILITY_DIR = config.DATA_PROCESSED / "suitability"
OUT_DIR = config.DATA_PROCESSED / "resistance"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def suitability_to_resistance(h: np.ndarray, c: float) -> np.ndarray:
    return 100 - 99 * (1 - np.exp(-c * h)) / (1 - np.exp(-c))


def main() -> None:
    for group_key, group in config.GROUPS.items():
        da = rioxarray.open_rasterio(
            SUITABILITY_DIR / f"{group_key}_suitability.tif", masked=True
        ).squeeze("band", drop=True)
        resistance = suitability_to_resistance(da.values, group.resistance_shape_c)
        out = da.copy(data=resistance)
        out_path = OUT_DIR / f"{group_key}_resistance.tif"
        out.rio.to_raster(out_path, compress="LZW")
        valid = resistance[~np.isnan(resistance)]
        print(f"{group.label}: c={group.resistance_shape_c}, "
              f"resistance range [{valid.min():.1f}, {valid.max():.1f}], mean {valid.mean():.1f}")
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
