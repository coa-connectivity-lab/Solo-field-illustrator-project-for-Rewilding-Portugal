"""
run_omniscape.py
──────────────────
Pure-Python circuit-theory connectivity solve, replacing Julia Omniscape.jl
per the user's explicit "just python" instruction (no Julia, and the legacy
PyPI `circuitscape` package is confirmed broken on modern Python — see
plan's Context section). The core Kirchhoff's-law linear system is solved
with scipy.sparse, an existing well-tested package doing the actual linear
algebra, not a from-scratch solver.

Algorithm, following Omniscape's own design (McRae et al.; Prima et al.
2024 Sec 2.6.1, p.2388-2389) and this project's "single best-estimate"
scoping decision (one parameter set per group, no uncertainty sweep):

  1. Resample resistance + source (suitability) rasters to 1km resolution
     for this step only. This mirrors Prima et al.'s own resolution choice
     (1km2, p.2388) despite having finer source data - a real trade-off,
     stated here rather than hidden, made for tractability across a
     9,377 km2 / 30km-buffer study area within this session's compute budget.
  2. Slide a moving window (radius = group dispersal distance, block size =
     radius/10, both in Prima's Sec 2.6.1) across the landscape. Each window
     is one small resistor network: pixels are nodes, 4-connected edges have
     conductance = 1/mean(resistance_i, resistance_j), pixels on the window's
     outer ring are grounded (V=0), and current is injected at source pixels
     proportional to their suitability.
  3. Solve G @ V = I for each window (sparse SPD solve), take
     |edge current| = conductance * (V_i - V_j), accumulate onto both
     endpoint pixels, and sum across all overlapping windows into one
     cumulative current-flow raster.
  4. Repeat with a uniform resistance surface (flow_potential, Omniscape's
     own normalisation baseline) and divide: normalized_current =
     current_flow / flow_potential.

Outputs per group, output/rasters/:
  {group}_current_flow.tif, {group}_flow_potential.tif,
  {group}_normalized_current.tif
(naming matches data-management/docs/07_qgis_analysis_protocol.md)
"""

import numpy as np
import rioxarray
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from rasterio.enums import Resampling

import config

RESISTANCE_DIR = config.DATA_PROCESSED / "resistance"
SUITABILITY_DIR = config.DATA_PROCESSED / "suitability"
OUT_DIR = config.OUTPUT_RASTERS

OMNISCAPE_RESOLUTION_M = 1000.0  # see module docstring


def resample_to_omniscape_grid(path, resampling=Resampling.average):
    da = rioxarray.open_rasterio(path, masked=True).squeeze("band", drop=True)
    return da.rio.reproject(da.rio.crs, resolution=OMNISCAPE_RESOLUTION_M, resampling=resampling)


def _node_index(valid_mask: np.ndarray) -> np.ndarray:
    """Map each valid (row, col) to a 0..n-1 node id; -1 where invalid."""
    idx = np.full(valid_mask.shape, -1, dtype=np.int64)
    idx[valid_mask] = np.arange(valid_mask.sum())
    return idx


def solve_window(resistance: np.ndarray, source: np.ndarray) -> np.ndarray:
    """
    One Omniscape window solve. resistance/source are 2D arrays (NaN = outside
    study area). Returns a same-shape array of accumulated |current| per pixel.
    Ground = the outer ring of valid pixels; source = interior pixels weighted
    by `source`.
    """
    valid = ~np.isnan(resistance)
    if valid.sum() < 4:
        return np.zeros_like(resistance)

    nrows, ncols = resistance.shape
    # Ground ring: valid pixels within 1 cell of the window edge or adjacent
    # to an invalid (outside-study-area) pixel - both count as "off the edge
    # of this window" for grounding purposes.
    ring = np.zeros_like(valid)
    ring[0, :] |= valid[0, :]
    ring[-1, :] |= valid[-1, :]
    ring[:, 0] |= valid[:, 0]
    ring[:, -1] |= valid[:, -1]
    invalid_padded = ~valid
    ring[1:-1, 1:-1] |= (
        invalid_padded[:-2, 1:-1] | invalid_padded[2:, 1:-1]
        | invalid_padded[1:-1, :-2] | invalid_padded[1:-1, 2:]
    ) & valid[1:-1, 1:-1]

    node_id = _node_index(valid)
    n = valid.sum()

    rows, cols, vals = [], [], []
    # Horizontal edges
    hz = valid[:, :-1] & valid[:, 1:]
    r_h = 0.5 * (resistance[:, :-1][hz] + resistance[:, 1:][hz])
    cond_h = 1.0 / r_h
    i_idx = node_id[:, :-1][hz]
    j_idx = node_id[:, 1:][hz]
    # Vertical edges
    vt = valid[:-1, :] & valid[1:, :]
    r_v = 0.5 * (resistance[:-1, :][vt] + resistance[1:, :][vt])
    cond_v = 1.0 / r_v
    i_idx_v = node_id[:-1, :][vt]
    j_idx_v = node_id[1:, :][vt]

    edge_i = np.concatenate([i_idx, i_idx_v])
    edge_j = np.concatenate([j_idx, j_idx_v])
    edge_cond = np.concatenate([cond_h, cond_v])

    G = sp.coo_matrix((edge_cond, (edge_i, edge_j)), shape=(n, n))
    G = G + G.T
    diag = np.asarray(G.sum(axis=1)).ravel()
    L = sp.diags(diag) - G  # graph Laplacian (conductance-weighted)
    L = L.tocsr()

    ground_nodes = node_id[ring & valid]
    is_ground = np.zeros(n, dtype=bool)
    is_ground[ground_nodes] = True
    free = ~is_ground

    source_strength = np.where(valid, np.nan_to_num(source), 0.0)
    I = source_strength[valid]
    I_free = I[free]

    if free.sum() == 0 or I_free.sum() == 0:
        return np.zeros_like(resistance)

    L_free = L[free][:, free]
    try:
        V_free = spla.spsolve(L_free.tocsc(), I_free)
    except Exception:
        V_free, _ = spla.cg(L_free.tocsc(), I_free, rtol=1e-4, maxiter=2000)

    V = np.zeros(n)
    V[free] = V_free
    # ground nodes stay at V=0

    edge_dV = np.abs(V[edge_i] - V[edge_j])
    edge_current = edge_cond * edge_dV

    node_current = np.zeros(n)
    np.add.at(node_current, edge_i, 0.5 * edge_current)
    np.add.at(node_current, edge_j, 0.5 * edge_current)

    out = np.zeros_like(resistance)
    out[valid] = node_current[node_id[valid]]
    return out


def run_moving_window(resistance: np.ndarray, source: np.ndarray, radius_px: int) -> np.ndarray:
    block = max(1, radius_px // 10)
    nrows, ncols = resistance.shape
    accum = np.zeros_like(resistance)

    centers_r = list(range(0, nrows, block))
    centers_c = list(range(0, ncols, block))
    n_windows = len(centers_r) * len(centers_c)
    print(f"    {n_windows} windows (radius={radius_px}px, block={block}px, grid {nrows}x{ncols})")

    for ri in centers_r:
        if resistance.shape[0] > 0 and np.isnan(resistance[ri, :]).all():
            continue
        for ci in centers_c:
            r0, r1 = max(0, ri - radius_px), min(nrows, ri + radius_px + 1)
            c0, c1 = max(0, ci - radius_px), min(ncols, ci + radius_px + 1)
            res_win = resistance[r0:r1, c0:c1]
            if np.isnan(res_win).all():
                continue
            src_win = source[r0:r1, c0:c1]
            if np.nansum(src_win) <= 0:
                continue
            contrib = solve_window(res_win, src_win)
            accum[r0:r1, c0:c1] += contrib
    return accum


def run_group(group_key: str) -> None:
    group = config.GROUPS[group_key]
    print(f"{group.label} (dispersal {group.dispersal_km}km):")

    resistance = resample_to_omniscape_grid(RESISTANCE_DIR / f"{group_key}_resistance.tif")
    source = resample_to_omniscape_grid(SUITABILITY_DIR / f"{group_key}_suitability.tif")
    source = source.interp_like(resistance, method="nearest")

    radius_px = max(2, round(group.dispersal_km * 1000 / OMNISCAPE_RESOLUTION_M))

    res_vals = resistance.values
    src_vals = source.values

    current_flow = run_moving_window(res_vals, src_vals, radius_px)

    uniform_resistance = np.where(np.isnan(res_vals), np.nan, 1.0)
    flow_potential = run_moving_window(uniform_resistance, src_vals, radius_px)

    with np.errstate(divide="ignore", invalid="ignore"):
        normalized = np.where(flow_potential > 0, current_flow / flow_potential, np.nan)
    normalized = np.where(np.isnan(res_vals), np.nan, normalized)

    for name, arr in [("current_flow", current_flow), ("flow_potential", flow_potential),
                       ("normalized_current", normalized)]:
        out = resistance.copy(data=np.where(np.isnan(res_vals), np.nan, arr))
        out_path = OUT_DIR / f"{group_key}_{name}.tif"
        out.rio.to_raster(out_path, compress="LZW")
    valid_norm = normalized[~np.isnan(normalized)]
    if len(valid_norm):
        print(f"  normalized_current range [{valid_norm.min():.3f}, {valid_norm.max():.3f}], "
              f"mean {valid_norm.mean():.3f}")
    print(f"  wrote {group_key}_{{current_flow,flow_potential,normalized_current}}.tif")


def main() -> None:
    for group_key in config.GROUPS:
        run_group(group_key)


if __name__ == "__main__":
    main()
