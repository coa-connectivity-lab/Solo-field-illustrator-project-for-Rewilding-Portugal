"""
build_suitability_models.py
─────────────────────────────
One presence-background suitability model per group (land / water / air),
following Prima et al. 2024's approach of unioning a group's species'
occurrences before modelling (p.2389), simplified to a single
RandomForestClassifier per group rather than their 4-model ensemble
(this project's "single best-estimate" scoping decision).

Output: one continuous 0-1 suitability raster per group,
data/processed/suitability/{group}_suitability.tif
"""

import geopandas as gpd
import numpy as np
import rioxarray
import xarray as xr
from sklearn.ensemble import RandomForestClassifier

import config

COVARIATE_DIR = config.DATA_PROCESSED / "covariates"
OUT_DIR = config.DATA_PROCESSED / "suitability"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Per-group covariate sets, matching the ecological rationale in the plan:
# Air's connectivity logic is topographic (thermals/cliffs), not road-driven;
# Water leans on the landcover/imperviousness signal for riparian condition;
# Land uses the full generalist set.
GROUP_COVARIATES = {
    "land": ["elevation", "slope_degrees", "ruggedness_tri", "landcover_clcplus",
             "distance_to_road_m", "imperviousness"],
    "water": ["elevation", "slope_degrees", "landcover_clcplus", "imperviousness",
              "distance_to_road_m"],
    "air": ["elevation", "slope_degrees", "ruggedness_tri", "hillshade"],
}

N_BACKGROUND = 2000
RANDOM_STATE = 42


def load_covariate_stack(names: list[str]) -> xr.DataArray:
    arrays = []
    for name in names:
        da = rioxarray.open_rasterio(COVARIATE_DIR / f"{name}.tif", masked=True).squeeze("band", drop=True)
        arrays.append(da.rename(name))
    stack = xr.concat(arrays, dim="covariate")
    stack = stack.assign_coords(covariate=names)
    return stack


def sample_covariates_at_points(stack: xr.DataArray, gdf: gpd.GeoDataFrame) -> np.ndarray:
    xs = xr.DataArray(gdf.geometry.x.values, dims="points")
    ys = xr.DataArray(gdf.geometry.y.values, dims="points")
    sampled = stack.sel(x=xs, y=ys, method="nearest")
    return sampled.values.T  # (n_points, n_covariates)


def sample_background(stack: xr.DataArray, study_area: gpd.GeoDataFrame, n: int) -> np.ndarray:
    minx, miny, maxx, maxy = study_area.total_bounds
    rng = np.random.default_rng(RANDOM_STATE)
    pts = []
    valid_mask = ~np.isnan(stack.isel(covariate=0).values)
    while len(pts) < n:
        x = rng.uniform(minx, maxx, size=n)
        y = rng.uniform(miny, maxy, size=n)
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x, y), crs=config.CRS_METRIC)
        inside = gdf[gdf.within(study_area.union_all())]
        pts.extend(list(zip(inside.geometry.x, inside.geometry.y)))
    pts = pts[:n]
    gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(*zip(*pts)), crs=config.CRS_METRIC)
    return sample_covariates_at_points(stack, gdf)


def build_group_suitability(group_key: str, study_area: gpd.GeoDataFrame) -> None:
    names = GROUP_COVARIATES[group_key]
    stack = load_covariate_stack(names)

    occ = gpd.read_file(
        config.DATA_PROCESSED / "gbif_occurrences.gpkg", layer=f"{group_key}_occurrences"
    )
    X_presence = sample_covariates_at_points(stack, occ)
    X_background = sample_background(stack, study_area, N_BACKGROUND)

    X = np.vstack([X_presence, X_background])
    y = np.concatenate([np.ones(len(X_presence)), np.zeros(len(X_background))])
    valid = ~np.isnan(X).any(axis=1)
    X, y = X[valid], y[valid]

    clf = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced",
                                  random_state=RANDOM_STATE, n_jobs=-1)
    clf.fit(X, y)
    train_acc = clf.score(X, y)
    print(f"  {group_key}: n_presence={len(X_presence)}, n_background={len(X_background)}, "
          f"train accuracy={train_acc:.2f}")

    # Predict across the full grid
    flat = stack.values.reshape(len(names), -1).T  # (n_pixels, n_covariates)
    valid_px = ~np.isnan(flat).any(axis=1)
    proba = np.full(flat.shape[0], np.nan)
    proba[valid_px] = clf.predict_proba(flat[valid_px])[:, 1]
    suitability = proba.reshape(stack.shape[1], stack.shape[2])

    template = stack.isel(covariate=0).drop_vars("covariate")
    out = template.copy(data=suitability)
    out = out.rio.write_crs(config.CRS_METRIC)
    out_path = OUT_DIR / f"{group_key}_suitability.tif"
    out.rio.to_raster(out_path, compress="LZW")
    print(f"  wrote {out_path}")


def main() -> None:
    study_area = gpd.read_file(config.DATA_PROCESSED / "study_area.gpkg", layer="study_area")
    for group_key in config.GROUPS:
        build_group_suitability(group_key, study_area)


if __name__ == "__main__":
    main()
