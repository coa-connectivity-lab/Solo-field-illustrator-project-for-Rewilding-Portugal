"""
combine_connectivity.py
──────────────────────────
Combine the three groups' normalized_current rasters into multispecies
outputs, following Prima et al. 2024's species-count-weighted averaging
(p.2389: "a probability map for all mammals or all birds by calculating
an average of all ... group maps weighted by the species number in each
group"). Land/Water/Air stand in for Prima's mammal/bird groupings here.

Outputs (naming matches data-management/docs/07_qgis_analysis_protocol.md):
  multispecies_mean_connectivity.tif  - species-count-weighted mean
  multispecies_max_connectivity.tif   - pixel-wise max across groups
"""

import warnings

import numpy as np
import rioxarray

import config

RASTER_DIR = config.OUTPUT_RASTERS


def main() -> None:
    stacks = []
    weights = []
    template = None
    for group_key, group in config.GROUPS.items():
        da = rioxarray.open_rasterio(
            RASTER_DIR / f"{group_key}_normalized_current.tif", masked=True
        ).squeeze("band", drop=True)
        if template is None:
            template = da
        stacks.append(da.values)
        weights.append(len(group.species))

    arr = np.stack(stacks)  # (n_groups, rows, cols)
    w = np.array(weights).reshape(-1, 1, 1)

    valid_count = (~np.isnan(arr)).sum(axis=0)
    with np.errstate(invalid="ignore"):
        weighted_sum = np.nansum(np.where(np.isnan(arr), 0, arr) * w, axis=0)
        weight_sum = np.nansum(np.where(np.isnan(arr), 0, 1) * w, axis=0)
        mean_map = np.where(valid_count > 0, weighted_sum / np.where(weight_sum == 0, np.nan, weight_sum), np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            max_map = np.where(valid_count > 0, np.nanmax(arr, axis=0), np.nan)

    for name, data in [("multispecies_mean_connectivity", mean_map),
                        ("multispecies_max_connectivity", max_map)]:
        out = template.copy(data=data)
        out_path = RASTER_DIR / f"{name}.tif"
        out.rio.to_raster(out_path, compress="LZW")
        valid = data[~np.isnan(data)]
        print(f"{name}: range [{valid.min():.3f}, {valid.max():.3f}], mean {valid.mean():.3f}")
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
